import asyncio
import logging
import time
from abc import ABC, abstractmethod
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

import pandas as pd
import yaml
from aiohttp import ClientSession
from pydantic import BaseModel, DirectoryPath, Field, HttpUrl
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from dotenv import load_dotenv

load_dotenv()

# --- Configuration Classes ---
class DataConfig(BaseModel):
    """Configuration for data processing."""

    mongo_uri: str = Field(..., description="MongoDB connection URI")
    mongo_db: str = Field(..., description="MongoDB database name")
    mo_base_url: HttpUrl = Field(..., description="Mushroom Observer base URL")
    data_dir: DirectoryPath = Field(..., description="Data directory path")
    date_format: str = Field("%Y-%m-%d", description="Date parsing format")
    schemas: List[str] = Field(..., description="List of schema names")
    batch_size: int = Field(1000, ge=1, description="Processing batch size")
    default_delimiter: str = Field(",", min_length=1, description="CSV delimiter")
    null_values: Set[str] = Field(
        default_factory=lambda: {"", "NA", "NULL", "None"},
        description="Values to treat as null",
    )

    class Config:
        validate_assignment = True


# --- Schema Definitions ---
SCHEMAS = {
    "observations": {
        "id": {"validators": ["id"]},
        "name_id": {"validators": ["id"]},
        "location_id": {"validators": ["id"]},
        "date": {"validators": ["date"]},
        "latitude": {"validators": ["float"]},
        "longitude": {"validators": ["float"]},
        "elevation": {"validators": ["float"]},
        "notes": {"validators": ["string"]},
    },
    "names": {
        "id": {"validators": ["id"]},
        "name": {"validators": ["string"]},
    },
    "name_classifications": {
        "id": {"validators": ["id"]},
        "name_id": {"validators": ["id"]},
        "domain": {"validators": ["string"]},
        "kingdom": {"validators": ["string"]},
        "phylum": {"validators": ["string"]},
        "class": {"validators": ["string"]},
        "order": {"validators": ["string"]},
        "family": {"validators": ["string"]},
    },
    "images": {
        "id": {"validators": ["id"]},
        "content_type": {"validators": ["string"]},
        "copyright_holder": {"validators": ["string"]},
        "license": {"validators": ["string"]},
        "ok_for_export": {"validators": ["boolean"]},
        "created_at": {"validators": ["date"]},
    },
    "images_observations": {
        "image_id": {"validators": ["id"]},
        "observation_id": {"validators": ["id"]},
    },
    "locations": {
        "id": {"validators": ["id"]},
        "name": {"validators": ["string"]},
        "north": {"validators": ["float"]},
        "south": {"validators": ["float"]},
        "east": {"validators": ["float"]},
        "west": {"validators": ["float"]},
        "high": {"validators": ["float"]},
        "low": {"validators": ["float"]},
    },
    "location_descriptions": {
        "id": {"validators": ["id"]},
        "location_id": {"validators": ["id"]},
        "source_type": {"validators": ["id"]},
        "source_name": {"validators": ["string"]},
        "gen_desc": {"validators": ["string"]},
        "refs": {"validators": ["string"]},
        "notes": {"validators": ["string"]},
    },
}


# --- Logging Setup ---
logger = logging.getLogger(__name__)


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Load logging configuration from YAML file."""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise FileProcessingError(f"Configuration file not found: {config_path}")


# --- Custom Exceptions ---
class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


class FileProcessingError(Exception):
    """Custom exception for file processing errors."""

    pass


class DataProcessingError(Exception):
    """Custom exception for general data processing errors."""

    pass


# --- Performance Decorator ---
def measure_performance(func):
    """Decorator to measure the execution time of a function."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        logger.info(
            f"Function {func.__name__} took {end_time - start_time:.4f} seconds to execute."
        )
        return result

    return wrapper


# --- Data Download Functions ---
async def download_mo_data(config: DataConfig) -> Dict[str, Path]:
    """Download data files from Mushroom Observer."""
    data_files = {}
    async with ClientSession() as session:
        for schema_name in config.schemas:
            url = f"{config.mo_base_url}/{schema_name}.csv"
            file_path = Path(config.data_dir) / f"{schema_name}.csv"
            try:
                await _download_file(session, url, file_path)
                data_files[schema_name] = file_path
            except Exception as e:
                logger.error(f"Failed to download {schema_name} data: {e}")
    return data_files


