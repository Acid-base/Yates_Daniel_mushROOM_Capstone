"""Integration tests for the data pipeline."""

import pytest
import asyncio
from src.data_pipeline import DataPipeline
from src.config import DataConfig
from src.downloader import MODownloader


@pytest.fixture
async def config():
    """Test configuration with downloaded data."""
    config = DataConfig()

    # Download real data
    async with MODownloader(config) as downloader:
        await downloader.download_data_files()

    return config


@pytest.mark.asyncio
async def test_pipeline_with_real_data(config):
    """Test pipeline with real Mushroom Observer data."""
    pipeline = DataPipeline(config)

    try:
        await pipeline.initialize()
        await pipeline.run()

        # Verify results
        stats = await pipeline.get_processing_stats()
        assert stats["processed"]["names"] > 0
        assert stats["processed"]["observations"] > 0
        assert stats["processed"]["locations"] > 0

        # Check for some known species
        db = pipeline.db
        amanita = await db.get_collection("names").find_one(
            {"text_name": {"$regex": "^Amanita"}}
        )
        assert amanita is not None

    finally:
        await pipeline.cleanup()


if __name__ == "__main__":
    asyncio.run(test_pipeline_with_real_data(DataConfig()))
