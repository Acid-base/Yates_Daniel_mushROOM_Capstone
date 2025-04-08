"""Data pipeline for processing CSV data and creating species documents."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Import required modules from the project
from config import DataConfig
from enhanced_csv_processor import EnhancedCSVProcessor  # Import EnhancedCSVProcessor
from database import AsyncDatabase
from log_utils import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)

# Define license mapping for standardization
LICENSE_MAPPING = {
    "Creative Commons Wikipedia Compatible v3.0": 1,
    "CC BY-SA": 2,
    "CC BY": 3,
    "Public Domain": 4,
    "All Rights Reserved": 5,
}


class PipelineProgress(BaseModel):
    """Track progress of pipeline processing."""

    total: int = 0
    processed: int = 0
    success: int = 0
    errors: int = 0
    csv_tables_processed: List[str] = []
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    def mark_table_complete(self, table_name: str) -> None:
        """Mark a table as completely processed."""
        self.processed += 1
        self.success += 1
        if table_name not in self.csv_tables_processed:
            self.csv_tables_processed.append(table_name)
        self.save_progress()

    def save_progress(self) -> None:
        """Save current progress to a file."""
        progress_file = Path(__file__).parent.parent / "pipeline_progress.json"
        try:
            # Create progress data structure
            data = {
                "csv_tables_processed": self.csv_tables_processed,
                "api_enrichment": {},  # Will be implemented when API enrichment is added
                "last_update": datetime.now().isoformat(),
                "errors": [],
                "stats": {
                    "total_records": self.total,
                    "processed_records": self.processed,
                    "failed_records": self.errors,
                    "start_time": self.start_time,
                    "end_time": self.end_time,
                },
            }

            # Save to file
            with open(progress_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save pipeline progress: {e}")

    def complete(self) -> None:
        """Mark the pipeline as complete."""
        self.end_time = datetime.now().isoformat()
        self.save_progress()

    def start(self) -> None:
        """Mark the pipeline as started."""
        self.start_time = datetime.now().isoformat()
        self.save_progress()


def save_results_to_json(data: Any, filepath: Path) -> None:
    """Save data to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class DataPipeline:
    """Pipeline for processing CSV data and creating species documents."""

    def __init__(self, config: DataConfig, **kwargs):
        """Initialize the data pipeline."""
        self.config = config
        self.progress = PipelineProgress()
        self.errors: List[str] = []
        self.data_storage: Dict[str, Dict[Any, Any]] = {}
        self.reports: Dict[str, Any] = {}

        # Use EnhancedCSVProcessor instead of the basic CSVProcessor
        self.csv_processor = EnhancedCSVProcessor(config)

        # Store a flag indicating if we're using enhanced processing
        self.using_enhanced_processor = True

        self.db = None

    async def initialize(self) -> None:
        """Initialize async components like database connection."""
        # Initialize database connection if configuration is available
        if self.config.MONGODB_URI and self.config.DATABASE_NAME:
            try:
                # Create AsyncDatabase instance
                self.db = AsyncDatabase(self.config)
                # Connect to database
                await self.db.connect()
                logger.info(
                    f"Connected to MongoDB database: {self.config.DATABASE_NAME}"
                )

                # Set up required indexes
                await self.db.ensure_names_indexes()  # Set up names collection indexes
                await (
                    self.db.ensure_species_indexes()
                )  # Set up species collection indexes

            except Exception as e:
                logger.warning(
                    f"Failed to connect to MongoDB: {e}. Data will be stored in memory only."
                )

    async def process_csv_file(self, file_path: Path, table_name: str) -> bool:
        """Process a single CSV file with report-specific handling."""
        logger.info(f"Processing {table_name} from {file_path}")

        # Log file existence and size
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        logger.info(f"File size: {file_size_mb:.2f} MB")

        # Apply special handling based on documented reports
        special_handling = self._get_special_handling(table_name)
        record_count = 0
        error_count = 0
        chunk_count = 0

        # Log info about using enhanced processing for complex CSV files
        if self.using_enhanced_processor and (
            "name_descriptions" in table_name or "location_descriptions" in table_name
        ):
            logger.info(f"Using enhanced CSV processing for complex file: {table_name}")

        # Use the CSV processor to handle the file with custom settings
        processor_options = special_handling.get("processor_options", {})
        logger.info(f"Using processor options for {table_name}: {processor_options}")

        try:
            # Use read_chunks to process the file
            start_time = datetime.now()
            for records_batch in self.csv_processor.read_chunks(
                file_path, **processor_options
            ):
                chunk_count += 1
                if chunk_count % 10 == 0:
                    # Log progress every 10 chunks
                    elapsed = datetime.now() - start_time
                    logger.info(
                        f"Progress: Processed {chunk_count} chunks from {table_name} ({record_count} records) in {elapsed}"
                    )

                logger.debug(f"Processing chunk {chunk_count} for {table_name}")

                if records_batch is not None and not records_batch.empty:
                    # Apply special chunk processor if available
                    if special_handling.get("chunk_processor"):
                        records_batch = special_handling["chunk_processor"](
                            records_batch
                        )

                    batch_size = len(records_batch)
                    logger.debug(f"Found {batch_size} records in chunk")

                    batch_records = records_batch.to_dict(orient="records")
                    if self.db is not None:
                        # Store records directly using store_records
                        try:
                            # Apply transformations if needed
                            if special_handling.get("transform_func"):
                                logger.debug("Applying transform function")
                                batch_records = special_handling["transform_func"](
                                    batch_records
                                )

                            # Filter records if needed
                            if special_handling.get("filter_func"):
                                logger.debug("Applying filter function")
                                original_count = len(batch_records)
                                batch_records = [
                                    record
                                    for record in batch_records
                                    if special_handling["filter_func"](record)
                                ]
                                filtered_count = len(batch_records)
                                logger.debug(
                                    f"Filtered {original_count - filtered_count} records"
                                )

                            # Store the records
                            logger.debug(
                                f"Storing {len(batch_records)} records in {table_name}"
                            )
                            stored_count = await self.db.store_records(
                                table_name, batch_records
                            )
                            record_count += stored_count
                            logger.debug(f"Successfully stored {stored_count} records")
                        except Exception as e:
                            logger.error(f"Error storing batch: {e}", exc_info=True)
                            error_count += len(batch_records)
                    else:
                        # Store in memory with transformations/filtering
                        if table_name not in self.data_storage:
                            self.data_storage[table_name] = {}

                        transformed_count = 0
                        for record in batch_records:
                            try:
                                # Apply transformations
                                transform_func = special_handling.get("transform_func")
                                if transform_func:
                                    record = transform_func([record])[0]
                                    transformed_count += 1

                                # Apply filters
                                filter_func = special_handling.get("filter_func")
                                if filter_func and not filter_func(record):
                                    continue

                                # For newline-delimited files, use name_id or location_id as key
                                record_id = (
                                    record.get("id")
                                    or record.get("name_id")
                                    or record.get("location_id")
                                )
                                if record_id:
                                    self.data_storage[table_name][record_id] = record
                                    record_count += 1
                                else:
                                    error_count += 1
                                    logger.warning(
                                        f"Record missing ID fields, skipping storage: {record}"
                                    )
                            except Exception as e:
                                error_count += 1
                                logger.error(f"Error processing record: {e}")

                        if transformed_count > 0:
                            logger.debug(
                                f"Transformed {transformed_count} records in memory"
                            )
                else:
                    logger.warning(f"Empty batch received for {table_name}")

            # Log processing results
            elapsed = datetime.now() - start_time
            logger.info(
                f"Finished processing {table_name}: {record_count} records in {elapsed}, {error_count} errors"
            )
            if record_count > 0:
                # Add file to processed list
                self._mark_file_processed(file_path, table_name, record_count)
                return True
            else:
                self._record_error(f"No records processed for {table_name}")
                return False

        except Exception as e:
            logger.error(f"Error processing {table_name}: {e}", exc_info=True)
            self._record_error(f"Error processing {table_name}: {str(e)}")
            return False

    def _get_special_handling(self, table_name: str) -> Dict[str, Any]:
        """Get special handling configuration for a table."""
        special_handling: Dict[str, Any] = {}

        if table_name == "species_table":
            special_handling["transform_func"] = self._transform_species_record
            special_handling["filter_func"] = self._filter_species_record
            special_handling["processor_options"] = {"delimiter": ";"}
        elif table_name == "names":
            special_handling["transform_func"] = self._transform_name_record
            special_handling["processor_options"] = {
                "sep": "\t",
                "header": 0,
                "dtype": str,
                "na_values": ["", "NULL", "null", "NA", "N/A", "n/a", "None", "none"],
                "keep_default_na": True,
                "on_bad_lines": "warn",  # Changed from warn_bad_lines: True
                "encoding": "utf-8",
                "encoding_errors": "replace",
            }
        elif table_name == "name_classifications":
            special_handling["transform_func"] = self._transform_classification_record
            special_handling["processor_options"] = {"delimiter": "\t"}
        elif table_name == "name_descriptions":
            special_handling["transform_func"] = self._transform_description_record
            # Enhanced options for complex files with embedded newlines
            special_handling["processor_options"] = {
                "sep": "\t",
                "quotechar": '"',
                "quoting": 1,  # csv.QUOTE_MINIMAL
                "engine": "python",
                # Additional options for the enhanced processor
                "enhanced_processing": True,
                "allow_embedded_newlines": True,
            }
        elif table_name == "locations":
            special_handling["transform_func"] = self._transform_location_record
            special_handling["processor_options"] = {"delimiter": "\t"}
        elif table_name == "location_descriptions":
            special_handling["transform_func"] = (
                self._transform_location_description_record
            )
            # Enhanced options for complex files with embedded newlines and special formatting
            special_handling["processor_options"] = {
                "sep": "\t",
                "quotechar": '"',
                "quoting": 1,  # csv.QUOTE_MINIMAL
                "engine": "python",
                "encoding": "utf-8",
                "encoding_errors": "replace",
                "na_values": ["", "NULL", "null", "NA", "N/A", "n/a", "None", "none"],
                "keep_default_na": True,
                # Additional options for the enhanced processor
                "enhanced_processing": True,
                "allow_embedded_newlines": True,
                "chunksize": 100  # Process in smaller chunks for complex files
            }
        elif table_name == "observations":
            special_handling["transform_func"] = self._transform_observation_record
            special_handling["processor_options"] = {"delimiter": "\t"}
        elif table_name == "images":
            special_handling["transform_func"] = self._transform_image_record
            special_handling["processor_options"] = {"delimiter": "\t"}
        elif table_name == "images_observations":
            special_handling["transform_func"] = (
                self._transform_image_observation_record
            )
            special_handling["processor_options"] = {"delimiter": "\t"}

        return special_handling

    def _transform_species_record(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform species records."""
        transformed_records = []
        for record in records:
            transformed_record = record.copy()

            # Convert string fields to lowercase for consistency
            for key, value in record.items():
                if isinstance(value, str):
                    transformed_record[key] = value.lower()

            # Handle group names
            is_group = "group" in transformed_record["text_name"].lower()
            transformed_record["is_group"] = is_group

            # Handle synonyms and correct spellings
            if transformed_record.get("synonym_id"):
                transformed_record["synonym_type"] = "synonym"
            elif transformed_record.get("correct_spelling_id"):
                transformed_record["synonym_type"] = "spelling"
            else:
                transformed_record["synonym_type"] = None

            transformed_records.append(transformed_record)

        # Sort by ID to ensure consistent processing
        transformed_records.sort(key=lambda x: x.get("id", 0))
        return transformed_records

    def _filter_species_record(self, record: Dict[str, Any]) -> bool:
        """Filter species records."""
        return bool(record.get("name"))

    def _transform_classification_record(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform classification records."""
        transformed_records = []
        for record in records:
            # Use name_id as the primary key
            transformed_record = record.copy()
            transformed_record["_id"] = record["name_id"]

            # Clean up fields
            for key in ["domain", "kingdom", "phylum", "class", "order", "family"]:
                if key in transformed_record and pd.isna(transformed_record[key]):
                    transformed_record[key] = None
                elif key in transformed_record and isinstance(
                    transformed_record[key], str
                ):
                    transformed_record[key] = transformed_record[key].strip()

            transformed_records.append(transformed_record)
        return transformed_records

    def _transform_description_record(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform name description records."""
        transformed_records = []
        for record in records:
            transformed_record = record.copy()
            transformed_record["_id"] = record.get("id")

            # Clean up text fields
            for field in [
                "gen_desc",
                "diag_desc",
                "distribution",
                "habitat",
                "look_alikes",
                "uses",
                "notes",
                "refs",
            ]:
                if field in transformed_record:
                    if pd.isna(transformed_record[field]):
                        transformed_record[field] = None
                    elif isinstance(transformed_record[field], str):
                        # The enhanced processor already handles HTML and textile markup,
                        # so we just need minimal processing here
                        text = transformed_record[field].strip()
                        if text:
                            transformed_record[field] = text

            # Convert source_type to integer
            if "source_type" in transformed_record:
                try:
                    transformed_record["source_type"] = int(
                        transformed_record["source_type"]
                    )
                    if pd.isna(transformed_record["source_type"]):
                        transformed_record["source_type"] = (
                            0  # Default to system source
                        )
                except (ValueError, TypeError):
                    transformed_record["source_type"] = 0  # Default to system source

            # Ensure source_name exists
            if "source_name" not in transformed_record or pd.isna(
                transformed_record.get("source_name")
            ):
                transformed_record["source_name"] = "Unknown"

            transformed_records.append(transformed_record)
        return transformed_records

    def _transform_location_record(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform location records."""
        transformed_records = []
        for record in records:
            # Validate ID
            record_id = self._validate_id(record.get("id"))
            if not record_id:
                logger.debug(f"Skipping location with invalid ID: {record.get('id')}")
                continue

            transformed_record = record.copy()
            transformed_record["_id"] = record_id
            transformed_record["id"] = record_id

            # Clean up coordinates and ensure they are valid
            for field in ["north", "south", "east", "west"]:
                if field in transformed_record and pd.isna(transformed_record[field]):
                    transformed_record[field] = None
                elif field in transformed_record and isinstance(
                    transformed_record[field], str
                ):
                    try:
                        transformed_record[field] = float(transformed_record[field].strip())
                    except (ValueError, TypeError):
                        transformed_record[field] = None

            # Calculate center coordinates if available
            if all(transformed_record.get(f) is not None for f in ["north", "south", "east", "west"]):
                try:
                    transformed_record["center_lat"] = (
                        float(transformed_record["north"]) + float(transformed_record["south"])
                    ) / 2
                    transformed_record["center_lng"] = (
                        float(transformed_record["east"]) + float(transformed_record["west"])
                    ) / 2
                except (ValueError, TypeError):
                    transformed_record["center_lat"] = None
                    transformed_record["center_lng"] = None
            else:
                transformed_record["center_lat"] = None
                transformed_record["center_lng"] = None

            # Handle elevation data
            if "high" in transformed_record and "low" in transformed_record:
                try:
                    high = (
                        float(transformed_record["high"])
                        if pd.notna(transformed_record["high"])
                        else None
                    )
                    low = (
                        float(transformed_record["low"])
                        if pd.notna(transformed_record["low"])
                        else None
                    )

                    if high is not None and low is not None:
                        transformed_record["elevation_range"] = high - low
                        transformed_record["elevation_avg"] = (high + low) / 2
                    else:
                        # Use whichever value is available
                        transformed_record["elevation_range"] = None
                        transformed_record["elevation_avg"] = high or low
                except (ValueError, TypeError):
                    transformed_record["elevation_range"] = None
                    transformed_record["elevation_avg"] = None

            # Standardize location name
            if "name" in transformed_record:
                if pd.isna(transformed_record["name"]):
                    transformed_record["name"] = None
                elif isinstance(transformed_record["name"], str):
                    # Filter out long descriptive text that's not a proper name
                    if len(transformed_record["name"]) > 100:
                        transformed_record["name"] = None
                    else:
                        # Remove extra whitespace and standardize separators
                        name = " ".join(transformed_record["name"].split())
                        # Capitalize first letter of each word
                        name = name.title()
                        transformed_record["name"] = name

            transformed_records.append(transformed_record)

        if not transformed_records:
            logger.warning("No valid location records found in batch")
        else:
            logger.debug(f"Processed {len(transformed_records)} valid location records")

        return transformed_records

    def _transform_location_description_record(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform location description records."""
        transformed_records = []
        for record in records:
            # Validate ID
            record_id = self._validate_id(record.get("id"))
            if not record_id:
                logger.debug(f"Skipping location description with invalid ID: {record.get('id')}")
                continue

            transformed_record = record.copy()
            transformed_record["_id"] = record_id
            transformed_record["id"] = record_id

            # Validate location_id if present
            if "location_id" in record:
                location_id = self._validate_location(record["location_id"])
                if location_id:
                    transformed_record["location_id"] = location_id
                else:
                    # Skip records with invalid location_id
                    logger.debug(f"Skipping location description {record_id} due to invalid location_id: {record['location_id']}")
                    continue

            # Clean up text fields
            text_fields = ["gen_desc", "ecology", "species", "notes", "refs"]
            for field in text_fields:
                if field in transformed_record:
                    if pd.isna(transformed_record[field]):
                        transformed_record[field] = None
                    elif isinstance(transformed_record[field], str):
                        # Process textile and HTML markup
                        text = transformed_record[field].strip()
                        if text:
                            # Convert textile links to markdown
                            text = re.sub(r'"([^"]+)"\:(\S+)', r"[\1](\2)", text)
                            # Strip HTML tags
                            text = re.sub(r"<[^>]+>", "", text)
                            # Clean up newlines and whitespace
                            paragraphs = [p.strip() for p in text.split("\n\n")]
                            paragraphs = [" ".join(p.split()) for p in paragraphs if p.strip()]
                            text = "\n\n".join(paragraphs)
                            transformed_record[field] = text
                        else:
                            transformed_record[field] = None
                else:
                    transformed_record[field] = None

            # Convert source_type to integer
            if "source_type" in transformed_record:
                try:
                    transformed_record["source_type"] = int(transformed_record["source_type"])
                    if pd.isna(transformed_record["source_type"]):
                        transformed_record["source_type"] = 0
                except (ValueError, TypeError):
                    transformed_record["source_type"] = 0

            # Ensure source_name exists
            if "source_name" not in transformed_record or pd.isna(transformed_record.get("source_name")):
                transformed_record["source_name"] = "Unknown"

            transformed_records.append(transformed_record)

        if not transformed_records:
            logger.warning("No valid location description records found in batch")
        else:
            logger.debug(f"Processed {len(transformed_records)} valid location description records")

        return transformed_records

    def _validate_id(self, id_value: Any) -> Optional[str]:
        """Validate and clean ID values.

        Returns:
            Valid ID string or None if invalid
        """
        if not id_value:
            return None

        # Convert to string and clean
        id_str = str(id_value).strip()

        # Check for obviously invalid values
        if not id_str:  # Empty after stripping
            return None
        if len(id_str) > 100:  # Too long to be an ID
            return None
        if id_str.startswith('\n') or '\n' in id_str:  # Contains newlines
            return None
        if any(x in id_str.lower() for x in ['http', 'www.', '.com', '.org', '.gov', '.edu', '.net']):  # URLs
            return None

        # Check if it looks like descriptive text
        word_count = len(id_str.split())
        if word_count > 3:  # More than 3 words is probably text
            return None

        # Check for obvious species names (italicized or not)
        if '_' in id_str or any(x in id_str for x in ['sp.', 'spp.', 'var.']):
            return None

        # Should be mostly numeric or a very short string
        if not (id_str.isdigit() or len(id_str) < 20):
            return None

        return id_str

    def _validate_location(self, location: Any) -> Optional[str]:
        """Validate location values.

        Returns:
            Valid location ID string or None if invalid
        """
        if not location:
            return None

        # Convert to string and clean
        loc_str = str(location).strip()

        # Check for obviously invalid values
        if not loc_str:  # Empty after stripping
            return None
        if len(loc_str) > 100:  # Too long to be an ID
            return None
        if loc_str.startswith('\n') or '\n' in loc_str:  # Contains newlines
            return None
        if any(x in loc_str.lower() for x in ['http', 'www.', '.com', '.org', '.gov', '.edu', '.net']):  # URLs
            return None

        # Filter out descriptive text that is incorrectly parsed as location IDs
        word_count = len(loc_str.split())
        if word_count > 3:  # More than 3 words is probably text
            return None

        # Check for habitat descriptions
        habitat_words = [
            'tree', 'forest', 'glade', 'ground', 'mainly', 'private', 'public',
            'swamp', 'creek', 'trail', 'park', 'road', 'mountain', 'river',
            'riparian', 'humid', 'dry', 'wet', 'soil', 'climate', 'habitat',
            'vegetation', 'acacia', 'pine', 'oak', 'maple', 'fir', 'cedar'
        ]
        if any(word.lower() in loc_str.lower() for word in habitat_words):
            return None

        # Check for species lists
        if ',' in loc_str and not loc_str.replace(',', '').isdigit():
            return None

        # Check for taxonomic names
        if '_' in loc_str or any(x in loc_str for x in ['sp.', 'spp.', 'var.']):
            return None

        # Should be mostly numeric or a very short string
        if not (loc_str.isdigit() or len(loc_str) < 20):
            return None

        return loc_str

    def _transform_observation_record(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform observation records."""
        transformed_records = []
        for record in records:
            transformed_record = record.copy()

            # Validate ID
            record_id = self._validate_id(record.get("id"))
            if not record_id:
                logger.debug(f"Skipping observation with invalid ID: {record.get('id')}")
                continue

            transformed_record["_id"] = record_id
            transformed_record["id"] = record_id

            # Validate location_id if present
            if "location_id" in record:
                location_id = self._validate_location(record["location_id"])
                if location_id:
                    transformed_record["location_id"] = location_id
                else:
                    transformed_record["location_id"] = None
                    logger.debug(f"Invalid location_id in observation {record_id}: {record['location_id']}")

            # Convert coordinates to float
            for field in ["lat", "lng", "alt"]:
                if field in transformed_record and pd.notna(transformed_record[field]):
                    try:
                        transformed_record[field] = float(transformed_record[field])
                    except (ValueError, TypeError):
                        transformed_record[field] = None

            # Convert vote_cache to float
            if "vote_cache" in transformed_record and pd.notna(
                transformed_record["vote_cache"]
            ):
                try:
                    transformed_record["vote_cache"] = float(
                        transformed_record["vote_cache"]
                    )
                except (ValueError, TypeError):
                    transformed_record["vote_cache"] = None

            transformed_records.append(transformed_record)

        if not transformed_records:
            logger.warning("No valid observation records found in batch")
        else:
            logger.debug(f"Processed {len(transformed_records)} valid observation records")

        return transformed_records

    def _transform_image_record(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform image records."""
        transformed_records = []

        for record in records:
            transformed_record = record.copy()
            transformed_record["_id"] = record.get("id")

            # Handle dimensions
            for field in ["width", "height"]:
                if field in transformed_record and pd.notna(transformed_record[field]):
                    try:
                        transformed_record[field] = int(transformed_record[field])
                    except (ValueError, TypeError):
                        transformed_record[field] = None

            # Convert boolean fields and provide defaults
            for field, default in [("ok_for_export", True), ("diagnostic", False)]:
                if field in transformed_record:
                    try:
                        transformed_record[field] = bool(int(transformed_record[field]))
                    except (ValueError, TypeError):
                        transformed_record[field] = default
                else:
                    transformed_record[field] = default

            # Map license string to license_id if needed
            if "license" in transformed_record and not transformed_record.get(
                "license_id"
            ):
                license_str = str(transformed_record["license"]).strip()
                transformed_record["license_id"] = LICENSE_MAPPING.get(
                    license_str, 1
                )  # Default to 1 if unknown

            # Calculate aspect ratio if dimensions are available
            if transformed_record.get("width") and transformed_record.get("height"):
                transformed_record["aspect_ratio"] = (
                    transformed_record["width"] / transformed_record["height"]
                )

            # Ensure required metadata fields
            transformed_record.setdefault(
                "content_type", "image/jpeg"
            )  # Default to JPEG if not specified
            transformed_record.setdefault(
                "copyright_holder", "Unknown"
            )  # Default copyright holder

            transformed_records.append(transformed_record)

        return transformed_records

    def _transform_image_observation_record(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform image-observation link records."""
        transformed_records = []
        for record in records:
            transformed_record = record.copy()
            transformed_record["_id"] = (
                f"{record['image_id']}_{record['observation_id']}"
            )

            # Convert rank to int
            if "rank" in transformed_record and pd.notna(transformed_record["rank"]):
                transformed_record["rank"] = int(transformed_record["rank"])

            transformed_records.append(transformed_record)
        return transformed_records

    def _transform_name_record(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform name records with proper handling of fields."""
        transformed_records = []
        for record in records:
            transformed_record = record.copy()

            # Ensure required fields are present
            if "id" not in record:
                logger.warning("Skipping name record without id")
                continue

            # Set id as both _id and id for consistency
            transformed_record["_id"] = record["id"]

            # Convert string fields to proper format
            text_fields = [
                "text_name",
                "display_name",
                "search_name",
                "sort_name",
                "author",
                "citation",
                "notes",
            ]
            for field in text_fields:
                if field in transformed_record:
                    if pd.isna(transformed_record[field]):
                        transformed_record[field] = None
                    elif isinstance(transformed_record[field], str):
                        transformed_record[field] = transformed_record[field].strip()
                else:
                    # Initialize missing text fields with appropriate defaults
                    if field in ["text_name", "display_name"]:
                        # These fields should have values
                        transformed_record[field] = None
                    elif field in ["search_name", "sort_name"]:
                        # These can be derived from text_name if missing
                        transformed_record[field] = transformed_record.get("text_name")
                    else:
                        # Optional fields can be None
                        transformed_record[field] = None

            # Handle numeric fields
            numeric_fields = ["rank", "synonym_id", "correct_spelling_id"]
            for field in numeric_fields:
                if field in transformed_record:
                    try:
                        if pd.notna(transformed_record[field]):
                            transformed_record[field] = int(transformed_record[field])
                        else:
                            transformed_record[field] = None
                    except (ValueError, TypeError):
                        transformed_record[field] = None
                else:
                    transformed_record[field] = None

            # Handle boolean fields
            bool_fields = ["deprecated", "ok_for_export"]
            for field in bool_fields:
                if field in transformed_record:
                    try:
                        value = transformed_record[field]
                        if isinstance(value, str):
                            transformed_record[field] = value.lower() in (
                                "true",
                                "1",
                                "t",
                                "yes",
                            )
                        elif isinstance(value, (int, float)):
                            transformed_record[field] = bool(value)
                        elif pd.isna(value):
                            transformed_record[field] = False
                    except (ValueError, TypeError):
                        transformed_record[field] = False
                else:
                    transformed_record[field] = False

            # Set defaults for required fields
            transformed_record.setdefault("deprecated", False)
            transformed_record.setdefault("ok_for_export", True)

            # Clean up classification
            if "classification" in transformed_record and pd.notna(
                transformed_record["classification"]
            ):
                transformed_record["classification"] = str(
                    transformed_record["classification"]
                ).strip()
            else:
                transformed_record["classification"] = None

            # Ensure required name fields are present and derive if possible
            required_name_fields = [
                "text_name",
                "display_name",
                "search_name",
                "sort_name",
            ]

            # Try to derive missing fields from text_name
            if transformed_record.get("text_name"):
                if not transformed_record.get("display_name"):
                    transformed_record["display_name"] = transformed_record["text_name"]
                if not transformed_record.get("search_name"):
                    # Create a searchable version of the name (lowercase, no special chars)
                    search_name = re.sub(r'[^a-zA-Z0-9\s]', '', transformed_record["text_name"]).lower()
                    transformed_record["search_name"] = search_name
                if not transformed_record.get("sort_name"):
                    # Use text_name as sort_name if not provided
                    transformed_record["sort_name"] = transformed_record["text_name"]

            # Check required fields after attempting to derive them
            missing_fields = [
                field for field in required_name_fields
                if not transformed_record.get(field)
            ]

            if missing_fields:
                logger.warning(
                    f"Skipping name record {record.get('id')} due to missing required fields: {', '.join(missing_fields)}"
                )
                logger.debug(f"Record contents: {record}")
                continue

            transformed_records.append(transformed_record)

        if not transformed_records:
            logger.error("No name records were successfully transformed")
            logger.debug(f"Sample of rejected records: {records[:5] if records else 'No records'}")
        else:
            logger.info(f"Successfully transformed {len(transformed_records)} name records")

        return transformed_records

    async def cleanup(self):
        """Clean up resources."""
        if self.db is not None:
            await self.db.close()

    async def create_species_documents(self) -> bool:
        """Create species documents from processed data."""
        try:
            species_docs = []
            synonym_map = {}  # Track synonym relationships

            # First pass - build synonym map
            if "names" in self.data_storage:
                for name_id, name_record in self.data_storage["names"].items():
                    if name_record.get("synonym_id"):
                        if name_record["synonym_id"] not in synonym_map:
                            synonym_map[name_record["synonym_id"]] = []
                        synonym_map[name_record["synonym_id"]].append(
                            {
                                "name": name_record["text_name"],
                                "author": name_record.get("author"),
                                "deprecated": name_record.get("deprecated", False),
                            }
                        )

            # Process names to create base species documents
            if "names" in self.data_storage:
                for name_id, name_record in self.data_storage["names"].items():
                    # Skip deprecated names that are synonyms
                    if name_record.get("deprecated") and name_record.get("synonym_id"):
                        continue

                    species_doc = {
                        "_id": name_id,
                        "scientific_name": name_record["text_name"],
                        "author": name_record.get("author"),
                        "rank": name_record["rank"],
                        "deprecated": name_record.get("deprecated", False),
                        "synonyms": synonym_map.get(name_id, []),
                        "is_group": "group" in name_record["text_name"].lower(),
                    }

                    # Add classification if available
                    if "name_classifications" in self.data_storage:
                        classifications = [
                            c
                            for c in self.data_storage["name_classifications"].values()
                            if c["name_id"] == name_id
                        ]
                        if classifications:
                            species_doc["classification"] = (
                                self._process_classification(classifications[0])
                            )

                    # Add descriptions if available
                    if "name_descriptions" in self.data_storage:
                        descriptions = [
                            d
                            for d in self.data_storage["name_descriptions"].values()
                            if d["name_id"] == name_id
                        ]
                        if descriptions:
                            species_doc["descriptions"] = self._merge_descriptions(
                                descriptions
                            )

                    # Add observations if available
                    if "observations" in self.data_storage:
                        observations = [
                            o
                            for o in self.data_storage["observations"].values()
                            if o["name_id"] == name_id
                        ]
                        if observations:
                            species_doc["observations"] = self._process_observations(
                                observations
                            )

                    # Add images if available
                    if (
                        "images" in self.data_storage
                        and "images_observations" in self.data_storage
                    ):
                        species_doc["images"] = self._process_images(name_id)

                    # Add search terms for improved searchability
                    search_terms = set([species_doc["scientific_name"].lower()])
                    search_terms.update(
                        syn["name"].lower() for syn in species_doc["synonyms"]
                    )
                    if "common_names" in name_record:
                        search_terms.update(
                            n.lower() for n in name_record["common_names"]
                        )
                    species_doc["search_terms"] = list(search_terms)

                    species_docs.append(species_doc)

                # Store all species documents
                if self.db is not None:
                    stored_count = await self.db.store_species_batch(species_docs)
                    if stored_count != len(species_docs):
                        logger.warning(
                            f"Only {stored_count} out of {len(species_docs)} species documents were stored"
                        )
                else:
                    # Store in memory
                    self.data_storage["species"] = {
                        doc["_id"]: doc for doc in species_docs
                    }

            return True

        except Exception as e:
            logger.error(f"Error creating species documents: {e}")
            self.errors.append(f"Failed to create species documents: {e}")
            return False

    def _process_classification(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Process and standardize taxonomic classification."""
        processed = {}

        # Standard taxonomic ranks
        ranks = ["domain", "kingdom", "phylum", "class", "order", "family", "genus"]

        # Copy and clean each rank
        for rank in ranks:
            value = classification.get(rank)
            if value and isinstance(value, str):
                # Capitalize and clean whitespace
                processed[rank] = value.strip().capitalize()
            else:
                processed[rank] = None

        # Calculate completeness
        valid_ranks = sum(1 for r in ranks if processed.get(r))
        processed["taxonomic_completeness"] = valid_ranks / len(ranks)

        return processed

    async def run_pipeline_async(self) -> bool:
        """Run the complete pipeline asynchronously."""
        try:
            # Initialize async components
            await self.initialize()

            # Start tracking progress
            self.progress.start()

            # Define the order of processing
            process_order = [
                ("names", "names.csv"),
                ("name_classifications", "name_classifications.csv"),
                ("name_descriptions", "name_descriptions.csv"),
                ("locations", "locations.csv"),
                ("location_descriptions", "location_descriptions.csv"),
                ("observations", "observations.csv"),
                ("images", "images.csv"),
                ("images_observations", "images_observations.csv"),
            ]

            # Count total records to process
            total_records = 0
            for table_name, filename in process_order:
                file_path = Path(self.config.DATA_DIR) / filename
                if file_path.exists():
                    try:
                        # Use CSV processor to count records
                        for chunk in self.csv_processor.read_chunks(file_path):
                            if chunk is not None and not chunk.empty:
                                total_records += len(chunk)
                    except Exception as e:
                        logger.warning(f"Error counting records in {filename}: {e}")

            self.progress.total = total_records

            # Process all CSV files
            for table_name, filename in process_order:
                file_path = Path(self.config.DATA_DIR) / filename
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue

                success = await self.process_csv_file(file_path, table_name)
                if not success:
                    logger.error(f"Failed to process {filename}")
                    continue

            # Create species documents after all data is processed
            success = await self.create_species_documents()
            if not success:
                logger.error("Failed to create species documents")
                return False

            # Mark pipeline as complete
            self.progress.complete()
            return True

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            self.errors.append(f"Pipeline execution failed: {e}")
            return False

    def _merge_descriptions(self, descriptions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple descriptions into a single comprehensive description.

        This function intelligently combines text from multiple descriptions,
        preserving source attribution and removing redundancy.
        """
        if not descriptions:
            return {
                "general": "",
                "diagnostic": "",
                "distribution": "",
                "habitat": "",
                "look_alikes": "",
                "uses": "",
                "notes": "",
                "sources": [],
            }

        # Initialize merged description structure
        merged = {
            "general": [],
            "diagnostic": [],
            "distribution": [],
            "habitat": [],
            "look_alikes": [],
            "uses": [],
            "notes": [],
            "sources": [],
        }

        # First pass: Collect all description sections from different sources
        for desc in descriptions:
            if desc.get("gen_desc"):
                merged["general"].append(desc["gen_desc"])
            if desc.get("diag_desc"):
                merged["diagnostic"].append(desc["diag_desc"])
            if desc.get("distribution"):
                merged["distribution"].append(desc["distribution"])
            if desc.get("habitat"):
                merged["habitat"].append(desc["habitat"])
            if desc.get("look_alikes"):
                merged["look_alikes"].append(desc["look_alikes"])
            if desc.get("uses"):
                merged["uses"].append(desc["uses"])
            if desc.get("notes"):
                merged["notes"].append(desc["notes"])

            # Track sources for proper attribution
            merged["sources"].append(
                {
                    "source_type": desc.get("source_type"),
                    "source_name": desc.get("source_name"),
                }
            )

        # Intelligently combine text for each field
        for key in merged:
            if key == "sources":
                continue

            # Remove duplicates while preserving order
            unique_texts = []
            for text in merged[key]:
                # Skip empty or None values
                if not text:
                    continue

                # Only add text if not already included in existing texts
                if not any(
                    self._is_text_similar(text, existing) for existing in unique_texts
                ):
                    unique_texts.append(text)

            # Join with paragraph separators
            if unique_texts:
                merged[key] = "\n\n".join(unique_texts)
            else:
                merged[key] = ""

        return merged

    def _is_text_similar(
        self, text1: str, text2: str, similarity_threshold: float = 0.8
    ) -> bool:
        """Check if two text strings are similar to avoid duplication.

        Uses a simple similarity metric based on common words.

        Args:
            text1: First text string
            text2: Second text string
            similarity_threshold: Threshold above which texts are considered similar (0-1)

        Returns:
            Boolean indicating if texts are similar
        """
        if not text1 or not text2:
            return False

        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Ignore very short texts
        if len(words1) < 5 or len(words2) < 5:
            return text1.lower() == text2.lower()

        # Check for containment (one text fully contains the other)
        if text1.lower() in text2.lower() or text2.lower() in text1.lower():
            return True

        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)

        similarity = len(intersection) / len(union) if union else 0

        return similarity > similarity_threshold

    def _process_observations(
        self, observations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process observations into a summary document."""
        if not observations:
            return {}

        # Calculate vote statistics
        votes = [o["vote_cache"] for o in observations if "vote_cache" != None]
        vote_stats = {
            "min": min(votes) if votes else None,
            "max": max(votes) if votes else None,
            "avg": sum(votes) / len(votes) if votes else None,
        }

        # Process individual observations
        processed_obs = []
        for obs in observations:
            processed_obs.append(
                {
                    "id": obs["id"],
                    "when": obs["when"],
                    "location_id": obs.get("location_id"),
                    "lat": obs.get("lat"),
                    "lng": obs.get("lng"),
                    "alt": obs.get("alt"),
                    "vote_cache": obs.get("vote_cache"),
                    "is_collection_location": obs.get("is_collection_location", True),
                }
            )

        return {
            "observation_count": len(observations),
            "vote_stats": vote_stats,
            "observations": processed_obs,
        }

    def _process_images(self, name_id: str) -> List[Dict[str, Any]]:
        """Process images for a species."""
        if not self.data_storage.get("images") or not self.data_storage.get(
            "images_observations"
        ):
            return []

        # Get observations for this name
        species_observations = {
            o["id"]: o
            for o in self.data_storage["observations"].values()
            if o["name_id"] == name_id
        }

        # Get image-observation links for these observations
        image_links = [
            link
            for link in self.data_storage["images_observations"].values()
            if link["observation_id"] in species_observations
        ]

        # Get and process the actual images
        processed_images = []
        for link in image_links:
            image = self.data_storage["images"].get(link["image_id"])
            if image:
                processed_images.append(
                    {
                        "image_id": image["id"],
                        "content_type": image["content_type"],
                        "copyright_holder": image["copyright_holder"],
                        "license_id": image["license_id"],
                        "ok_for_export": image.get("ok_for_export", True),
                        "diagnostic": image.get("diagnostic", False),
                        "width": image.get("width"),
                        "height": image.get("height"),
                        "rank": link.get("rank", 0),
                    }
                )

        # Sort by rank and diagnostic status
        return sorted(
            processed_images,
            key=lambda x: (-x.get("diagnostic", False), x.get("rank", 0)),
        )

    def _record_error(self, error_message: str) -> None:
        """Record an error message and update the progress tracking."""
        logger.error(error_message)
        self.errors.append(error_message)
        self.progress.errors += 1

    def _mark_file_processed(
        self, file_path: Path, table_name: str, record_count: int
    ) -> None:
        """Mark a file as processed and update progress tracking."""
        logger.info(f"Processed {record_count} records from {table_name}")
        self.progress.mark_table_complete(table_name)
        self.progress.processed += record_count
        self.progress.save_progress()
