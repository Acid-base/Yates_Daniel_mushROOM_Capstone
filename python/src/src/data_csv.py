from __future__ import annotations

import csv
import logging
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Final
from dataclasses import dataclass, asdict
import functools
import logging.config
import yaml
import os
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection
import re
from enum import Enum

try:
    import pandas as pd
except ImportError as e:
    logging.error(f"Failed to import required package: {e}")
    raise

# At the top of your file, after imports
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')
Schema = Dict[str, type]
DataDict = Dict[str, List[Dict[str, Any]]]
DataFrameTransform = Callable[[pd.DataFrame], pd.DataFrame]

@dataclass(frozen=True)
class DataConfig:
    """Configuration constants for data processing."""
    MONGODB_URI: Final[str] = "mongodb://localhost:27017/"
    DATABASE_NAME: Final[str] = "my_database"
    BATCH_SIZE: Final[int] = 1000
    DEFAULT_DELIMITER: Final[str] = "\t"
    NULL_VALUES: Final[tuple[str, ...]] = ("NULL",)
    DATE_FORMAT: Final[str] = "%Y-%m-%d"

# Schema definitions
SCHEMAS: Final[Dict[str, Schema]] = {
    "observations": {
        "id": int,
        "name_id": int,
        "when": str,
        "location_id": int,
        "lat": float,
        "lng": float,
        " alt": float,
        "vote_cache": float,
        "is_collection_location": bool,
        "thumb_image_id": int
    },
    "names": {
        "id": int,
        "text_name": str,
        "author": str,
        "deprecated": bool,
        "correct_spelling_id": int,
        "synonym_id": int,
        "rank": int
    },
    "name_descriptions": {
        "id": int,
        "name_id": int,
        "source_type": int,
        "source_name": str,
        "general_description": str,
        "diagnostic_description": str,
        "distribution": str,
        "habitat": str,
        "look_alikes": str,
        "uses": str,
        "notes": str,
        "refs": str
    },
    "name_classifications": {
        "id": int,
        "name_id": int,
        "domain": str,
        "kingdom": str,
        "phylum": str,
        "class": str,
        "order": str,
        "family": str
    }
}

# Utility functions
def safe_cast(value: Any, to_type: type, default: Any = None) -> Any:
    """Safely cast a value to a given type."""
    if value is None or value == "NULL" or value == "":
        return default
    try:
        return to_type(value)
    except (ValueError, TypeError):
        if to_type == float:
            return default
        return value