async def _download_file(session: ClientSession, url: str, file_path: Path) -> None:
    """Download a single file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    async with session.get(url) as response:
        response.raise_for_status()
        with open(file_path, "wb") as f:
            while True:
                chunk = await response.content.readany()
                if not chunk:
                    break
                f.write(chunk)
    logger.info(f"Downloaded {url} to {file_path}")


# --- Database Functions ---
async def get_database(config: DataConfig) -> "DatabaseManager":
    """Get a MongoDB database connection."""
    client = MongoClient(config.mongo_uri)
    db = client[config.mongo_db]
    return DatabaseManager(db)


class DatabaseManager:
    """Manages database operations."""

    def __init__(self, db: Database):
        self.db = db

    async def batch_upsert(
        self, collection: Collection, data: List[Dict[str, Any]]
    ) -> None:
        """Upsert a batch of data into a MongoDB collection."""
        if not data:
            return

        insert_data = []
        update_operations = []
        for record in data:
            if "_id" in record:
                update_operations.append(
                    {
                        "replaceOne": {
                            "filter": {"_id": record["_id"]},
                            "replacement": record,
                            "upsert": True,
                        }
                    }
                )
            else:
                insert_data.append(record)

        if insert_data:
            await collection.insert_many(insert_data)
        if update_operations:
            await collection.bulk_write(update_operations)

    def get_collection(self, name: str) -> Collection:
        """Get a MongoDB collection."""
        return self.db[name]

    async def close(self) -> None:
        """Close the database connection."""
        self.db.client.close()


# --- Validator Classes ---
class Validator(ABC):
    """Abstract base class for validators."""

    @abstractmethod
    def validate(self, value: Any) -> Tuple[bool, str]:
        """Validate a value."""
        pass


class DateValidator(Validator):
    """Validator for date strings."""

    def __init__(self, date_format: str):
        self.date_format = date_format

    def validate(self, value: Any) -> Tuple[bool, str]:
        """Validate a date string."""
        if value is None:
            return True, ""
        try:
            pd.to_datetime(value, format=self.date_format, errors="raise")
            return True, ""
        except (ValueError, TypeError):
            return False, f"Invalid date format: {value}"


class LocationValidator(Validator):
    """Validator for location data."""

    def validate(self, value: Any) -> Tuple[bool, str]:
        """Validate location data."""
        if value is None:
            return True, ""
        if isinstance(value, dict) and "lat" in value and "lng" in value:
            try:
                float(value["lat"])
                float(value["lng"])
                return True, ""
            except (ValueError, TypeError):
                return False, f"Invalid location format: {value}"
        return False, f"Invalid location format: {value}"


class IdValidator(Validator):
    """Validator for ID values."""

    def validate(self, value: Any) -> Tuple[bool, str]:
        """Validate an ID value."""
        if value is None:
            return True, ""
        if isinstance(value, (int, str)):
            try:
                if isinstance(value, str):
                    int(value)
                return True, ""
            except (ValueError, TypeError):
                return False, f"Invalid ID format: {value}"
        return False, f"Invalid ID format: {value}"


class BooleanValidator(Validator):
    """Validator for boolean values."""

    def validate(self, value: Any) -> Tuple[bool, str]:
        """Validate a boolean value."""
        if value is None:
            return True, ""
        if isinstance(value, bool):
            return True, ""
        return False, f"Invalid boolean format: {value}"


class StringValidator(Validator):
    """Validator for string values."""

    def validate(self, value: Any) -> Tuple[bool, str]:
        """Validate a string value."""
        if value is None:
            return True, ""
        if isinstance(value, str):
            return True, ""
        return False, f"Invalid string format: {value}"


class FloatValidator(Validator):
    """Validator for float values."""

    def validate(self, value: Any) -> Tuple[bool, str]:
        """Validate a float value."""
        if value is None:
            return True, ""
        try:
            float(value)
            return True, ""
        except (ValueError, TypeError):
            return False, f"Invalid float format: {value}"


# --- Validation Functions ---
class ValidationResult(BaseModel):
    """Represents the result of a validation."""

    is_valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    record: Optional[Dict[str, Any]] = Field(None, description="Validated record")

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


def validate_with_schema(
    data: Dict[str, Any], schema: Dict[str, Any], validators: Dict[str, Validator]
) -> ValidationResult:
    """
    Validate data against a schema using the provided validators.

    This function iterates through the fields defined in the schema and applies
    the corresponding validators to each field's value in the data. If a field
    has multiple validators, each one is applied in sequence. If a validator
    fails, an error message is recorded, and the overall validation result is
    marked as invalid. If a validator is unknown, a warning is recorded.

    Args:
        data (Dict[str, Any]): The data to be validated, where keys are field
            names and values are the corresponding field values.
        schema (Dict[str, Any]): The schema defining the structure and validation
            rules for the data. Each field in the schema may specify one or more
            validators to apply.
        validators (Dict[str, Validator]): A dictionary
            mapping validator names to callable validator functions. Each
            validator function takes a value and returns a tuple containing a
            boolean indicating whether the value is valid and an error message
            if the value is invalid.

    Returns:
        ValidationResult: An object containing the validation result, including
            whether the data is valid, a list of error messages, and a list of
            warnings for unknown validators.
    """
    errors = []
    warnings = []
    is_valid = True

    for field, field_schema in schema.items():
        if "validators" in field_schema:
            is_valid, errors, warnings = _validate_field(
                field, field_schema, data, validators, is_valid, errors, warnings
            )

    return ValidationResult(
        is_valid=is_valid, errors=errors, warnings=warnings, record=data
    )


def _validate_field(
    field: str,
    field_schema: Dict[str, Any],
    data: Dict[str, Any],
    validators: Dict[str, Validator],
    is_valid: bool,
    errors: List[str],
    warnings: List[str],
) -> Tuple[bool, List[str], List[str]]:
    """Validate a single field against its schema."""
    new_errors = errors[:]
    new_warnings = warnings[:]
    new_is_valid = is_valid
    for validator_name in field_schema["validators"]:
        validator = validators.get(validator_name)
        if validator:
            value = data.get(field)
            valid, error_message = validator.validate(value)
            if not valid:
                new_errors.append(f"Field '{field}': {error_message}")
                new_is_valid = False
            else:
                new_warnings.append(
                    f"Unknown validator: {validator_name} for field {field}"
                )
    return new_is_valid, new_errors, new_warnings


def create_validators(config: DataConfig) -> Dict[str, Validator]:
    """Create validator instances."""
    return {
        "date": DateValidator(config.date_format),
        "id": IdValidator(),
        "location": LocationValidator(),
        "boolean": BooleanValidator(),
        "string": StringValidator(),
        "float": FloatValidator(),
    }


async def process_data_files(
    config: DataConfig, data_files: Dict[str, Path], db_manager: DatabaseManager
) -> None:
    """Process data files and insert into MongoDB."""
    validators = create_validators(config)
    for schema_name, file_path in data_files.items():
        schema = SCHEMAS.get(schema_name)
        if not schema:
            logger.warning(f"No schema found for {schema_name}, skipping")
            continue
        collection = db_manager.get_collection(schema_name)
        await _process_file(
            config, file_path, schema, validators, collection, db_manager
        )


async def _process_file(
    config: DataConfig,
    file_path: Path,
    schema: Dict[str, Any],
    validators: Dict[str, Validator],
    collection: Collection,
    db_manager: DatabaseManager,
) -> None:
    """Process a single data file."""
    try:
        async for batch in _read_csv_in_batches(config, file_path):
            validated_batch = []
            for record in batch:
                validation_result = validate_with_schema(record, schema, validators)
                if validation_result.is_valid:
                    validated_batch.append(record)
                else:
                    logger.warning(
                        f"Record failed validation: {validation_result.errors} in {record}"
                    )
            await db_manager.batch_upsert(collection, validated_batch)
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        raise DataProcessingError(f"Error processing {file_path}: {e}")


async def _read_csv_in_batches(
    config: DataConfig, file_path: Path
) -> AsyncGenerator[List[Dict[str, Any]], None]:
    """Read a CSV file in batches."""
    try:
        df_chunks = pd.read_csv(
            file_path,
            chunksize=config.batch_size,
            na_values=config.null_values,
            keep_default_na=True,
            encoding="utf-8",
        )
        for df_chunk in df_chunks:
            records = df_chunk.to_dict(orient="records")
            yield records
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {e}")
        raise FileProcessingError(f"Error reading CSV file {file_path}: {e}")


@measure_performance
async def main():
    """Main function to run the data pipeline."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    config_path = "config.yaml"
    try:
        config_data = load_yaml_config(config_path)
        config = DataConfig(**config_data)
        data_files = await download_mo_data(config)
        db_manager = await get_database(config)
        await process_data_files(config, data_files, db_manager)
        await db_manager.close()
        logger.info("Data pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Data pipeline failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
