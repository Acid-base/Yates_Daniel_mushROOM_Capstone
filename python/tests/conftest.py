"""Shared pytest fixtures."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from motor.motor_asyncio import AsyncIOMotorClient
from config import DataConfig
from database import AsyncDatabase


@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary data directory for tests."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def config(test_data_dir):
    """Create test configuration."""
    return DataConfig(
        MONGODB_URI="mongodb://test:27017",
        DATABASE_NAME="test_db",
        DATA_DIR=test_data_dir,
        BATCH_SIZE=100,
        MAX_RETRIES=3,
        RETRY_DELAY=1,
        CHUNK_SIZE=1024,
    )


@pytest.fixture
def mock_motor_client():
    """Create mock MongoDB motor client."""
    client = AsyncMock(spec=AsyncIOMotorClient)
    client.admin.command = AsyncMock()
    return client


@pytest.fixture
async def database(config, mock_motor_client):
    """Create database instance with mock client."""
    with patch(
        "motor.motor_asyncio.AsyncIOMotorClient", return_value=mock_motor_client
    ):
        db = AsyncDatabase(config)
        await db.connect()
        yield db
        await db.close()


@pytest.fixture
def sample_observation():
    """Create a sample observation record."""
    return {
        "_id": 1,
        "name_id": 100,
        "when": "2023-01-01",
        "location_id": 200,
        "lat": 45.0,
        "lng": -122.5,
        "alt": 100,
        "vote_cache": 4.5,
        "is_collection_location": True,
    }


@pytest.fixture
def sample_name():
    """Create a sample name record."""
    return {
        "_id": 100,
        "text_name": "Agaricus campestris",
        "author": "L.",
        "deprecated": False,
        "synonym_id": None,
        "rank": 4,
    }


@pytest.fixture
def sample_location():
    """Create a sample location record."""
    return {
        "_id": 200,
        "name": "Forest Park, Portland, Oregon, USA",
        "north": 45.6,
        "south": 45.5,
        "east": -122.7,
        "west": -122.8,
        "high": 1000,
        "low": 0,
    }


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    return Mock(info=Mock(), error=Mock(), warning=Mock(), debug=Mock())