def compose(*functions: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """Compose multiple functions from left to right."""
    return functools.reduce(lambda f, g: lambda x: g(f(x)), functions)

def pipe(value: T, *functions: Callable[[T], T]) -> T:
    """Pipe a value through a series of functions."""
    return functools.reduce(lambda acc, f: f(acc), functions, value)

# Data loading functions
def load_csv_data(
    filename: Path,
    schema: Optional[Schema] = None,
    delimiter: str = DataConfig.DEFAULT_DELIMITER
) -> List[Dict[str, Any]]:
    """Load and validate CSV data."""
    try:
        with open(filename, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)

            if schema:
                validate_schema(reader.fieldnames, schema, filename)

            data = []
            for row in reader:
                processed_row = {}
                for field, value in row.items():
                    if schema and field in schema:
                        if value == "NULL" or value == "":
                            processed_row[field] = None
                        else:
                            try:
                                processed_row[field] = schema[field](value)
                            except (ValueError, TypeError):
                                if schema[field] == float:
                                    processed_row[field] = None
                                else:
                                    processed_row[field] = value
                    else:
                        processed_row[field] = value
                data.append(processed_row)
            return data
    except FileNotFoundError:
        logging.error(f"File not found: {filename}")
        return []
    except Exception as e:
        logging.error(f"Error loading {filename}: {str(e)}")
        return []

def validate_schema(fieldnames: List[str], schema: Schema, filename: Path) -> None:
    """Validate CSV headers against schema."""
    missing_fields = set(schema.keys()) - set(fieldnames)
    if missing_fields:
        logging.warning(f"Fields {missing_fields} not found in {filename}")

# Data processing functions
def process_names(data: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Process names data into standardized format."""
    result = {}
    for item in data:
        name_id = int(item["id"])
        result[name_id] = {
            "_id": name_id,
            "text_name": (item.get("text_name") or "").strip(),
            "author": (item.get("author") or "").strip(),
            "deprecated": safe_cast(item.get("deprecated"), bool),
            "correct_spelling_id": safe_cast(item.get("correct_spelling_id"), int),
            "synonym_id": safe_cast(item.get("synonym_id"), int),
            "rank": safe_cast(item.get("rank"), int)
        }
    return result

def process_name_descriptions(
    descriptions: List[Dict[str, Any]],
    species_data: Dict[int, Dict[str, Any]]
) -> Dict[int, Dict[str, Any]]:
    """Process name descriptions and merge with species data.

    Args:
        descriptions: List of name description records
        species_data: Existing species data dictionary

    Returns:
        Updated species data dictionary with descriptions merged
    """
    # Process descriptions into a lookup by name_id
    desc_by_name = defaultdict(list)
    for item in descriptions:
        name_id = safe_cast(item["name_id"], int)
        if name_id:
            desc_by_name[name_id].append({
                "source_type": safe_cast(item["source_type"], int),
                "source_name": clean_text(item.get("source_name")),
                "general_description": clean_text(item.get("general_description")),
                "diagnostic_description": clean_text(item.get("diagnostic_description")),
                "distribution": clean_text(item.get("distribution")),
                "habitat": clean_text(item.get("habitat")),
                "look_alikes": clean_text(item.get("look_alikes")),
                "uses": clean_text(item.get("uses")),
                "notes": clean_text(item.get("notes")),
                "refs": clean_text(item.get("refs"))
            })

    # Merge descriptions into species data
    return {
        species_id: {
            **species_data,
            "descriptions": desc_by_name.get(species_id, [])
        }
        for species_id, species_data in species_data.items()
    }

def process_name_classifications(data: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Process taxonomic classifications into standardized format."""
    result = {}
    for item in data:
        class_id = int(item["id"])
        result[class_id] = {
            "_id": class_id,
            "domain": clean_text(item.get("domain")),
            "kingdom": clean_text(item.get("kingdom")),
            "phylum": clean_text(item.get("phylum")),
            "class": clean_text(item.get("class")),
            "order": clean_text(item.get("order")),
            "family": clean_text(item.get("family"))
        }
    return result

def process_observations(
    observations: List[Dict[str, Any]],
    images_observations: List[Dict[str, Any]]
) -> Tuple[Dict[int, List[Dict[str, Any]]], Dict[int, List[int]]]:
    """Process observations and image-observation relationships.

    Args:
        observations: List of observation records
        images_observations: List of image-observation relationship records

    Returns:
        Tuple containing:
        - Dict mapping name_id to list of observation records
        - Dict mapping observation_id to list of image_ids
    """
    # Process image-observation relationships first
    images_by_obs = defaultdict(list)
    for rel in images_observations:
        obs_id = int(rel["observation_id"])
        img_id = int(rel["image_id"])
        images_by_obs[obs_id].append(img_id)

    # Process observations and group by name_id
    obs_by_name = defaultdict(list)
    for item in observations:
        obs_id = int(item["id"])
        name_id = int(item["name_id"])

        processed_obs = {
            "_id": obs_id,
            "name_id": name_id,
            "when": item["when"],
            "location_id": safe_cast(item["location_id"], int),
            "lat": safe_cast(item["lat"], float),
            "lng": safe_cast(item["lng"], float),
            "alt": safe_cast(item[" alt"], float),
            "vote_cache": safe_cast(item["vote_cache"], float),
            "is_collection_location": bool(int(item["is_collection_location"])),
            "thumb_image_id": safe_cast(item["thumb_image_id"], int),
            "images": images_by_obs.get(obs_id, [])  # Add associated image IDs
        }

        obs_by_name[name_id].append(processed_obs)

    return dict(obs_by_name), dict(images_by_obs)

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string with error handling."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, DataConfig.DATE_FORMAT)
    except (ValueError, TypeError):
        logger.warning(f"Invalid date format: {date_str}", extra={
            'date_str': date_str,
            'format': DataConfig.DATE_FORMAT
        })
        return None

def validate_observation(
    observation: Dict[str, Any],
    images_by_obs: Dict[int, Set[int]],
    names: Dict[int, Any],
    locations: Dict[int, Any]
) -> List[str]:
    """Validate observation data and relationships."""
    issues = []
    obs_id = observation["_id"]

    # Check name reference
    if observation["name_id"] not in names:
        issues.append(f"Invalid name_id reference: {observation['name_id']}")

    # Check location reference
    if observation.get("location_id") and observation["location_id"] not in locations:
        issues.append(f"Invalid location_id reference: {observation['location_id']}")

    # Verify image counts match
    actual_images = len(images_by_obs.get(obs_id, set()))
    if actual_images != observation["image_count"]:
        issues.append(f"Image count mismatch: stored={observation['image_count']}, actual={actual_images}")

    return issues

def clean_text(text: Optional[str]) -> Optional[str]:
    """Clean text fields by removing excess whitespace and normalizing newlines."""
    if not text or text == "NULL":
        return None
    # Replace multiple newlines with single newline
    text = re.sub(r'\n\s*\n', '\n', text.strip())
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up textile/markdown links
    text = re.sub(r'"([^"]+)":([^\s]+)', r'\1 (\2)', text)
    return text

def extract_references(text: Optional[str]) -> List[str]:
    """Extract URLs from text."""
    if not text:
        return []
    # Match both HTML and textile style links
    url_pattern = r'(?:href="([^"]+)"|"[^"]+":(\S+))'
    urls = re.findall(url_pattern, text)
    # Flatten and clean the matches
    return [url for match in urls for url in match if url]

def process_taxonomy(taxonomy: List[Dict[str, Any]], species_data: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Process taxonomy data and merge with species data."""
    # Create taxonomy lookup
    taxonomy_lookup = {
        safe_cast(tax["name_id"], int): {
            "taxonomy": {
                "domain": tax.get("domain", "").strip() or None,
                "kingdom": tax.get("kingdom", "").strip() or None,
                "phylum": tax.get("phylum", "").strip() or None,
                "class": tax.get("class", "").strip() or None,
                "order": tax.get("order", "").strip() or None,
                "family": tax.get("family", "").strip() or None
            },
            "taxonomic_status": get_taxonomic_status(tax)
        }
        for tax in taxonomy
    }

    # Merge taxonomy into species data
    return {
        species_id: {
            **species_data,
            **(taxonomy_lookup.get(species_id, {
                "taxonomy": {},
                "taxonomic_status": "unknown"
            }))
        }
        for species_id, species_data in species_data.items()
    }

def get_taxonomic_status(tax: Dict[str, str]) -> str:
    """Determine taxonomic status based on completeness of classification."""
    required_ranks = ["kingdom", "phylum", "class", "order", "family"]

    # Check if all required ranks are present
    has_all_ranks = all(
        tax.get(rank, "").strip()
        for rank in required_ranks
    )

    # Check if some ranks are present
    has_some_ranks = any(
        tax.get(rank, "").strip()
        for rank in required_ranks
    )

    if has_all_ranks:
        return "complete"
    elif has_some_ranks:
        return "partial"
    else:
        return "unclassified"

def validate_taxonomy(taxonomy: Dict[str, Optional[str]]) -> List[str]:
    """Validate taxonomy hierarchy and return any inconsistencies."""
    errors = []
    ranks = ["domain", "kingdom", "phylum", "class", "order", "family"]

    # Check if all required ranks are present
    has_all_ranks = all(
        taxonomy.get(rank, "").strip()
        for rank in ranks
    )

    # Check if some ranks are present
    has_some_ranks = any(
        taxonomy.get(rank, "").strip()
        for rank in ranks
    )

    if not has_all_ranks:
        errors.append("Missing required taxonomic ranks")

    if not has_some_ranks:
        errors.append("Missing some taxonomic ranks")

    return errors

class License(Enum):
    """Image license types."""
    CC_WIKI_V3 = "Creative Commons Wikipedia Compatible v3.0"
    CC_BY = "Creative Commons Attribution"
    CC_BY_SA = "Creative Commons Attribution-ShareAlike"
    PUBLIC_DOMAIN = "Public Domain"
    UNKNOWN = "Unknown"

@dataclass
class ImageMetadata:
    """Metadata for an image."""
    _id: int
    content_type: str
    copyright_holder: str
    license: License
    ok_for_export: bool = False
    diagnostic: bool = False

def process_images(images: List[Dict[str, Any]], images_by_obs: Dict[int, List[int]]) -> Dict[int, Dict[str, Any]]:
    """Process images and merge with species data."""
    return {
        int(img["id"]): {
            "_id": int(img["id"]),
            "content_type": img.get("content_type", "").lower(),
            "copyright_holder": img.get("copyright_holder", ""),
            "license": parse_license(img.get("license", "")).value,
            "ok_for_export": bool(int(img.get("ok_for_export", 0))),
            "diagnostic": bool(int(img.get("diagnostic", 0)))
        }
        for img in images
    }

def parse_license(license_text: str) -> License:
    """Convert license text to standardized enum."""
    license_map = {
        "Creative Commons Wikipedia Compatible v3.0": License.CC_WIKI_V3,
        "Creative Commons Attribution": License.CC_BY,
        "Creative Commons Attribution-ShareAlike": License.CC_BY_SA,
        "Public Domain": License.PUBLIC_DOMAIN
    }
    return license_map.get(license_text, License.UNKNOWN)

def validate_image_metadata(metadata: ImageMetadata) -> List[str]:
    """Validate image metadata and return any issues."""
    issues = []

    # Validate content type
    if not metadata.content_type.startswith(('image/', 'video/')):
        issues.append(f"Invalid content type: {metadata.content_type}")

    # Validate copyright holder
    if not metadata.copyright_holder or metadata.copyright_holder.isspace():
        issues.append("Missing copyright holder")

    # Validate license
    if metadata.license == License.UNKNOWN:
        issues.append("Unknown or invalid license")

    return issues

@dataclass
class BoundingBox:
    """Geographic bounding box with elevation data."""
    north: float
    south: float
    east: float
    west: float
    high: Optional[float] = None
    low: Optional[float] = None

    @property
    def center(self) -> Tuple[float, float]:
        """Calculate the center point of the bounding box."""
        return (
            (self.north + self.south) / 2,
            (self.east + self.west) / 2
        )

    @property
    def dimensions(self) -> Tuple[float, float]:
        """Calculate the height and width in degrees."""
        return (
            abs(self.north - self.south),
            abs(self.east - self.west)
        )

    @property
    def elevation_range(self) -> Optional[Tuple[float, float]]:
        """Get the elevation range if available."""
        if self.high is not None and self.low is not None:
            return (self.low, self.high)
        return None

def process_locations(locations: List[Dict[str, Any]],
                     location_descriptions: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Process locations and their descriptions."""
    return {
        int(loc["id"]): {
            "_id": int(loc["id"]),
            "name": loc["name"],
            "bbox": BoundingBox(
                north=float(loc["north"]),
                south=float(loc["south"]),
                east=float(loc["east"]),
                west=float(loc["west"]),
                high=safe_cast(loc["high"], float),
                low=safe_cast(loc["low"], float)
            ),
            "location_type": determine_location_type(loc["name"]),
            "parsed_location": parse_location_hierarchy(loc["name"])
        }
        for loc in locations
    }

def determine_location_type(name: str) -> str:
    """Determine the type of location based on name patterns."""
    lower_name = name.lower()
    if any(park in lower_name for park in ["national park", "state park", "regional park"]):
        return "park"
    elif any(forest in lower_name for forest in ["national forest", "state forest"]):
        return "forest"
    elif any(marker in lower_name for marker in ["co.", "county"]):
        return "county"
    elif ", usa" in lower_name:
        return "city"
    elif any(country in lower_name for country in [", canada", ", usa", ", mexico"]):
        return "country"
    return "unknown"

def parse_location_hierarchy(name: str) -> Dict[str, str]:
    """Parse location name into hierarchical components."""
    parts = [p.strip() for p in name.split(",")]
    hierarchy = {}

    if len(parts) >= 1:
        hierarchy["place"] = parts[0]

    for part in parts[1:]:
        part = part.strip()
        if "co." in part.lower() or "county" in part.lower():
            hierarchy["county"] = part
        elif part.strip().lower() in ["usa", "canada", "mexico"]:
            hierarchy["country"] = part
        elif len(part.split()) <= 2:  # Likely a state/province
            hierarchy["state"] = part

    return hierarchy

# MongoDB operations
def get_mongodb_client(config: Dict[str, Any]) -> MongoClient:
    """Create MongoDB client connection."""
    try:
        return MongoClient(config["database"]["uri"])
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        raise

def convert_dates_recursive(obj: Any) -> Any:
    """Recursively convert date objects to datetime for MongoDB compatibility."""
    if isinstance(obj, date):
        return datetime.combine(obj, datetime.min.time())
    elif isinstance(obj, dict):
        return {key: convert_dates_recursive(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates_recursive(item) for item in obj]
    elif isinstance(obj, set):
        return {convert_dates_recursive(item) for item in obj}
    return obj

def convert_sets_recursive(obj: Any) -> Any:
    """Recursively convert sets to lists for MongoDB compatibility."""
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        return {key: convert_sets_recursive(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_sets_recursive(item) for item in obj]
    return obj

def batch_upsert(collection: Collection, items: List[Any], batch_size: int = 1000) -> None:
    """Batch upsert items into MongoDB collection."""
    try:
        operations = []
        for item in items:
            # Convert dataclass instances to dictionaries
            if hasattr(item, '__dataclass_fields__'):
                item_dict = asdict(item)
            elif hasattr(item, '__dict__'):
                item_dict = item.__dict__
            else:
                item_dict = item

            # Create update operation
            operations.append(UpdateOne(
                {"_id": item_dict.get("_id", item_dict.get("id"))},
                {"$set": item_dict},
                upsert=True
            ))

            # Execute batch when reaching batch size
            if len(operations) >= batch_size:
                collection.bulk_write(operations, ordered=False)
                operations = []

        # Execute remaining operations
        if operations:
            collection.bulk_write(operations, ordered=False)

    except Exception as e:
        logging.error(f"Unexpected error during batch upsert: {e}")
        raise

def validate_data_types(data: Dict[str, Any], schema: Schema) -> bool:
    """Validate data types against schema."""
    return all(
        isinstance(data.get(field), type_)
        for field, type_ in schema.items()
        if field in data
    )

def load_config(config_path: Path) -> Dict[str, Any]:
    """Load and merge configuration with defaults, resolving environment variables."""
    # Load .env file explicitly
    load_dotenv(override=True)

    with config_path.open() as f:
        config = yaml.safe_load(f)

    # Resolve environment variables in database URI
    if "${MONGODB_URI}" in config["database"]["uri"]:
        mongodb_uri = os.getenv("MONGODB_URI")
        logging.info("Looking for MONGODB_URI in environment variables")
        if not mongodb_uri:
            logging.error("MONGODB_URI environment variable not found")
            logging.error(f"Current environment variables: {list(os.environ.keys())}")
            logging.error(f"Current working directory: {os.getcwd()}")
            raise ValueError("MONGODB_URI environment variable not set in .env file")
        logging.info("Found MONGODB_URI in environment variables")
        config["database"]["uri"] = mongodb_uri

    return config

def setup_logging(config_path: Path) -> None:
    """Set up logging configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            log_config = yaml.safe_load(f)
            logging.config.dictConfig(log_config)
    except Exception as e:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        logging.warning(f"Failed to load logging config: {e}. Using basic config.")

def load_all_data(config: Dict[str, Any], required_files: List[str]) -> Optional[Dict[str, List[Dict[str, Any]]]]:
    """Load all required data files."""
    data = {}

    for file_name in required_files:
        if file_name not in config["files"]:
            logging.error(f"Missing configuration for required file: {file_name}")
            return None

        try:
            file_path = Path(config["files"][file_name]["input"])
            if not file_path.exists():
                logging.error(f"Required file not found: {file_path}")
                return None

            file_data = load_csv_data(file_path, SCHEMAS.get(file_name))
            if not file_data:
                logging.error(f"No data loaded from {file_name}")
                return None
            data[file_name] = file_data
            logging.info(f"Loaded {len(file_data)} records from {file_name}")
        except Exception as e:
            logging.error(f"Error loading {file_name}: {str(e)}")
            return None

    return data

def process_image_observations(image_observations: List[Dict[str, Any]]) -> Dict[int, List[int]]:
    """Process image-observation relationships."""
    images_by_obs = defaultdict(list)
    for rel in image_observations:
        obs_id = int(rel["observation_id"])
        img_id = int(rel["image_id"])
        images_by_obs[obs_id].append(img_id)
    return dict(images_by_obs)

def process_data_pipeline(data: DataDict) -> Tuple[Dict[int, Dict[str, Any]], Dict[int, Dict[str, Any]]]:
    """Main data processing pipeline."""
    try:
        # Process observations and get image mappings
        obs_by_name, images_by_obs = process_observations(
            data["observations"],
            data["images_observations"]
        )

        # Handle missing name_classifications
        name_classifications = data.get("name_classifications", [])

        # Build species dictionary through pipeline
        species_dict = pipe(
            data["names"],
            process_names,
            lambda d: process_taxonomy(name_classifications, d),
            lambda d: process_name_descriptions(data["name_descriptions"], d),
            lambda d: {
                name_id: {
                    **species_data,
                    "_id": name_id,
                    "observations": obs_by_name.get(name_id, [])
                }
                for name_id, species_data in d.items()
            },
            lambda d: process_images(data["images"], images_by_obs)
        )

        # Process locations separately
        locations_dict = process_locations(
            data["locations"],
            data["location_descriptions"]
        )

        return species_dict, locations_dict

    except Exception as e:
        logger.error(f"Error in data pipeline: {str(e)}")
        raise

def main(config_path: Path = Path("config.yaml")) -> None:
    """Main pipeline execution."""
    try:
        config = load_config(config_path)
        setup_logging(Path("logging.yaml"))

        # Create required directories
        for directory in config["directories"].values():
            Path(directory).mkdir(parents=True, exist_ok=True)

        required_files = [
            "names", "observations", "locations", "images",
            "taxonomy", "images_observations", "location_descriptions",
            "name_descriptions"
        ]

        # Optional files
        optional_files = ["name_classifications"]

        data = load_all_data(config, required_files)
        if not data:
            return

        # Load optional files
        for file_name in optional_files:
            if file_name in config["files"]:
                try:
                    file_path = Path(config["files"][file_name]["input"])
                    if file_path.exists():
                        data[file_name] = load_csv_data(file_path, SCHEMAS.get(file_name))
                        logging.info(f"Loaded optional file {file_name}")
                    else:
                        data[file_name] = []
                        logging.warning(f"Optional file not found: {file_path}")
                except Exception as e:
                    logging.warning(f"Error loading optional file {file_name}: {str(e)}")
                    data[file_name] = []

        # Update process_data_pipeline to handle missing name_classifications
        species_dict, locations_dict = process_data_pipeline(data)

        # Database operations
        client = get_mongodb_client(config)
        db = client[config["database"]["name"]]

        batch_upsert(db.species, list(species_dict.values()))
        batch_upsert(db.locations, list(locations_dict.values()))

        logging.info("Data migration complete!")

    except Exception as e:
        logging.exception(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    load_dotenv()
    print(f"MONGODB_URI present: {'MONGODB_URI' in os.environ}")
    main()

