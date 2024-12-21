"""Tests for the data pipeline."""

import pytest
from unittest.mock import Mock, AsyncMock

from data_pipeline import DataPipeline
from config import DataConfig
from exceptions import DataProcessingError

# Test data
MOCK_CSV_BATCH = [
    {
        "_id": 387,
        "text_name": "Agaricus xanthodermus",
        "author": "Genev.",
        "rank": "species",
    },
    {
        "_id": 388,
        "text_name": "Agaricus silvicola",
        "author": "Peck",
        "rank": "species",
    },
]

MOCK_API_RESPONSE = {
    "results": [
        {
            "id": 387,
            "type": "name",
            "name": "Agaricus xanthodermus",
            "author": "Genev.",
            "rank": "species",
            "citation": "Bull. Soc. bot. Fr. 23: 28 (1876)",
            "parents": [
                {"name": "Agaricus", "rank": "genus"},
                {"name": "Agaricaceae", "rank": "family"},
            ],
        }
    ]
}


@pytest.fixture
def config():
    """Create test configuration."""
    return DataConfig()


@pytest.fixture
async def pipeline(config):
    """Create test pipeline instance."""
    pipeline = DataPipeline(config)
    yield pipeline
    await pipeline.cleanup()


@pytest.mark.asyncio
async def test_initialize(pipeline):
    """Test pipeline initialization."""
    # Mock database methods
    pipeline.db.connect = AsyncMock()
    pipeline.db.get_collection = Mock()
    pipeline.db.ensure_indexes = AsyncMock()

    await pipeline.initialize()

    # Verify database connection
    pipeline.db.connect.assert_called_once()

    # Verify index creation
    assert pipeline.db.ensure_indexes.call_count > 0


@pytest.mark.asyncio
async def test_process_csv_table(pipeline):
    """Test CSV table processing."""
    table_name = "names"

    # Mock CSV processor
    pipeline.csv_processor.process_file = AsyncMock()
    pipeline.csv_processor.process_file.return_value = [MOCK_CSV_BATCH]

    # Mock database methods
    pipeline.db.get_collection = Mock()
    pipeline.db.batch_upsert = AsyncMock()

    await pipeline._process_csv_table(table_name)

    # Verify data was processed
    pipeline.csv_processor.process_file.assert_called_once_with(table_name)
    pipeline.db.batch_upsert.assert_called_once()

    # Verify IDs were tracked
    assert 387 in pipeline.processed_ids["names"]
    assert 388 in pipeline.processed_ids["names"]


@pytest.mark.asyncio
async def test_process_csv_table_error(pipeline):
    """Test CSV processing error handling."""
    table_name = "names"

    # Mock CSV processor to raise error
    pipeline.csv_processor.process_file = AsyncMock(
        side_effect=Exception("CSV processing failed")
    )

    with pytest.raises(DataProcessingError) as exc:
        await pipeline._process_csv_table(table_name)

    assert "Failed to process names" in str(exc.value)


@pytest.mark.asyncio
async def test_enrich_taxonomic_data(pipeline):
    """Test taxonomic data enrichment."""
    # Add test IDs
    pipeline.processed_ids["names"].add(387)

    # Mock API mapper
    mapper = AsyncMock()
    mapper.test_endpoint = AsyncMock(return_value=MOCK_API_RESPONSE)

    # Mock database methods
    collection_mock = AsyncMock()
    pipeline.db.get_collection = Mock(return_value=collection_mock)

    await pipeline._enrich_taxonomic_data(mapper)

    # Verify API call
    mapper.test_endpoint.assert_called_with(
        "names", {"id": "387", "detail": "high"}, "name_387"
    )

    # Verify database update
    collection_mock.update_one.assert_called_once()
    args = collection_mock.update_one.call_args[0]
    assert args[0] == {"_id": 387}
    assert "api_data" in args[1]["$set"]
    assert "last_api_update" in args[1]["$set"]


@pytest.mark.asyncio
async def test_enrich_external_links(pipeline):
    """Test external links enrichment."""
    # Add test IDs
    pipeline.processed_ids["names"].add(387)

    # Mock API mapper
    mapper = AsyncMock()
    mapper.test_endpoint = AsyncMock(
        return_value={
            "results": [
                {
                    "id": 1,
                    "url": "http://indexfungorum.org/123",
                    "site": "Index Fungorum",
                }
            ]
        }
    )

    # Mock database methods
    collection_mock = AsyncMock()
    pipeline.db.get_collection = Mock(return_value=collection_mock)

    await pipeline._enrich_external_links(mapper)

    # Verify API call
    mapper.test_endpoint.assert_called_with(
        "external_links", {"name_id": "387", "detail": "high"}, "external_links_387"
    )

    # Verify database update
    collection_mock.update_one.assert_called_once()
    args = collection_mock.update_one.call_args[0]
    assert args[0] == {"_id": 387}
    assert "external_links" in args[1]["$set"]
    assert "last_links_update" in args[1]["$set"]


@pytest.mark.asyncio
async def test_enrich_sequence_data(pipeline):
    """Test sequence data enrichment."""
    # Add test IDs
    pipeline.processed_ids["names"].add(387)

    # Mock API mapper
    mapper = AsyncMock()
    mapper.test_endpoint = AsyncMock(
        return_value={
            "results": [
                {"id": 1, "locus": "ITS", "bases": "ATCG...", "accession": "MN123456"}
            ]
        }
    )

    # Mock database methods
    collection_mock = AsyncMock()
    pipeline.db.get_collection = Mock(return_value=collection_mock)

    await pipeline._enrich_sequence_data(mapper)

    # Verify API call
    mapper.test_endpoint.assert_called_with(
        "sequences", {"name_id": "387", "detail": "high"}, "sequences_387"
    )

    # Verify database update
    collection_mock.update_one.assert_called_once()
    args = collection_mock.update_one.call_args[0]
    assert args[0] == {"_id": 387}
    assert "sequences" in args[1]["$set"]
    assert "last_sequence_update" in args[1]["$set"]


@pytest.mark.asyncio
async def test_full_pipeline_integration(pipeline):
    """Test full pipeline integration."""
    # Mock all dependencies
    pipeline.initialize = AsyncMock()
    pipeline.process_csv_data = AsyncMock()
    pipeline.enrich_with_api_data = AsyncMock()
    pipeline.cleanup = AsyncMock()

    # Run main function
    await pipeline.initialize()
    await pipeline.process_csv_data()
    await pipeline.enrich_with_api_data()
    await pipeline.cleanup()

    # Verify all steps were called
    pipeline.initialize.assert_called_once()
    pipeline.process_csv_data.assert_called_once()
    pipeline.enrich_with_api_data.assert_called_once()
    pipeline.cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_error_handling(pipeline):
    """Test pipeline error handling."""
    # Mock process_csv_data to raise error
    pipeline.process_csv_data = AsyncMock(side_effect=Exception("Pipeline failed"))

    # Mock cleanup
    pipeline.cleanup = AsyncMock()

    with pytest.raises(Exception) as exc:
        await pipeline.process_csv_data()

    assert "Pipeline failed" in str(exc.value)

    # Verify cleanup was called
    pipeline.cleanup.assert_not_called()  # Cleanup should be handled by context manager
