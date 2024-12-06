"""Configuration management using Pydantic."""

from pathlib import Path
from typing import Dict, Any, Tuple, List
from pydantic import BaseModel, Field, field_validator, AnyHttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml

class MODataSource:
    """Mushroom Observer data source URLs."""
    BASE_URL = "https://mushroomobserver.org"
    
    # Core data
    OBSERVATIONS = f"{BASE_URL}/observations.csv"
    NAMES = f"{BASE_URL}/names.csv"
    LOCATIONS = f"{BASE_URL}/locations.csv"
    IMAGES = f"{BASE_URL}/images.csv"
    
    # Relationships
    IMAGES_OBSERVATIONS = f"{BASE_URL}/images_observations.csv"
    OBSERVATION_HERBARIUM_RECORDS = f"{BASE_URL}/observation_herbarium_records.csv"
    
    # Taxonomic data
    NAME_CLASSIFICATIONS = f"{BASE_URL}/name_classifications.csv"
    NAME_DESCRIPTIONS = f"{BASE_URL}/name_descriptions.csv"
    
    # Location data
    LOCATION_DESCRIPTIONS = f"{BASE_URL}/location_descriptions.csv"
    
    # Herbarium data
    HERBARIUM_RECORDS = f"{BASE_URL}/herbarium_records.csv"
    
    # Voting and naming
    VOTES = f"{BASE_URL}/votes.csv"
    NAMINGS = f"{BASE_URL}/namings.csv"
    NAMING_REASONS = f"{BASE_URL}/naming_reasons.csv"

class DataConfig(BaseSettings):
    """Main configuration settings."""
    # Database settings
    mongodb_uri: str = Field(
        ...,
        env="MONGODB_URI",
        description="MongoDB connection string"
    )
    database_name: str = Field("mushroom_db")
    batch_size: int = Field(1000, ge=1)
    
    # File settings
    default_delimiter: str = Field("\t")
    null_values: Tuple[str, ...] = Field(("NULL",))
    date_format: str = Field("%Y-%m-%d")
    log_config_path: Path = Field(Path("logging.yaml"))
    data_dir: Path = Field(Path("data"))
    download_timeout: int = Field(300)  # 5 minutes timeout for downloads
    
    # Processing settings
    max_retries: int = Field(3)
    retry_delay: int = Field(5)  # seconds
    chunk_size: int = Field(8192)  # bytes for file download
    
    # MongoDB indexes
    indexes: Dict[str, List[Dict[str, Any]]] = Field(default_factory=lambda: {
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
        "namings": [
            {"keys": [("observation_id", 1)]},
            {"keys": [("name_id", 1)]},
        ],
        "votes": [
            {"keys": [("observation_id", 1)]},
            {"keys": [("naming_id", 1)]},
        ],
    })
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"  # Allow extra fields in MongoDB URI
    )

    @field_validator("batch_size")
    def validate_batch_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Batch size must be positive")
        return v

    @field_validator("data_dir")
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

from exceptions import ConfigurationError