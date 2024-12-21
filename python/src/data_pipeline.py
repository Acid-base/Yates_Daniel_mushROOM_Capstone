import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Set, List
from datetime import datetime, timedelta
import json
import shutil
import aiohttp
import aiofiles
from collections import defaultdict
from pydantic import BaseModel, Field

from src.config import DataConfig, MODataSource
from src.monitoring import measure_performance
from src.exceptions import DataProcessingError
from src.validation import validate_data

logger = logging.getLogger(__name__)


class PipelineStats(BaseModel):
    """Pipeline processing statistics."""

    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class PipelineState(BaseModel):
    """Pipeline state tracking."""

    csv_tables_processed: Set[str] = Field(default_factory=set)
    api_enrichment: Dict[str, Set[int]] = Field(
        default_factory=lambda: defaultdict(set)
    )
    last_update: Optional[datetime] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    stats: PipelineStats = Field(default_factory=PipelineStats)

    class Config:
        arbitrary_types_allowed = True


class PipelineProgress:
    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.state = PipelineState()
        self.load_progress()

    def load_progress(self):
        if self.progress_file.exists():
            try:
                with open(self.progress_file) as f:
                    data = json.load(f)
                    self.state.csv_tables_processed = set(data["csv_tables_processed"])
                    for key, value in data.get("api_enrichment", {}).items():
                        self.state.api_enrichment[key] = set(value)
                    self.state.last_update = data.get("last_update")
                    self.state.errors = data.get("errors", [])
            except Exception as e:
                logger.error(f"Failed to load progress: {e}")

    def save_progress(self):
        try:
            data = {
                "csv_tables_processed": list(self.state.csv_tables_processed),
                "api_enrichment": {
                    key: list(value) for key, value in self.state.api_enrichment.items()
                },
                "last_update": datetime.utcnow().isoformat(),
                "errors": self.state.errors,
            }
            with open(self.progress_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")

    def mark_csv_table_complete(self, table_name: str):
        self.state.csv_tables_processed.add(table_name)
        self.save_progress()

    def mark_api_enrichment_complete(self, enrichment_type: str, item_id: int):
        self.state.api_enrichment[enrichment_type].add(item_id)
        self.save_progress()

    def log_error(self, error: str, context: Dict[str, Any]):
        self.state.errors.append(
            {
                "error": str(error),
                "context": context,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        self.save_progress()

    def is_csv_table_processed(self, table_name: str) -> bool:
        return table_name in self.state.csv_tables_processed

    def is_api_enrichment_complete(self, enrichment_type: str, item_id: int) -> bool:
        return item_id in self.state.api_enrichment[enrichment_type]

    def update_stats(
        self, total: Optional[int] = None, processed: int = 0, failed: int = 0
    ):
        if total is not None:
            self.state.stats.total_records = total
        self.state.stats.processed_records += processed
        self.state.stats.failed_records += failed
        self.save_progress()

    def get_progress_percentage(self) -> float:
        total = self.state.stats.total_records
        return (self.state.stats.processed_records / total) * 100 if total else 0.0

    def get_eta(self) -> Optional[timedelta]:
        start_time = self.state.stats.start_time
        if not start_time:
            return None

        start = datetime.fromisoformat(start_time)
        now = datetime.utcnow()
        elapsed = now - start
        processed = self.state.stats.processed_records
        total = self.state.stats.total_records

        if not processed or not total:
            return None

        rate = processed / elapsed.total_seconds()
        if not rate:
            return None

        remaining_seconds = (total - processed) / rate
        return timedelta(seconds=int(remaining_seconds))


class DataPipeline:
    def __init__(self, config: DataConfig):
        self.config = config
        self.progress = PipelineProgress(Path("pipeline_progress.json"))

    @validator("config")
    def validate_config(cls, v):
        if not v.data_dir.exists():
            raise ValueError(f"Data directory {v.data_dir} does not exist")
        return v

    async def validate_record(self, record: Dict[str, Any], schema_name: str) -> bool:
        try:
            if not validate_data(record, self.config.SCHEMAS[schema_name]):
                return False

            if schema_name == "observations":
                return await self._validate_observation(record)
            if schema_name == "names":
                return await self._validate_name(record)
            return True

        except Exception as e:
            logger.error(
                f"Validation error for {schema_name} record {record.get('_id')}: {e}"
            )
            return False

    async def _validate_observation(self, record: Dict[str, Any]) -> bool:
        try:
            if "location" in record:
                loc = record["location"]
                if "lat" in loc and "lng" in loc:
                    if not (-90 <= loc["lat"] <= 90 and -180 <= loc["lng"] <= 180):
                        return False

            if "when" in record:
                datetime.strptime(record["when"], "%Y-%m-%d")

            if "name_id" in record:
                names_coll = self.db.get_collection("names")
                if not await names_coll.find_one({"_id": record["name_id"]}):
                    return False

            return True

        except Exception:
            return False

    async def _validate_name(self, record: Dict[str, Any]) -> bool:
        try:
            if "text_name" in record:
                name = record["text_name"]
                if not name[0].isupper() or " " not in name:
                    return False

            if "rank" in record and record["rank"] not in range(1, 101):
                return False

            if "synonym_id" in record and record["synonym_id"]:
                names_coll = self.db.get_collection("names")
                if not await names_coll.find_one({"_id": record["synonym_id"]}):
                    return False

            return True

        except Exception:
            return False

    @measure_performance
    async def initialize(self):
        await self.db.connect()
        for collection, indexes in self.config.indexes.items():
            collection_obj = self.db.get_collection(collection)
            await self.db.ensure_indexes(collection_obj, indexes)

    async def download_csv_files(self):
        logger.info("Downloading CSV files...")
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        mo_source = MODataSource()
        files = {
            "names": mo_source.NAMES,
            "observations": mo_source.OBSERVATIONS,
            "locations": mo_source.LOCATIONS,
            "images": mo_source.IMAGES,
            "images_observations": mo_source.IMAGES_OBSERVATIONS,
            "name_classifications": mo_source.NAME_CLASSIFICATIONS,
            "name_descriptions": mo_source.NAME_DESCRIPTIONS,
            "location_descriptions": mo_source.LOCATION_DESCRIPTIONS,
        }

        async with aiohttp.ClientSession() as session:
            for name, url in files.items():
                target_path = self.config.data_dir / f"{name}.csv"
                if not target_path.exists():
                    logger.info(f"Downloading {name}.csv...")
                    try:
                        async with session.get(url) as response:
                            response.raise_for_status()
                            async with aiofiles.open(target_path, "wb") as f:
                                await f.write(await response.read())
                        logger.info(f"Downloaded {name}.csv")

                    except Exception as e:
                        logger.error(f"Failed to download {name}.csv: {e}")
                        raise DataProcessingError(f"Failed to download {name}.csv: {e}")

    @measure_performance
    async def process_csv_data(self):
        logger.info("Starting CSV data processing...")
        core_tables = ["names", "observations", "locations", "images"]
        relationship_tables = [
            "images_observations",
            "name_classifications",
            "name_descriptions",
            "location_descriptions",
        ]
        all_tables = core_tables + relationship_tables
        for table in all_tables:
            if not self.progress.is_csv_table_processed(table):
                logger.info(f"Processing {table}.csv")
                await self._process_csv_table(table)
                self.progress.mark_csv_table_complete(table)

    async def _process_csv_table(self, table_name: str):
        try:
            file_path = self.config.data_dir / f"{table_name}.csv"
            if not file_path.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")

            async for batch in self.csv_processor.process_file(file_path, table_name):
                valid_records = [
                    record
                    for record in batch
                    if await self.validate_record(record, table_name)
                ]
                self.progress.update_stats(failed=len(batch) - len(valid_records))

                if valid_records:
                    collection = self.db.get_collection(table_name)
                    await self.db.batch_upsert(collection, valid_records)
                    self.progress.update_stats(processed=len(valid_records))

                    if table_name in self.processed_ids:
                        self.processed_ids[table_name].update(
                            record["_id"] for record in valid_records
                        )

        except Exception as e:
            raise DataProcessingError(f"Failed to process {table_name}: {str(e)}")

    @measure_performance
    async def cleanup(self):
        try:
            await self.db.close()
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            self.progress.state.stats.end_time = datetime.utcnow().isoformat()
            self.progress.save_progress()
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise


async def main():
    try:
        config = DataConfig()
        pipeline = DataPipeline(config)
        pipeline.progress.state.stats.start_time = datetime.utcnow().isoformat()
        await pipeline.initialize()
        await pipeline.download_csv_files()
        await pipeline.process_csv_data()
        await pipeline.cleanup()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
