"""Configuration management module."""

import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


def resolve_env_placeholders(value: Any) -> Any:
    """
    Resolve environment variable placeholders in a string value.
    E.g., ${MY_VAR} or $MY_VAR will be replaced with the value of MY_VAR environment variable.
    """
    if not isinstance(value, str):
        return value

    # Pattern matches both ${VAR} and $VAR formats
    pattern = r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)"

    def replace_var(match):
        var_name = match.group(1) or match.group(2)
        return os.getenv(var_name, match.group(0))

    return re.sub(pattern, replace_var, value)


def process_config_dict(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a config dictionary, resolving environment variable placeholders recursively.
    """
    processed = {}
    for key, value in config_dict.items():
        if isinstance(value, dict):
            processed[key] = process_config_dict(value)
        elif isinstance(value, list):
            processed[key] = [resolve_env_placeholders(item) for item in value]
        else:
            processed[key] = resolve_env_placeholders(value)
    return processed


class DataConfig(BaseModel):
    """Data processing configuration."""

    DATA_DIR: str = Field(
        default_factory=lambda: os.path.abspath(
            os.getenv("DATA_DIR", str(Path("data").absolute()))
        )
    )
    BATCH_SIZE: int = Field(
        default_factory=lambda: int(os.getenv("BATCH_SIZE", "1000"))
    )
    MAX_RETRIES: int = Field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    RETRY_DELAY: int = Field(default_factory=lambda: int(os.getenv("RETRY_DELAY", "5")))
    CHUNK_SIZE: int = Field(
        default_factory=lambda: int(os.getenv("CHUNK_SIZE", "8192"))
    )
    NULL_VALUES: List[str] = Field(
        default_factory=lambda: os.getenv("NULL_VALUES", "").split(",")
        or ["", "NULL", "null", "NA", "N/A", "n/a", "None", "none"]
    )
    MONGODB_URI: Optional[str] = Field(default_factory=lambda: os.getenv("MONGODB_URI"))
    DATABASE_NAME: Optional[str] = Field(
        default_factory=lambda: os.getenv("DATABASE_NAME", "mushroom_db")
    )

    @validator("DATA_DIR")
    def validate_data_dir(cls, v):
        """Validate and create data directory if it doesn't exist."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path.absolute())


def load_config(config_path: Optional[Path] = None) -> DataConfig:
    """Load configuration from environment variables with defaults.

    Args:
        config_path: Optional path to a YAML config file to load settings from

    Returns:
        DataConfig: Configuration object with loaded settings

    Raises:
        ValueError: If there is an error loading the configuration
    """
    try:
        config = DataConfig()
        # Convert to dict for processing
        config_dict = config.model_dump()
        # Process the dictionary
        processed_dict = process_config_dict(config_dict)
        # Create new config from processed dict
        return DataConfig(**processed_dict)
    except Exception as e:
        raise ValueError(f"Error loading configuration: {e}")
