"""Main data processing script with async support."""

from __future__ import annotations

import asyncio
import logging
import logging.config
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncGenerator

import pandas as pd
from dotenv import load_dotenv

from src.config import DataConfig, load_yaml_config
from src.database import get_database
from src.downloader import download_mo_data
from src.exceptions import (
    DataProcessingError,
    ValidationError,
    DatabaseError,
    FileProcessingError
)
from src.monitoring import measure_performance
from src.validation import (
    SchemaValidator,
    DateValidator,
    LocationValidator,
    NameValidator,
    validate_with_schema
)
from src.schemas import SCHEMAS

# Initialize logging
logger = logging.getLogger(__name__)

class DataProcessor:
    """Main data processing class with async support."""
    
    def __init__(self, config: DataConfig):
        self.config = config
        self.validators = {
            "date": DateValidator(config.DATE_FORMAT),
            "location": LocationValidator(),
            "name": NameValidator()
        }
    
    @measure_performance
    async def process_file(
        self,
        file_path: Path,
        schema_name: str
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """Process a single data file."""
        try:
            schema = SCHEMAS.get(schema_name)
            if not schema:
                raise ValidationError(f"Unknown schema: {schema_name}")
            
            # Read CSV file with proper encoding and error handling
            df = pd.read_csv(
                file_path,
                delimiter=self.config.default_delimiter,
                na_values=list(self.config.null_values),
                encoding='utf-8',
                on_bad_lines='warn'
            )
            
            # Process data in chunks to manage memory
            chunk_size = self.config.batch_size
            
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i:i + chunk_size]
                processed_data = []
                
                for _, row in chunk.iterrows():
                    data = row.to_dict()
                    
                    # Validate against schema
                    validation_result = validate_with_schema(
                        data,
                        schema,
                        [self.validators[v] for v in self._get_validators(schema_name)]
                    )
                    
                    if not validation_result.is_valid:
                        logger.warning(
                            f"Validation issues for {schema_name} record: "
                            f"Errors: {validation_result.errors}, "
                            f"Warnings: {validation_result.warnings}"
                        )
                        continue
                    
                    processed_data.append(self._process_record(data, schema_name))
                
                if processed_data:
                    logger.info(
                        f"Processed {len(processed_data)} records from {schema_name}"
                    )
                    yield processed_data
                
                # Give other tasks a chance to run
                await asyncio.sleep(0)
            
        except Exception as e:
            raise FileProcessingError(f"Failed to process {file_path}: {e}")
    
    def _get_validators(self, schema_name: str) -> List[str]:
        """Get relevant validators for schema."""
        validators = []
        if "when" in SCHEMAS[schema_name]:
            validators.append("date")
        if any(f in SCHEMAS[schema_name] for f in ["lat", "lng", "alt"]):
            validators.append("location")
        if "text_name" in SCHEMAS[schema_name]:
            validators.append("name")
        return validators
    
    def _process_record(
        self,
        data: Dict[str, Any],
        schema_name: str
    ) -> Dict[str, Any]:
        """Process a single record based on schema."""
        processors = {
            "observations": self._process_observation,
            "names": self._process_name,
            "name_descriptions": self._process_description,
            "name_classifications": self._process_classification,
            "images": self._process_image,
            "images_observations": self._process_image_observation,
            "locations": self._process_location,
            "location_descriptions": self._process_location_description
        }
        
        processor = processors.get(schema_name, lambda x: x)
        return processor(data)
    
    def _process_observation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process observation record."""
        return {
            "_id": int(data["id"]),
            "name_id": int(data["name_id"]),
            "when": data["when"],
            "location": {
                "lat": float(data["lat"]) if pd.notna(data["lat"]) else None,
                "lng": float(data["lng"]) if pd.notna(data["lng"]) else None,
                "alt": float(data["alt"]) if pd.notna(data["alt"]) else None
            },
            "vote_cache": float(data["vote_cache"]) if pd.notna(data["vote_cache"]) else None,
            "is_collection_location": bool(data["is_collection_location"]),
            "thumb_image_id": int(data["thumb_image_id"]) if pd.notna(data["thumb_image_id"]) else None
        }
    
    def _process_name(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process name record."""
        return {
            "_id": int(data["id"]),
            "text_name": str(data["text_name"]).strip(),
            "author": str(data["author"]).strip() if pd.notna(data["author"]) else None,
            "deprecated": bool(data["deprecated"]) if pd.notna(data["deprecated"]) else False,
            "correct_spelling_id": int(data["correct_spelling_id"]) if pd.notna(data["correct_spelling_id"]) else None,
            "synonym_id": int(data["synonym_id"]) if pd.notna(data["synonym_id"]) else None,
            "rank": int(data["rank"]) if pd.notna(data["rank"]) else None
        }
    
    def _process_description(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process name description record."""
        return {
            "_id": int(data["id"]),
            "name_id": int(data["name_id"]),
            "source_type": int(data["source_type"]) if pd.notna(data["source_type"]) else None,
            "source_name": str(data["source_name"]).strip() if pd.notna(data["source_name"]) else None,
            "description": {
                "general": str(data["gen_desc"]).strip() if pd.notna(data["gen_desc"]) else None,
                "diagnostic": str(data["diag_desc"]).strip() if pd.notna(data["diag_desc"]) else None,
                "distribution": str(data["distribution"]).strip() if pd.notna(data["distribution"]) else None,
                "habitat": str(data["habitat"]).strip() if pd.notna(data["habitat"]) else None,
                "look_alikes": str(data["look_alikes"]).strip() if pd.notna(data["look_alikes"]) else None,
                "uses": str(data["uses"]).strip() if pd.notna(data["uses"]) else None,
                "notes": str(data["notes"]).strip() if pd.notna(data["notes"]) else None,
                "refs": str(data["refs"]).strip() if pd.notna(data["refs"]) else None
            }
        }
    
    def _process_classification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process name classification record."""
        return {
            "_id": int(data["id"]),
            "name_id": int(data["name_id"]),
            "taxonomy": {
                "domain": str(data["domain"]).strip() if pd.notna(data["domain"]) else None,
                "kingdom": str(data["kingdom"]).strip() if pd.notna(data["kingdom"]) else None,
                "phylum": str(data["phylum"]).strip() if pd.notna(data["phylum"]) else None,
                "class": str(data["class"]).strip() if pd.notna(data["class"]) else None,
                "order": str(data["order"]).strip() if pd.notna(data["order"]) else None,
                "family": str(data["family"]).strip() if pd.notna(data["family"]) else None
            }
        }
    
    def _process_image(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process image record."""
        return {
            "_id": int(data["id"]),
            "content_type": str(data["content_type"]).lower() if pd.notna(data["content_type"]) else None,
            "copyright_holder": str(data["copyright_holder"]).strip() if pd.notna(data["copyright_holder"]) else None,
            "license": str(data["license"]).strip() if pd.notna(data["license"]) else None,
            "ok_for_export": bool(int(data["ok_for_export"])) if pd.notna(data["ok_for_export"]) else False,
            "created_at": data["created_at"] if pd.notna(data["created_at"]) else None
        }
    
    def _process_image_observation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process image-observation relationship record."""
        return {
            "_id": f"{data['image_id']}_{data['observation_id']}",
            "image_id": int(data["image_id"]),
            "observation_id": int(data["observation_id"])
        }
    
    def _process_location(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process location record."""
        return {
            "_id": int(data["id"]),
            "name": str(data["name"]).strip(),
            "north": float(data["north"]) if pd.notna(data["north"]) else None,
            "south": float(data["south"]) if pd.notna(data["south"]) else None,
            "east": float(data["east"]) if pd.notna(data["east"]) else None,
            "west": float(data["west"]) if pd.notna(data["west"]) else None,
            "high": float(data["high"]) if pd.notna(data["high"]) else None,
            "low": float(data["low"]) if pd.notna(data["low"]) else None
        }
    
    def _process_location_description(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process location description record."""
        return {
            "_id": int(data["id"]),
            "location_id": int(data["location_id"]),
            "source_type": int(data["source_type"]) if pd.notna(data["source_type"]) else None,
            "source_name": str(data["source_name"]).strip() if pd.notna(data["source_name"]) else None,
            "description": str(data["gen_desc"]).strip() if pd.notna(data["gen_desc"]) else None,
            "refs": str(data["refs"]).strip() if pd.notna(data["refs"]) else None,
            "notes": str(data["notes"]).strip() if pd.notna(data["notes"]) else None
        }

async def main() -> None:
    """Main async execution function."""
    try:
        # Load configuration
        config = DataConfig()
        
        # Setup logging
        logging_config = load_yaml_config(config.LOG_CONFIG_PATH)
        logging.config.dictConfig(logging_config)
        
        # Download data files
        logger.info("Downloading Mushroom Observer data files...")
        data_files = await download_mo_data(config)
        
        if not data_files:
            raise DataProcessingError("No data files downloaded")
        
        # Initialize processor and database
        processor = DataProcessor(config)
        db = await get_database(config)
        
        try:
            # Process each data file
            for schema_name, file_path in data_files.items():
                logger.info(f"Processing {schema_name} data")
                async for processed_data in processor.process_file(file_path, schema_name):
                    collection = db.get_collection(schema_name)
                    await db.batch_upsert(collection, processed_data)
                    logger.info(f"Successfully processed {len(processed_data)} {schema_name} records")
            
            logger.info("Data processing completed successfully")
            
        finally:
            await db.close()
            
    except Exception as e:
        logger.exception("Data processing failed")
        raise DataProcessingError(f"Pipeline failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())

