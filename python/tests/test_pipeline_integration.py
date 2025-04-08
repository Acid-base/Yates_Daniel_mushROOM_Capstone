"""Integration tests for the complete data pipeline."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from motor.motor_asyncio import AsyncIOMotorCollection

from data_pipeline import DataPipeline
from config import DataConfig
from exceptions import DataProcessingError


@pytest.fixture
async def pipeline(test_data_dir):
    """Create test pipeline instance."""
    config = DataConfig(
        MONGODB_URI="mongodb://test:27017",
        DATABASE_NAME="test_db",
        DATA_DIR=test_data_dir,
        BATCH_SIZE=100,
    )

    with patch("motor.motor_asyncio.AsyncIOMotorClient") as mock_client:
        pipeline = DataPipeline(config)
        pipeline.db.client = mock_client
        yield pipeline
        await pipeline.close()


@pytest.mark.asyncio
async def test_pipeline_initialization(pipeline):
    """Test pipeline initialization."""
    assert pipeline.config is not None
    assert pipeline.db is not None


@pytest.mark.asyncio
async def test_pipeline_download_data(pipeline, test_data_dir):
    """Test downloading data files."""
    with patch("downloader.MODownloader") as mock_downloader:
        mock_instance = AsyncMock()
        mock_instance.download_all = AsyncMock(
            return_value={
                "observations": test_data_dir / "observations.csv",
                "names": test_data_dir / "names.csv",
            }
        )
        mock_downloader.return_value.__aenter__.return_value = mock_instance

        result = await pipeline.download_data()
        assert isinstance(result, dict)
        assert "observations" in result
        assert "names" in result


@pytest.mark.asyncio
async def test_pipeline_process_csv_data(pipeline, test_data_dir):
    """Test processing CSV data."""
    # Create test CSV files
    obs_path = test_data_dir / "observations.csv"
    names_path = test_data_dir / "names.csv"

    obs_path.write_text("id,name,when\n1,Test Species,2023-01-01")
    names_path.write_text("id,text_name,author\n1,Test Species,Author")

    csv_files = {"observations": obs_path, "names": names_path}

    processed_data = await pipeline.process_csv_data(csv_files)
    assert isinstance(processed_data, dict)
    assert "observations" in processed_data
    assert "names" in processed_data


@pytest.mark.asyncio
async def test_pipeline_process_api_data(pipeline):
    """Test processing API data."""
    with patch("api_mapper.MOApiMapper") as mock_mapper:
        mock_instance = AsyncMock()
        mock_instance.map_endpoints = AsyncMock()
        mock_mapper.return_value.__aenter__.return_value = mock_instance

        await pipeline.process_api_data()
        mock_instance.map_endpoints.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_store_data(pipeline):
    """Test storing processed data."""
    test_data = {
        "observations": [{"_id": 1, "name": "Test"}],
        "names": [{"_id": 1, "text_name": "Test Species"}],
    }

    mock_collection = AsyncMock(spec=AsyncIOMotorCollection)
    pipeline.db.get_collection = Mock(return_value=mock_collection)

    await pipeline.store_data(test_data)
    assert mock_collection.bulk_write.called


@pytest.mark.asyncio
async def test_pipeline_full_run(pipeline, test_data_dir):
    """Test full pipeline execution."""
    # Mock downloader
    with patch("downloader.MODownloader") as mock_downloader:
        mock_dl_instance = AsyncMock()
        mock_dl_instance.download_all = AsyncMock(
            return_value={
                "observations": test_data_dir / "observations.csv",
                "names": test_data_dir / "names.csv",
            }
        )
        mock_downloader.return_value.__aenter__.return_value = mock_dl_instance

        # Mock API mapper
        with patch("api_mapper.MOApiMapper") as mock_mapper:
            mock_api_instance = AsyncMock()
            mock_api_instance.map_endpoints = AsyncMock()
            mock_mapper.return_value.__aenter__.return_value = mock_api_instance

            # Create test files
            (test_data_dir / "observations.csv").write_text(
                "id,name,when\n1,Test Species,2023-01-01"
            )
            (test_data_dir / "names.csv").write_text(
                "id,text_name,author\n1,Test Species,Author"
            )

            # Run pipeline
            await pipeline.run()

            # Verify all steps were called
            mock_dl_instance.download_all.assert_called_once()
            mock_api_instance.map_endpoints.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_error_handling(pipeline):
    """Test pipeline error handling."""
    with patch("downloader.MODownloader") as mock_downloader:
        mock_instance = AsyncMock()
        mock_instance.download_all = AsyncMock(
            side_effect=DataProcessingError("Download failed")
        )
        mock_downloader.return_value.__aenter__.return_value = mock_instance

        with pytest.raises(DataProcessingError):
            await pipeline.download_data()


@pytest.mark.asyncio
async def test_pipeline_progress_tracking(pipeline, test_data_dir):
    """Test pipeline progress tracking."""
    progress_file = test_data_dir / "pipeline_progress.json"

    with patch("downloader.MODownloader") as mock_downloader:
        mock_dl_instance = AsyncMock()
        mock_dl_instance.download_all = AsyncMock(
            return_value={"observations": test_data_dir / "observations.csv"}
        )
        mock_downloader.return_value.__aenter__.return_value = mock_dl_instance

        await pipeline.run()

        assert progress_file.exists()
        progress_content = progress_file.read_text()
        assert "completed" in progress_content.lower()


@pytest.mark.asyncio
async def test_pipeline_cleanup(pipeline, test_data_dir):
    """Test pipeline cleanup operations."""
    # Create test files
    test_files = ["temp1.csv", "temp2.json"]
    for file in test_files:
        (test_data_dir / file).write_text("test data")

    await pipeline.cleanup()

    # Verify temp files are removed
    for file in test_files:
        assert not (test_data_dir / file).exists()


@pytest.mark.asyncio
async def test_pipeline_resume_from_checkpoint(pipeline, test_data_dir):
    """Test pipeline resuming from checkpoint."""
    progress_file = test_data_dir / "pipeline_progress.json"
    progress_file.write_text('{"last_completed": "download_data"}')

    with patch("downloader.MODownloader") as mock_downloader:
        mock_dl_instance = AsyncMock()
        # Download should be skipped due to checkpoint
        mock_dl_instance.download_all = AsyncMock()
        mock_downloader.return_value.__aenter__.return_value = mock_dl_instance

        await pipeline.run(resume=True)

        mock_dl_instance.download_all.assert_not_called()


@pytest.mark.asyncio
async def test_pipeline_validation(pipeline):
    """Test data validation in pipeline."""
    invalid_data = {"observations": [{"_id": "invalid", "name": None}]}

    with pytest.raises(DataProcessingError) as exc_info:
        await pipeline.validate_data(invalid_data)
    assert "Validation failed" in str(exc_info.value)
