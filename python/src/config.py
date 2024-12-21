"""Configuration management using Pydantic."""

from pathlib import Path
from typing import Dict, Any, Tuple, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml
from src.exceptions import ConfigurationError


class MODataSource:
    """Mushroom Observer data source URLs."""

    BASE_URL = "https://mushroomobserver.org"

    def __init__(self):
        """
        Initialize the MODataSource class with URLs for various data sources.

        This method sets up the URLs for different datasets available from the Mushroom Observer website.
        Each URL corresponds to a specific CSV file containing relevant data.

        - Core Data:
            - OBSERVATIONS: URL for the observations dataset.
            - NAMES: URL for the names dataset.
            - LOCATIONS: URL for the locations dataset.
            - IMAGES: URL for the images dataset.
        - Relationships:
            - IMAGES_OBSERVATIONS: URL for the dataset linking images to observations.

        - Taxonomic Data:
            - NAME_CLASSIFICATIONS: URL for the dataset containing taxonomic classifications of names.
            - NAME_DESCRIPTIONS: URL for the dataset containing descriptions of names.
        - Location Data:
            - LOCATION_DESCRIPTIONS: URL for the dataset containing descriptions of locations.
        """
        self.OBSERVATIONS = f"{self.BASE_URL}/observations.csv"
        self.NAMES = f"{self.BASE_URL}/names.csv"
        self.LOCATIONS = f"{self.BASE_URL}/locations.csv"
        self.IMAGES = f"{self.BASE_URL}/images.csv"

        # Relationships
        self.IMAGES_OBSERVATIONS = f"{self.BASE_URL}/images_observations.csv"

        # Taxonomic data
        self.NAME_CLASSIFICATIONS = f"{self.BASE_URL}/name_classifications.csv"
        self.NAME_DESCRIPTIONS = f"{self.BASE_URL}/name_descriptions.csv"

        # Location data
        self.LOCATION_DESCRIPTIONS = f"{self.BASE_URL}/location_descriptions.csv"


class DataConfig(BaseSettings):
    """Main configuration settings."""

    # Database settings
    MONGODB_URI: str = Field(
        ..., env="MONGODB_URI", description="MongoDB connection string"
    )
    DATABASE_NAME: str = Field("mushroom_db")
    BATCH_SIZE: int = Field(
        1000, ge=1, description="Batch size for database operations"
    )

    # File settings
    DEFAULT_DELIMITER: str = Field("\t", description="Default delimiter for CSV files")
    NULL_VALUES: Tuple[str, ...] = Field(
        ("NULL",), description="Values to be treated as null"
    )
    DATE_FORMAT: str = Field("%Y-%m-%d", description="Date format for parsing dates")
    LOG_CONFIG_PATH: Path = Field(
        Path("logging.yaml"), description="Path to the logging configuration file"
    )
    DATA_DIR: Path = Field(Path("data"), description="Path to the data directory")

    # Processing settings
    MAX_RETRIES: int = Field(
        3, description="Maximum number of retries for failed operations"
    )
    RETRY_DELAY: int = Field(
        5, description="Delay in seconds before retrying an operation"
    )  # seconds
    CHUNK_SIZE: int = Field(
        8192, description="Chunk size in bytes for file downloads"
    )  # bytes for file download

    # MongoDB indexes
    INDEXES: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=lambda: {
            "observations": [
                {"keys": [("name_id", 1)]},
                {"keys": [("location_id", 1)]},
                {"keys": [("user_id", 1)]},
                {"keys": [("when", 1)]},
                {"keys": [("lat", 1), ("lng", 1)]},
            ],
            "names": [
                {"keys": [("text_name", 1)], "unique": True},
                {"keys": [("synonym_id", 1)]},
                {"keys": [("rank", 1)]},
            ],
            "images_observations": [
                {"keys": [("observation_id", 1)]},
                {"keys": [("image_id", 1)]},
            ],
            "locations": [
                {"keys": [("name", 1)]},
                {"keys": [("north", 1), ("south", 1), ("east", 1), ("west", 1)]},
            ],
            "images": [
                {"keys": [("content_type", 1)]},
                {"keys": [("created_at", 1)]},
            ],
            "name_classifications": [
                {"keys": [("name_id", 1)]},
                {
                    "keys": [
                        ("kingdom", 1),
                        ("phylum", 1),
                        ("class", 1),
                        ("order", 1),
                        ("family", 1),
                    ]
                },
            ],
            "name_descriptions": [
                {"keys": [("name_id", 1)]},
                {"keys": [("source_type", 1)]},
            ],
            "location_descriptions": [
                {"keys": [("location_id", 1)]},
                {"keys": [("source_type", 1)]},
            ],
        },
        description="MongoDB indexes for collections",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # Allow extra fields in MongoDB URI
    )

    @field_validator("BATCH_SIZE")
    def validate_batch_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Batch size must be positive")
        return v

    @field_validator("DATA_DIR")
    def validate_data_dir(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v


def load_yaml_config(path: Path) -> Dict[str, Any]:
    """Load YAML configuration file."""
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise ConfigurationError(f"Failed to load config from {path}: {e}")
