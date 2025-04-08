"""Tests for API mapping functionality."""

import pytest
from unittest.mock import AsyncMock, patch
import aiohttp
import json
from src.api_mapper import MOApiMapper
from config import DataConfig
from exceptions import DataProcessingError


@pytest.fixture
def api_config(test_data_dir):
    """Create test configuration."""
    return DataConfig(
        MONGODB_URI="mongodb://test:27017",
        DATABASE_NAME="test_db",
        DATA_DIR=test_data_dir,
        BATCH_SIZE=100,
        MAX_RETRIES=2,
        RETRY_DELAY=0.1,
    )


@pytest.fixture
def mock_session():
    """Create mock aiohttp session."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    return session


@pytest.fixture
async def api_mapper(api_config, test_data_dir):
    """Create API mapper instance."""
    output_dir = test_data_dir / "api_responses"
    mapper = MOApiMapper(api_config, output_dir)
    async with mapper:  # This will create and close the session automatically
        yield mapper


@pytest.mark.asyncio
async def test_discover_ids(api_mapper, mock_session):
    """Test ID discovery functionality."""
    mock_responses = {
        "observations": {"results": [1, 2, 3, 4, 5]},
        "images": {"results": [10, 11]},
        "names": {"results": [100, 101, 102, 103, 104]},
        "locations": {"results": [200, 201, 202, 203, 204]},
    }

    async def mock_make_request(endpoint: str, params: dict):
        return mock_responses.get(endpoint, {"results": []})

    with patch.object(api_mapper, "_make_request", side_effect=mock_make_request):
        await api_mapper.discover_ids()

        assert len(api_mapper.example_ids["observations"]) == 5
        assert len(api_mapper.example_ids["names"]) == 5
        assert len(api_mapper.example_ids["locations"]) == 5


@pytest.mark.asyncio
async def test_make_request_with_rate_limit(api_mapper, mock_session):
    """Test rate limiting in request handling."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"test": "data"})

    mock_session.get = AsyncMock(return_value=mock_response)
    api_mapper.session = mock_session

    # Make multiple requests to test rate limiting
    results = []
    for _ in range(3):
        result = await api_mapper._make_request("test", {})
        results.append(result)

    assert len(results) == 3
    assert all(r == {"test": "data"} for r in results)

    # Check that delays were enforced
    assert mock_session.get.call_count == 3


@pytest.mark.asyncio
async def test_request_error_handling(api_mapper, mock_session):
    """Test error handling in requests."""
    mock_response = AsyncMock()
    mock_response.status = 404
    mock_response.text = AsyncMock(return_value="Not found")

    mock_session.get = AsyncMock(return_value=mock_response)
    api_mapper.session = mock_session

    with pytest.raises(DataProcessingError) as exc_info:
        await api_mapper._make_request("test", {})
    assert "API request failed: 404" in str(exc_info.value)


@pytest.mark.asyncio
async def test_map_endpoints(api_mapper):
    """Test mapping of all endpoints."""
    mock_responses = {
        "observations": {"results": [{"id": 1}]},
        "names": {"results": [{"id": 100}]},
        "locations": {"results": [{"id": 200}]},
        "images": {"results": [{"id": 300}]},
        "sequences": {"results": [{"id": 400}]},
        "external_links": {"results": [{"id": 500}]},
    }

    async def mock_make_request(endpoint: str, params: dict):
        return mock_responses.get(endpoint, {"results": []})

    with patch.object(api_mapper, "_make_request", side_effect=mock_make_request):
        await api_mapper.map_endpoints()

        # Verify that response files were created
        assert (api_mapper.output_dir / "names_help.json").exists()
        assert (api_mapper.output_dir / "observations_help.json").exists()
        assert (api_mapper.output_dir / "locations_help.json").exists()


@pytest.mark.asyncio
async def test_test_endpoint(api_mapper, mock_session):
    """Test endpoint testing functionality."""
    test_response = {"results": [{"id": 1, "name": "test"}]}
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=test_response)

    mock_session.get = AsyncMock(return_value=mock_response)
    api_mapper.session = mock_session

    result = await api_mapper.test_endpoint(
        "test_endpoint", {"param": "value"}, "test_output"
    )

    assert result == test_response
    assert (api_mapper.output_dir / "test_output.json").exists()


@pytest.mark.asyncio
async def test_connection_error(api_mapper, mock_session):
    """Test handling of connection errors."""
    mock_session.get = AsyncMock(side_effect=aiohttp.ClientError("Connection failed"))
    api_mapper.session = mock_session

    with pytest.raises(DataProcessingError) as exc_info:
        await api_mapper._make_request("test", {})
    assert "API request failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_json_parsing_error(api_mapper, mock_session):
    """Test handling of JSON parsing errors."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        side_effect=json.JSONDecodeError("Invalid JSON", "", 0)
    )

    mock_session.get = AsyncMock(return_value=mock_response)
    api_mapper.session = mock_session

    with pytest.raises(DataProcessingError) as exc_info:
        await api_mapper._make_request("test", {})
    assert "API request failed" in str(exc_info.value)
