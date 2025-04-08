"""Tests for async database operations."""

import pytest
import asyncio

from src.database import get_database
from config import DataConfig
from exceptions import DatabaseError


@pytest.fixture
def db_config(tmp_path):
    """Create a test database configuration."""
    return DataConfig(
        MONGODB_URI="mongodb://localhost:27017",
        DATABASE_NAME="test_mushroom_db",
        BATCH_SIZE=100,
    )


@pytest.fixture
async def test_db(db_config):
    """Create a test database instance."""
    db = await get_database(db_config)
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_database_connection(db_config):
    """Test database connection."""
    db = None
    try:
        db = await get_database(db_config)
        assert db is not None
        assert db.client is not None
    finally:
        if db:
            await db.close()


@pytest.mark.asyncio
async def test_store_records(test_db):
    """Test storing records in database."""
    test_records = [{"_id": 1, "name": "Test 1"}, {"_id": 2, "name": "Test 2"}]

    stored_count = await test_db.store_records("test_collection", test_records)
    assert stored_count == len(test_records)

    # Verify records were stored
    collection = test_db.get_collection("test_collection")
    count = await collection.count_documents({})
    assert count == len(test_records)


@pytest.mark.asyncio
async def test_batch_process(test_db):
    """Test batch processing with transformations."""
    test_records = [
        {"_id": 1, "value": "test1"},
        {"_id": 2, "value": "test2"},
        {"_id": 3, "value": "skip"},
    ]

    # Test transform and filter functions
    def transform(record):
        record["value"] = record["value"].upper()
        return record

    def filter_func(record):
        return record["value"] != "skip"

    success_count, error_count = await test_db.batch_process(
        "test_collection",
        test_records,
        transform_func=transform,
        filter_func=filter_func,
    )

    assert success_count == 2  # Two records should pass the filter
    assert error_count == 0

    # Verify transformed records
    collection = test_db.get_collection("test_collection")
    records = await collection.find({}).to_list(length=None)
    assert len(records) == 2
    assert all(r["value"].isupper() for r in records)


@pytest.mark.asyncio
async def test_bulk_update_species(test_db):
    """Test bulk updates of species documents."""
    # Insert initial records
    species_docs = [
        {"_id": 1, "name": "Species 1", "count": 0},
        {"_id": 2, "name": "Species 2", "count": 0},
    ]
    await test_db.store_records("species", species_docs)

    # Prepare updates
    updates = [
        {"_id": 1, "count": 1},
        {"_id": 2, "count": 2},
        {"_id": 3, "count": 3},  # Non-existent document
    ]

    success_count, error_count = await test_db.bulk_update_species(updates, upsert=True)
    assert success_count > 0

    # Verify updates
    collection = test_db.get_collection("species")
    updated_docs = await collection.find({}).to_list(length=None)
    assert len(updated_docs) == 3  # Should include upserted document


@pytest.mark.asyncio
async def test_ensure_species_indexes(test_db):
    """Test creation of species collection indexes."""
    await test_db.ensure_species_indexes()

    collection = test_db.get_collection("species")
    indexes = await collection.list_indexes().to_list(length=None)

    # Convert to list of index names for easier assertion
    index_names = [idx["name"] for idx in indexes]

    # Check for required indexes
    assert "scientific_name_1" in index_names
    assert "display_name_1" in index_names
    assert "search_name_1" in index_names
    assert "taxonomic_completeness_-1" in index_names


@pytest.mark.asyncio
async def test_aggregate_related_data(test_db):
    """Test aggregation pipeline execution."""
    # Insert test data
    species_data = [
        {"_id": 1, "genus": "Amanita", "observations": 2},
        {"_id": 2, "genus": "Amanita", "observations": 3},
        {"_id": 3, "genus": "Boletus", "observations": 1},
    ]
    await test_db.store_records("species", species_data)

    # Test aggregation pipeline
    pipeline = [
        {"$group": {"_id": "$genus", "total_observations": {"$sum": "$observations"}}}
    ]

    results = []
    async for doc in test_db.aggregate_related_data("species", pipeline):
        results.append(doc)

    assert len(results) == 2  # Two distinct genera
    amanita_result = next(r for r in results if r["_id"] == "Amanita")
    assert amanita_result["total_observations"] == 5


@pytest.mark.asyncio
async def test_error_handling(test_db):
    """Test error handling in database operations."""
    # Test invalid collection name
    with pytest.raises(DatabaseError):
        await test_db.store_records(None, [])

    # Test invalid record format
    with pytest.raises(Exception):  # Specific exception type may vary
        await test_db.store_records("test_collection", [{"_id": None}])

    # Test invalid pipeline
    with pytest.raises(Exception):
        async for _ in test_db.aggregate_related_data("species", None):
            pass


@pytest.mark.asyncio
async def test_sync_client_fallback(db_config):
    """Test fallback to synchronous client."""
    # Force async client to fail by using invalid URI
    db_config.MONGODB_URI = "invalid_uri"

    with pytest.raises(DatabaseError):
        await get_database(db_config)


@pytest.mark.asyncio
async def test_batch_size_handling(test_db):
    """Test handling of different batch sizes."""
    # Create large number of test records
    large_batch = [{"_id": i, "value": f"test{i}"} for i in range(1000)]

    # Test with different batch sizes
    batch_sizes = [1, 10, 100, 1000]
    for batch_size in batch_sizes:
        await test_db.store_records("test_batch", large_batch, batch_size=batch_size)

        collection = test_db.get_collection("test_batch")
        count = await collection.count_documents({})
        assert count == len(large_batch)

        # Clean up
        await collection.delete_many({})


@pytest.mark.asyncio
async def test_concurrent_operations(test_db):
    """Test concurrent database operations."""

    async def insert_batch(batch_id: int) -> int:
        records = [{"_id": f"{batch_id}-{i}", "batch": batch_id} for i in range(100)]
        return await test_db.store_records("concurrent_test", records)

    # Run multiple operations concurrently
    tasks = [insert_batch(i) for i in range(5)]
    results = await asyncio.gather(*tasks)

    assert all(count == 100 for count in results)

    # Verify total records
    collection = test_db.get_collection("concurrent_test")
    total_count = await collection.count_documents({})
    assert total_count == 500  # 5 batches * 100 records
