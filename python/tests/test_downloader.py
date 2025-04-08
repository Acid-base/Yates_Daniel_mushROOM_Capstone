"""Tests for data downloading functionality."""

import pytest
from unittest.mock import AsyncMock, patch
import aiohttp
from pathlib import Path

from downloader import MODownloader, download_mo_data
from config import DataConfig
from exceptions import FileProcessingError


@pytest.fixture
def downloader_config(test_data_dir):
    """Create test configuration."""
    return DataConfig(
        MONGODB_URI="mongodb://test:27017",
        DATABASE_NAME="test_db",
        DATA_DIR=test_data_dir,
        BATCH_SIZE=100,
        MAX_RETRIES=2,
        RETRY_DELAY=0.1,
        CHUNK_SIZE=1024,
        DOWNLOAD_TIMEOUT=30,
    )


@pytest.fixture
def mock_response():
    """Create mock aiohttp response."""
    response = AsyncMock()
    response.status = 200
    response.content = AsyncMock()
    response.content.iter_chunked = AsyncMock(return_value=[b"test data"])
    return response


@pytest.fixture
def mock_session(mock_response):
    """Create mock aiohttp session."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    session.get = AsyncMock(return_value=mock_response)
    return session


@pytest.fixture
async def downloader(downloader_config):
    """Create downloader instance."""
    return MODownloader(downloader_config)


@pytest.mark.asyncio
async def test_download_file(downloader, mock_session, test_data_dir):
    """Test downloading a single file."""
    test_url = "https://mushroomobserver.org/observations.csv"
    output_path = test_data_dir / "test.csv"

    async with downloader:
        downloader.session = mock_session
        result = await downloader.download_file(test_url, output_path)

    assert result is True
    assert output_path.exists()
    mock_session.get.assert_called_once_with(test_url)


@pytest.mark.asyncio
async def test_download_file_exists(downloader, mock_session, test_data_dir):
    """Test skipping download when file exists."""
    output_path = test_data_dir / "existing.csv"
    output_path.write_text("existing data")

    async with downloader:
        downloader.session = mock_session
        result = await downloader.download_file(
            "https://example.com/test.csv", output_path
        )

    assert result is False
    mock_session.get.assert_not_called()


@pytest.mark.asyncio
async def test_download_file_error(downloader, mock_session):
    """Test handling download errors."""
    mock_session.get = AsyncMock(side_effect=aiohttp.ClientError("Download failed"))

    async with downloader:
        downloader.session = mock_session
        with pytest.raises(FileProcessingError) as exc_info:
            await downloader.download_file(
                "https://example.com/test.csv", Path("test.csv")
            )
        assert "Failed to download" in str(exc_info.value)


@pytest.mark.asyncio
async def test_download_file_bad_status(downloader, mock_session, mock_response):
    """Test handling non-200 status codes."""
    mock_response.status = 404
    mock_session.get = AsyncMock(return_value=mock_response)

    async with downloader:
        downloader.session = mock_session
        with pytest.raises(FileProcessingError) as exc_info:
            await downloader.download_file(
                "https://example.com/test.csv", Path("test.csv")
            )
        assert "Failed to download" in str(exc_info.value)


@pytest.mark.asyncio
async def test_download_all(downloader, mock_session, test_data_dir):
    """Test downloading all data files."""
    async with downloader:
        downloader.session = mock_session
        results = await downloader.download_all()

    assert len(results) > 0
    assert all(isinstance(path, Path) for path in results.values())
    assert mock_session.get.call_count > 0


@pytest.mark.asyncio
async def test_download_all_with_force(downloader, mock_session, test_data_dir):
    """Test force downloading all files."""
    # Create existing files
    for name in ["observations.csv", "names.csv"]:
        (test_data_dir / name).write_text("existing data")

    async with downloader:
        downloader.session = mock_session
        results = await downloader.download_all(force=True)

    assert len(results) > 0
    assert mock_session.get.call_count > 0


@pytest.mark.asyncio
async def test_download_mo_data_function(test_data_dir):
    """Test the download_mo_data convenience function."""
    config = DataConfig(
        MONGODB_URI="mongodb://test:27017",
        DATABASE_NAME="test_db",
        DATA_DIR=test_data_dir,
    )

    with patch("downloader.MODownloader") as MockDownloader:
        mock_downloader = AsyncMock()
        mock_downloader.download_all = AsyncMock(
            return_value={"test": Path("test.csv")}
        )
        MockDownloader.return_value.__aenter__.return_value = mock_downloader

        result = await download_mo_data(config)

        assert result == {"test": Path("test.csv")}
        mock_downloader.download_all.assert_called_once_with(False)


@pytest.mark.asyncio
async def test_retries_on_failure(downloader, mock_session, test_data_dir):
    """Test retry behavior on failed downloads."""
    # First two calls fail, third succeeds
    mock_session.get.side_effect = [
        aiohttp.ClientError("First failure"),
        aiohttp.ClientError("Second failure"),
        AsyncMock(
            status=200,
            content=AsyncMock(iter_chunked=AsyncMock(return_value=[b"success"])),
        ),
    ]

    async with downloader:
        downloader.session = mock_session
        result = await downloader.download_file(
            "https://example.com/test.csv", test_data_dir / "test.csv"
        )

    assert result is True
    assert mock_session.get.call_count == 3


@pytest.mark.asyncio
async def test_timeout_handling(downloader, mock_session, test_data_dir):
    """Test handling of timeout errors."""
    mock_session.get = AsyncMock(side_effect=aiohttp.ClientTimeout("Timeout"))

    async with downloader:
        downloader.session = mock_session
        with pytest.raises(FileProcessingError) as exc_info:
            await downloader.download_file(
                "https://example.com/test.csv", test_data_dir / "test.csv"
            )
        assert "Failed to download" in str(exc_info.value)
