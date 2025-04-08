"""Tests for DataConfig and configuration loading."""

import pytest
from pydantic import ValidationError

from src.config import (
    DataConfig,
    load_config,
)  # Replace 'config' with your actual module name
from src.exceptions import ConfigurationError


def test_data_config_default():
    """Test DataConfig with default values."""
    config = DataConfig()
    assert config.MONGODB_URI is None
    assert config.DATABASE_NAME is None
    assert config.BATCH_SIZE is None
    assert config.DEFAULT_DELIMITER is None
    assert config.NULL_VALUES == ("NULL",)  # Default NULL_VALUES


def test_data_config_env_vars(monkeypatch):
    """Test DataConfig loading from environment variables."""
    monkeypatch.setenv("MONGODB_URI", "mongodb://env_test:27017")
    monkeypatch.setenv("DATABASE_NAME", "env_test_db")
    monkeypatch.setenv("BATCH_SIZE", "500")
    monkeypatch.setenv("DEFAULT_DELIMITER", ";")
    monkeypatch.setenv("NULL_VALUES", "None,NaN,")  # Test comma-separated NULL_VALUES

    config = DataConfig()

    assert config.MONGODB_URI == "mongodb://env_test:27017"
    assert config.DATABASE_NAME == "env_test_db"
    assert config.BATCH_SIZE == 500
    assert config.DEFAULT_DELIMITER == ";"
    assert config.NULL_VALUES == ("None", "NaN")  # Parsed NULL_VALUES


def test_data_config_file_override(tmp_path):
    """Test DataConfig loading from file overrides environment variables."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
    MONGODB_URI: "mongodb://file_test:27017"
    DATABASE_NAME: "file_test_db"
    BATCH_SIZE: 250
    DEFAULT_DELIMITER: ","
    NULL_VALUES: "na,missing"
    """
    )
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("MONGODB_URI", "mongodb://env_test:27017")  # Still set env vars
    monkeypatch.setenv("DATABASE_NAME", "env_test_db")
    monkeypatch.setenv("BATCH_SIZE", "500")
    monkeypatch.setattr(
        DataConfig.model_config, "env_file", config_file
    )  # point to test config file

    config = DataConfig()

    assert config.MONGODB_URI == "mongodb://file_test:27017"  # File overrides env
    assert config.DATABASE_NAME == "file_test_db"  # File overrides env
    assert config.BATCH_SIZE == 250  # File overrides env
    assert config.DEFAULT_DELIMITER == ","  # File overrides env
    assert config.NULL_VALUES == ("na", "missing")  # File overrides env


def test_data_config_validation_required_fields(monkeypatch):
    """Test DataConfig validation for required fields."""
    monkeypatch.delenv("MONGODB_URI", raising=False)
    monkeypatch.delenv("DATABASE_NAME", raising=False)
    monkeypatch.delenv("BATCH_SIZE", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        DataConfig()

    errors = exc_info.value.errors(include_url=False)
    assert len(errors) == 3  # MONGODB_URI, DATABASE_NAME, BATCH_SIZE are required
    assert any(
        err["type"] == "value_error" and err["loc"] == ("mongodb_uri",)
        for err in errors
    )
    assert any(
        err["type"] == "value_error" and err["loc"] == ("database_name",)
        for err in errors
    )
    assert any(
        err["type"] == "value_error" and err["loc"] == ("batch_size",) for err in errors
    )


def test_data_config_validation_batch_size_positive(monkeypatch):
    """Test DataConfig validation for positive batch size."""
    monkeypatch.setenv("MONGODB_URI", "test_uri")
    monkeypatch.setenv("DATABASE_NAME", "test_db")
    monkeypatch.setenv("BATCH_SIZE", "-100")  # Invalid negative batch size

    with pytest.raises(ValidationError) as exc_info:
        DataConfig()

    errors = exc_info.value.errors(include_url=False)
    assert len(errors) == 1
    assert errors[0]["type"] == "value_error"
    assert errors[0]["loc"] == ("batch_size",)
    assert "Batch size must be positive" in errors[0]["msg"]


def test_data_config_data_dir_creation(tmp_path):
    """Test DataConfig data directory creation."""
    data_dir = tmp_path / "test_data_dir"
    config = DataConfig(
        DATA_DIR=data_dir,
        MONGODB_URI="test_uri",
        DATABASE_NAME="test_db",
        BATCH_SIZE=100,
    )

    assert config.DATA_DIR.exists()
    assert config.DATA_DIR.is_dir()


def test_load_config_valid_yaml(tmp_path):
    """Test load_config with a valid YAML file."""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(
        """
        setting1: value1
        setting2: 123
        """
    )
    loaded_config = load_config(config_path)
    assert isinstance(loaded_config, dict)
    assert loaded_config["setting1"] == "value1"
    assert loaded_config["setting2"] == 123


def test_load_config_invalid_yaml(tmp_path):
    """Test load_config with an invalid YAML file."""
    config_path = tmp_path / "invalid_config.yaml"
    config_path.write_text("invalid yaml: : :")  # intentionally invalid YAML

    with pytest.raises(ConfigurationError) as exc_info:
        load_config(config_path)

    assert "Failed to load config from" in str(exc_info.value)
    assert "invalid_config.yaml" in str(exc_info.value)


def test_load_config_file_not_found(tmp_path):
    """Test load_config when the config file is not found."""
    config_path = tmp_path / "nonexistent_config.yaml"

    with pytest.raises(ConfigurationError) as exc_info:
        load_config(config_path)

    assert "Failed to load config from" in str(exc_info.value)
    assert "nonexistent_config.yaml" in str(exc_info.value)


def test_data_config_null_values_default():
    """Test DataConfig NULL_VALUES default value."""
    config = DataConfig(MONGODB_URI="test_uri", DATABASE_NAME="test_db", BATCH_SIZE=100)
    assert config.NULL_VALUES == ("NULL",)


def test_data_config_null_values_parsing():
    """Test DataConfig NULL_VALUES parsing from env var."""
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("NULL_VALUES", "None, NaN, na ,  ")  # Spaces and empty values
    config = DataConfig(MONGODB_URI="test_uri", DATABASE_NAME="test_db", BATCH_SIZE=100)
    assert config.NULL_VALUES == ("None", "NaN", "na")  # Spaces and empty removed
