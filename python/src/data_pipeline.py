"""Data pipeline for combining CSV and API data."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import pandas as pd
from datetime import datetime, timedelta
import json
import shutil
from tqdm import tqdm
import aiohttp
import aiofiles

from src.config import DataConfig, MODataSource
from src.database import AsyncDatabase
from src.data_csv import DataProcessor
from src.api_mapper import MOApiMapper
from src.monitoring import measure_performance
from src.exceptions import DataProcessingError
from src.validation import validate_data

logger = logging.getLogger(__name__)

class PipelineProgress:
    """Track pipeline progress and enable recovery."""
    
    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.state: Dict[str, Any] = {
            "csv_tables_processed": set(),
            "api_enrichment": {
                "taxonomic": set(),
                "observations": set(),
                "external_links": set(),
                "sequences": set()
            },
            "last_update": None,
            "errors": [],
            "stats": {
                "total_records": 0,
                "processed_records": 0,
                "failed_records": 0,
                "start_time": None,
                "end_time": None
            }
        }
        self.load_progress()
    
    def load_progress(self):
        """Load progress from file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file) as f:
                    data = json.load(f)
                    # Convert JSON lists back to sets
                    self.state["csv_tables_processed"] = set(data["csv_tables_processed"])
                    for key in self.state["api_enrichment"]:
                        self.state["api_enrichment"][key] = set(data["api_enrichment"][key])
                    self.state["last_update"] = data["last_update"]
                    self.state["errors"] = data["errors"]
            except Exception as e:
                logger.error(f"Failed to load progress: {e}")
    
    def save_progress(self):
        """Save progress to file."""
        try:
            # Convert sets to lists for JSON serialization
            data = {
                "csv_tables_processed": list(self.state["csv_tables_processed"]),
                "api_enrichment": {
                    key: list(value)
                    for key, value in self.state["api_enrichment"].items()
                },
                "last_update": datetime.utcnow().isoformat(),
                "errors": self.state["errors"]
            }
            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def mark_csv_table_complete(self, table_name: str):
        """Mark a CSV table as processed."""
        self.state["csv_tables_processed"].add(table_name)
        self.save_progress()
    
    def mark_api_enrichment_complete(self, enrichment_type: str, item_id: int):
        """Mark an API enrichment as complete."""
        if enrichment_type in self.state["api_enrichment"]:
            self.state["api_enrichment"][enrichment_type].add(item_id)
            self.save_progress()
    
    def log_error(self, error: str, context: Dict[str, Any]):
        """Log an error with context."""
        self.state["errors"].append({
            "error": str(error),
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.save_progress()
    
    def is_csv_table_processed(self, table_name: str) -> bool:
        """Check if a CSV table has been processed."""
        return table_name in self.state["csv_tables_processed"]
    
    def is_api_enrichment_complete(self, enrichment_type: str, item_id: int) -> bool:
        """Check if an API enrichment has been completed."""
        return (
            enrichment_type in self.state["api_enrichment"] and
            item_id in self.state["api_enrichment"][enrichment_type]
        )
    
    def update_stats(self, total: Optional[int] = None, processed: int = 0, failed: int = 0):
        """Update processing statistics."""
        if total is not None:
            self.state["stats"]["total_records"] = total
        self.state["stats"]["processed_records"] += processed
        self.state["stats"]["failed_records"] += failed
        self.save_progress()
    
    def get_progress_percentage(self) -> float:
        """Get overall progress percentage."""
        total = self.state["stats"]["total_records"]
        if total == 0:
            return 0.0
        return (self.state["stats"]["processed_records"] / total) * 100
    
    def get_eta(self) -> Optional[timedelta]:
        """Estimate time remaining based on progress."""
        if not self.state["stats"]["start_time"]:
            return None
            
        start = datetime.fromisoformat(self.state["stats"]["start_time"])
        now = datetime.utcnow()
        elapsed = now - start
        
        processed = self.state["stats"]["processed_records"]
        total = self.state["stats"]["total_records"]
        
        if processed == 0 or total == 0:
            return None
            
        rate = processed / elapsed.total_seconds()
        remaining_records = total - processed
        
        if rate == 0:
            return None
            
        seconds_remaining = remaining_records / rate
        return timedelta(seconds=int(seconds_remaining))

class DataPipeline:
    """Combined data pipeline for CSV and API data."""
    
    def __init__(self, config: DataConfig):
        self.config = config
        self.db = AsyncDatabase(config)
        self.csv_processor = DataProcessor(config)
        self.api_cache_dir = Path("api_cache")
        self.temp_dir = Path("temp")
        self.api_cache_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize progress tracking
        self.progress = PipelineProgress(Path("pipeline_progress.json"))
        
        # Track processed records
        self.processed_ids: Dict[str, Set[int]] = {
            "observations": set(),
            "names": set(),
            "locations": set(),
            "images": set()
        }
    
    async def validate_record(self, record: Dict[str, Any], schema_name: str) -> bool:
        """Validate a record against its schema."""
        try:
            # Basic schema validation
            if not validate_data(record, self.config.SCHEMAS[schema_name]):
                return False
            
            # Additional validation based on record type
            if schema_name == "observations":
                if not await self._validate_observation(record):
                    return False
            elif schema_name == "names":
                if not await self._validate_name(record):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error for {schema_name} record {record.get('_id')}: {e}")
            return False
    
    async def _validate_observation(self, record: Dict[str, Any]) -> bool:
        """Validate observation-specific rules."""
        try:
            # Validate location if present
            if "location" in record:
                loc = record["location"]
                if "lat" in loc and "lng" in loc:
                    if not (-90 <= loc["lat"] <= 90 and -180 <= loc["lng"] <= 180):
                        return False
            
            # Validate date format
            if "when" in record:
                datetime.strptime(record["when"], "%Y-%m-%d")
            
            # Validate references
            if "name_id" in record:
                names_coll = self.db.get_collection("names")
                if not await names_coll.find_one({"_id": record["name_id"]}):
                    return False
            
            return True
            
        except Exception:
            return False
    
    async def _validate_name(self, record: Dict[str, Any]) -> bool:
        """Validate name-specific rules."""
        try:
            # Validate scientific name format
            if "text_name" in record:
                name = record["text_name"]
                if not name[0].isupper() or " " not in name:
                    return False
            
            # Validate rank
            if "rank" in record and record["rank"] not in range(1, 101):
                return False
            
            # Validate references
            if "synonym_id" in record and record["synonym_id"]:
                names_coll = self.db.get_collection("names")
                if not await names_coll.find_one({"_id": record["synonym_id"]}):
                    return False
            
            return True
            
        except Exception:
            return False
    
    @measure_performance
    async def initialize(self):
        """Initialize database connection and create indexes."""
        await self.db.connect()
        
        # Create indexes for each collection
        for collection, indexes in self.config.indexes.items():
            collection_obj = self.db.get_collection(collection)
            await self.db.ensure_indexes(collection_obj, indexes)
    
    async def download_csv_files(self):
        """Download CSV files from Mushroom Observer."""
        logger.info("Downloading CSV files...")
        
        # Create data directory if it doesn't exist
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data source
        mo_source = MODataSource()
        
        # Core data files
        core_files = {
            "names": mo_source.NAMES,
            "observations": mo_source.OBSERVATIONS,
            "locations": mo_source.LOCATIONS,
            "images": mo_source.IMAGES
        }
        
        # Relationship files
        relationship_files = {
            "images_observations": mo_source.IMAGES_OBSERVATIONS,
            "name_classifications": mo_source.NAME_CLASSIFICATIONS,
            "name_descriptions": mo_source.NAME_DESCRIPTIONS,
            "location_descriptions": mo_source.LOCATION_DESCRIPTIONS
        }
        
        async with aiohttp.ClientSession() as session:
            # Download core files first
            for name, url in core_files.items():
                target_path = self.config.data_dir / f"{name}.csv"
                if not target_path.exists():
                    logger.info(f"Downloading {name}.csv...")
                    try:
                        async with session.get(url) as response:
                            response.raise_for_status()
                            async with aiofiles.open(target_path, 'wb') as f:
                                await f.write(await response.read())
                        logger.info(f"Downloaded {name}.csv")
                    except Exception as e:
                        logger.error(f"Failed to download {name}.csv: {e}")
                        raise DataProcessingError(f"Failed to download {name}.csv: {e}")
            
            # Download relationship files
            for name, url in relationship_files.items():
                target_path = self.config.data_dir / f"{name}.csv"
                if not target_path.exists():
                    logger.info(f"Downloading {name}.csv...")
                    try:
                        async with session.get(url) as response:
                            response.raise_for_status()
                            async with aiofiles.open(target_path, 'wb') as f:
                                await f.write(await response.read())
                        logger.info(f"Downloaded {name}.csv")
                    except Exception as e:
                        logger.error(f"Failed to download {name}.csv: {e}")
                        raise DataProcessingError(f"Failed to download {name}.csv: {e}")
    
    @measure_performance
    async def process_csv_data(self):
        """Process CSV data files."""
        logger.info("Starting CSV data processing...")
        
        # Process core data first
        core_tables = ["names", "observations", "locations", "images"]
        for table in core_tables:
            if not self.progress.is_csv_table_processed(table):
                logger.info(f"Processing {table}.csv")
                await self._process_csv_table(table)
                self.progress.mark_csv_table_complete(table)
        
        # Process relationship tables
        relationship_tables = [
            "images_observations",
            "name_classifications",
            "name_descriptions",
            "location_descriptions"
        ]
        for table in relationship_tables:
            if not self.progress.is_csv_table_processed(table):
                logger.info(f"Processing {table}.csv")
                await self._process_csv_table(table)
                self.progress.mark_csv_table_complete(table)
    
    async def _process_csv_table(self, table_name: str):
        """Process a single CSV table."""
        try:
            file_path = self.config.data_dir / f"{table_name}.csv"
            if not file_path.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")
            
            async for batch in self.csv_processor.process_file(file_path, table_name):
                # Validate and filter batch
                valid_records = []
                for record in batch:
                    if await self.validate_record(record, table_name):
                        valid_records.append(record)
                    else:
                        self.progress.update_stats(failed=1)
                
                if valid_records:
                    # Insert valid records into database
                    collection = self.db.get_collection(table_name)
                    await self.db.batch_upsert(collection, valid_records)
                    self.progress.update_stats(processed=len(valid_records))
                
                # Track processed IDs for core tables
                if table_name in self.processed_ids:
                    self.processed_ids[table_name].update(
                        record["_id"] for record in valid_records
                    )
        
        except Exception as e:
            raise DataProcessingError(f"Failed to process {table_name}: {str(e)}")
    
    @measure_performance
    async def cleanup(self):
        """Cleanup temporary files and close connections."""
        try:
            # Close database connection
            await self.db.close()
            
            # Remove temporary files
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            
            # Save final progress
            current_time = datetime.utcnow()
            self.progress.state["stats"]["end_time"] = current_time.isoformat()
            self.progress.save_progress()
            
            logger.info("Cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise

async def main():
    """Main execution function."""
    try:
        # Initialize pipeline
        config = DataConfig()
        pipeline = DataPipeline(config)
        
        # Start timing
        pipeline.progress.state["stats"]["start_time"] = datetime.utcnow().isoformat()
        
        # Initialize database and indexes
        await pipeline.initialize()
        
        # Download CSV files
        await pipeline.download_csv_files()
        
        # Process CSV data
        await pipeline.process_csv_data()
        
        # Cleanup
        await pipeline.cleanup()
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 