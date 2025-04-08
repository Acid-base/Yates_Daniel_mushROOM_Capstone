"""Async database operations module."""

from typing import Any, Dict, List, Optional, Callable, Tuple, AsyncGenerator
import asyncio
import certifi
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import MongoClient, UpdateOne

from exceptions import DatabaseError
from monitoring import measure_performance
from config import DataConfig

logger = logging.getLogger(__name__)


class AsyncDatabase:
    """Async database operations handler."""

    def __init__(self, config: DataConfig):
        self.config = config
        self.client = None
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._use_sync_client = False  # Flag to indicate which client type is in use

    async def connect(self) -> None:
        """Connect to the database and initialize collections."""
        try:
            # First try the AsyncIOMotorClient
            logger.info(
                f"Attempting to connect to MongoDB using AsyncIO driver... URI: {self.config.MONGODB_URI}"
            )
            logger.info(f"Database name: {self.config.DATABASE_NAME}")
            await self._try_async_connect()

            # Initialize database structure
            await self.initialize_database()

        except Exception as async_error:
            logger.warning(
                f"Async connection failed: {type(async_error).__name__} - {str(async_error)}"
            )
            logger.info("Falling back to synchronous driver with async wrapper...")

            try:
                # Fall back to synchronous client wrapped for async usage
                await self._try_sync_connect()
                # Initialize database structure
                await self.initialize_database()
            except Exception as sync_error:
                logger.error(
                    f"Sync connection failed too: {type(sync_error).__name__} - {str(sync_error)}"
                )
                raise DatabaseError(
                    f"All MongoDB connection attempts failed. Last error: {sync_error}"
                )

    async def _try_async_connect(self) -> None:
        """Try connecting with AsyncIOMotorClient."""
        ca_file_path = certifi.where()
        logger.info(f"Using CA file: {ca_file_path}")

        self.client = AsyncIOMotorClient(
            self.config.MONGODB_URI,
            tls=True,
            tlsCAFile=ca_file_path,
            tlsAllowInvalidCertificates=True,  # Added to match VSCode settings
            retryWrites=True,
            serverSelectionTimeoutMS=30000,  # Increased timeout
            connectTimeoutMS=30000,  # Increased timeout
        )

        # Verify connection with ping
        await self.client.admin.command("ping")
        logger.info("Successfully connected using AsyncIOMotorClient")
        self._use_sync_client = False

    async def _try_sync_connect(self) -> None:
        """Try connecting with synchronous MongoClient wrapped for async usage."""
        ca_file_path = certifi.where()
        logger.info(f"Using CA file for sync client: {ca_file_path}")

        # Create a synchronous client
        self._sync_client = MongoClient(
            self.config.MONGODB_URI,
            tls=True,
            tlsCAFile=ca_file_path,
            tlsAllowInvalidCertificates=True,  # Added to match VSCode settings
            retryWrites=True,
            connectTimeoutMS=30000,  # Increased timeout
            serverSelectionTimeoutMS=30000,  # Increased timeout
        )

        # Test the connection
        await asyncio.get_event_loop().run_in_executor(
            self._executor, lambda: self._sync_client.admin.command("ping")
        )

        logger.info(
            "Successfully connected using synchronous MongoClient with async wrapper"
        )
        self._use_sync_client = True
        self.client = self._sync_client  # Use sync client as the primary client

    async def close(self) -> None:
        """Close database connection."""
        if self.client:
            if self._use_sync_client:
                # Close synchronously
                await asyncio.get_event_loop().run_in_executor(
                    self._executor, lambda: self.client.close()
                )
            else:
                # Close async client
                self.client.close()

            logger.info("Closed MongoDB connection")

        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)

    def get_collection(self, name: str) -> Any:
        """Get a collection by name."""
        if not self.client:
            raise DatabaseError("Database not connected")

        return self.client[self.config.DATABASE_NAME][name]

    @measure_performance
    async def batch_upsert(
        self,
        collection: Any,
        items: List[Any],
        batch_size: Optional[int] = None,
    ) -> None:
        """Batch upsert items into collection."""
        if not items:
            return

        batch_size = batch_size or self.config.BATCH_SIZE
        operations = []

        try:
            for item in items:
                # Convert dataclass instances to dictionaries
                item_dict = (
                    asdict(item) if hasattr(item, "__dataclass_fields__") else item
                )

                operations.append(
                    UpdateOne(
                        {"_id": item_dict.get("_id")}, {"$set": item_dict}, upsert=True
                    )
                )

                if len(operations) >= batch_size:
                    if self._use_sync_client:
                        await self._sync_bulk_write(collection, operations)
                    else:
                        await collection.bulk_write(operations, ordered=False)
                    operations = []

            if operations:
                if self._use_sync_client:
                    await self._sync_bulk_write(collection, operations)
                else:
                    await collection.bulk_write(operations, ordered=False)

        except Exception as e:
            raise DatabaseError(f"Batch upsert failed: {e}")

    async def _sync_bulk_write(self, collection, operations):
        """Execute bulk write using synchronous client."""
        await asyncio.get_event_loop().run_in_executor(
            self._executor, lambda: collection.bulk_write(operations, ordered=False)
        )

    @measure_performance
    async def batch_delete(
        self, collection: AsyncIOMotorCollection, filter_query: Dict[str, Any]
    ) -> int:
        """Delete documents matching the filter query."""
        try:
            result = await collection.delete_many(filter_query)
            return result.deleted_count
        except Exception as e:
            raise DatabaseError(f"Batch delete failed: {e}")

    @measure_performance
    async def ensure_indexes(
        self, collection: AsyncIOMotorCollection, indexes: List[Dict[str, Any]]
    ) -> None:
        """Create indexes if they don't exist."""
        try:
            for index in indexes:
                await collection.create_index(**index)
        except Exception as e:
            raise DatabaseError(f"Failed to create indexes: {e}")

    async def store_records(
        self,
        collection_name: str,
        records: List[Dict[str, Any]],
        batch_size: int = 1000,
    ) -> int:
        """Store records in a collection with batching and error handling."""
        if not records:
            return 0

        stored_count = 0
        collection = self.get_collection(collection_name)
        logger.debug(
            f"Got collection {collection_name}, storing {len(records)} records"
        )

        try:
            # Process in batches
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]

                # For names collection, handle duplicates at the record level before creating operations
                if collection_name == "names":
                    # Group records by text_name
                    records_by_text_name = {}
                    for record in batch:
                        text_name = record["text_name"]
                        if text_name not in records_by_text_name:
                            records_by_text_name[text_name] = []
                        records_by_text_name[text_name].append(record)

                    # Apply duplicate handling rules
                    filtered_records = []
                    for text_name, text_records in records_by_text_name.items():
                        # Find existing record
                        existing = await collection.find_one({"text_name": text_name})

                        if not existing:
                            # No existing record
                            if len(text_records) == 1:
                                filtered_records.append(text_records[0])
                            else:
                                # Multiple records with same name
                                non_deprecated = [
                                    r
                                    for r in text_records
                                    if not r.get("deprecated", 0)
                                ]
                                if non_deprecated:
                                    # Keep non-deprecated one with lowest ID
                                    filtered_records.append(
                                        min(
                                            non_deprecated,
                                            key=lambda x: x.get("id", float("inf")),
                                        )
                                    )
                                    # Add all deprecated ones
                                    filtered_records.extend(
                                        r
                                        for r in text_records
                                        if r.get("deprecated", 0)
                                    )
                                else:
                                    # All deprecated, keep all
                                    filtered_records.extend(text_records)
                        else:
                            # Have existing record
                            if not existing.get("deprecated", 0):
                                # Existing record is not deprecated, only keep deprecated new ones
                                filtered_records.extend(
                                    r for r in text_records if r.get("deprecated", 0)
                                )
                            else:
                                # Existing record is deprecated
                                non_deprecated = [
                                    r
                                    for r in text_records
                                    if not r.get("deprecated", 0)
                                ]
                                if non_deprecated:
                                    filtered_records.append(
                                        min(
                                            non_deprecated,
                                            key=lambda x: x.get("id", float("inf")),
                                        )
                                    )
                                filtered_records.extend(
                                    r for r in text_records if r.get("deprecated", 0)
                                )

                    # Use filtered records for this batch
                    batch = filtered_records

                # Create operations from (possibly filtered) batch
                operations = []
                for record in batch:
                    # Look for an ID field in order of preference
                    record_id = (
                        record.get("_id") or record.get("id") or record.get("name_id")
                    )
                    if not record_id:
                        logger.warning(f"Record missing any ID field: {record}")
                        continue

                    # Create a copy of the record with _id set
                    record_copy = record.copy()
                    record_copy["_id"] = record_id

                    operations.append(
                        UpdateOne(
                            {"_id": record_id}, {"$set": record_copy}, upsert=True
                        )
                    )

                if operations:
                    logger.debug(
                        f"Executing {len(operations)} operations on {collection_name}"
                    )
                    if self._use_sync_client:
                        await self._sync_bulk_write(collection, operations)
                    else:
                        await collection.bulk_write(operations, ordered=False)
                    stored_count += len(operations)
                    logger.debug(f"Successfully stored {len(operations)} records")

            logger.info(f"Total records stored in {collection_name}: {stored_count}")
            return stored_count

        except Exception as e:
            logger.error(
                f"Error storing records in {collection_name}: {e}", exc_info=True
            )
            raise DatabaseError(f"Error storing records in {collection_name}: {e}")

    async def update_species_document(
        self, species_id: int, update_data: Dict[str, Any], upsert: bool = True
    ) -> bool:
        """Update a species document with new data.

        Args:
            species_id: ID of the species to update
            update_data: Dictionary containing the data to update
            upsert: Whether to insert if document doesn't exist

        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.get_collection("species")

            if self._use_sync_client:
                await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    lambda: collection.update_one(
                        {"_id": species_id}, {"$set": update_data}, upsert=upsert
                    ),
                )
            else:
                await collection.update_one(
                    {"_id": species_id}, {"$set": update_data}, upsert=upsert
                )

            return True

        except Exception as e:
            logger.error(f"Error updating species {species_id}: {e}")
            return False

    async def store_species_batch(
        self, species_batch: List[Dict[str, Any]], batch_size: int = 1000
    ) -> int:
        """Store a batch of species documents.

        Args:
            species_batch: List of species documents to store
            batch_size: Size of batches for bulk operations

        Returns:
            Number of species documents stored
        """
        try:
            return await self.store_records("species", species_batch, batch_size)
        except Exception as e:
            logger.error(f"Error storing species batch: {e}")
            return 0

    async def batch_process(
        self,
        collection_name: str,
        records: List[Dict[str, Any]],
        transform_func: Optional[Callable] = None,
        filter_func: Optional[Callable] = None,
        batch_size: int = 1000,
    ) -> Tuple[int, int]:
        """Process and store records in batches with optional transformation and filtering.

        Args:
            collection_name: Collection to store records in
            records: List of records to process
            transform_func: Optional function to transform records
            filter_func: Optional function to filter records
            batch_size: Size of batches for bulk operations

        Returns:
            Tuple of (success_count, error_count)
        """
        success_count = 0
        error_count = 0

        try:
            collection = self.get_collection(collection_name)
            current_batch = []

            for record in records:
                try:
                    # Apply transformations if specified
                    if transform_func:
                        record = transform_func(record)

                    # Apply filters if specified
                    if filter_func and not filter_func(record):
                        continue

                    current_batch.append(record)

                    # Process batch when full
                    if len(current_batch) >= batch_size:
                        try:
                            await self.store_records(collection_name, current_batch)
                            success_count += len(current_batch)
                        except Exception as batch_error:
                            logger.error(f"Error processing batch: {batch_error}")
                            error_count += len(current_batch)
                        current_batch = []

                except Exception as record_error:
                    logger.debug(f"Error processing record: {record_error}")
                    error_count += 1

            # Process any remaining records
            if current_batch:
                try:
                    await self.store_records(collection_name, current_batch)
                    success_count += len(current_batch)
                except Exception as batch_error:
                    logger.error(f"Error processing final batch: {batch_error}")
                    error_count += len(current_batch)

            return success_count, error_count

        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return success_count, error_count

    async def aggregate_related_data(
        self,
        collection_name: str,
        pipeline: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute an aggregation pipeline on a collection.

        Args:
            collection_name: Collection to aggregate
            pipeline: MongoDB aggregation pipeline
            options: Optional aggregation options

        Yields:
            Aggregated documents
        """
        try:
            collection = self.get_collection(collection_name)

            if self._use_sync_client:
                # Run sync aggregation in executor
                cursor = await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    lambda: collection.aggregate(pipeline, **(options or {})),
                )
                async for doc in AsyncIterator(cursor):
                    yield doc
            else:
                # Use motor's async aggregation
                async for doc in collection.aggregate(pipeline, **(options or {})):
                    yield doc

        except Exception as e:
            logger.error(f"Aggregation error in {collection_name}: {e}")
            raise DatabaseError(f"Failed to aggregate data: {e}")

    async def bulk_update_species(
        self, updates: List[Dict[str, Any]], upsert: bool = True, ordered: bool = False
    ) -> Tuple[int, int]:
        """Perform bulk updates on species documents.

        Args:
            updates: List of update operations
            upsert: Whether to insert if document doesn't exist
            ordered: Whether to execute updates in order

        Returns:
            Tuple of (success_count, error_count)
        """
        success_count = 0
        error_count = 0

        try:
            collection = self.get_collection("species")
            operations = []

            for update in updates:
                try:
                    species_id = update.get("_id")
                    if not species_id:
                        error_count += 1
                        continue

                    operations.append(
                        UpdateOne({"_id": species_id}, {"$set": update}, upsert=upsert)
                    )
                except Exception as op_error:
                    logger.debug(f"Error creating update operation: {op_error}")
                    error_count += 1

            if operations:
                try:
                    if self._use_sync_client:
                        result = await self._sync_bulk_write(collection, operations)
                    else:
                        result = await collection.bulk_write(
                            operations, ordered=ordered
                        )
                    success_count = len(operations)
                except Exception as bulk_error:
                    logger.error(f"Bulk update error: {bulk_error}")
                    error_count = len(operations)

            return success_count, error_count

        except Exception as e:
            logger.error(f"Species bulk update error: {e}")
            return success_count, error_count

    async def ensure_species_indexes(self) -> None:
        """Create required indexes for species collection."""
        try:
            collection = self.get_collection("species")

            indexes = [
                # Remove unique constraint from text_name
                {"keys": [("scientific_name", 1)], "sparse": True},
                # Add compound index for text_name + deprecated to allow duplicates if deprecated
                {"keys": [("text_name", 1), ("deprecated", 1)], "sparse": True},
                {"keys": [("display_name", 1)], "sparse": True},
                {"keys": [("search_name", 1)], "sparse": True},
                {"keys": [("kingdom", 1)], "sparse": True},
                {"keys": [("phylum", 1)], "sparse": True},
                {"keys": [("class_name", 1)], "sparse": True},
                {"keys": [("order", 1)], "sparse": True},
                {"keys": [("family", 1)], "sparse": True},
                {"keys": [("genus", 1)], "sparse": True},
                {"keys": [("taxonomic_completeness", -1)], "sparse": True},
            ]

            # Drop existing indexes first to avoid conflicts
            await collection.drop_indexes()
            await self.ensure_indexes(collection, indexes)

        except Exception as e:
            logger.error(f"Error creating species indexes: {e}")
            raise DatabaseError(f"Failed to create species indexes: {e}")

    async def ensure_names_indexes(self) -> None:
        """Create required indexes for names collection."""
        try:
            collection = self.get_collection("names")

            # Drop existing indexes to remove the unique constraint
            await collection.drop_indexes()

            # Create new indexes without unique constraint
            indexes = [
                # Compound index to handle duplicates based on deprecated status
                {"keys": [("text_name", 1), ("deprecated", 1)]},
                # Single field indexes for common queries
                {"keys": [("author", 1)]},
                {"keys": [("rank", -1)]},
                {"keys": [("deprecated", 1)]},
                {"keys": [("synonym_id", 1)]},
            ]

            await self.ensure_indexes(collection, indexes)
            logger.info("Successfully created indexes for names collection")

        except Exception as e:
            logger.error(f"Error creating names indexes: {e}")
            raise DatabaseError(f"Failed to create names indexes: {e}")

    async def handle_duplicate_names(
        self, collection, operations: List[UpdateOne]
    ) -> List[UpdateOne]:
        """Handle duplicate name records by applying business rules.

        Rules:
        1. If a name is already in the database:
           - If both records are deprecated=0, keep the one with the lower ID
           - If one record has deprecated=1, keep the non-deprecated one
           - If both are deprecated, keep both with their own IDs
        2. For new records, apply the same rules against each other
        """
        try:
            # Extract record data from UpdateOne operations
            records_by_text_name = {}
            for op in operations:
                # For each operation, we want to group by text_name
                # First get the record ID from the filter criteria
                record_id = op._filter["_id"]
                # Then get the full record from the $set operation
                record = op._update["$set"]

                text_name = record["text_name"]
                if text_name not in records_by_text_name:
                    records_by_text_name[text_name] = []
                records_by_text_name[text_name].append((op, record))

            # Check existing records and apply rules
            filtered_ops = []
            for text_name, op_records in records_by_text_name.items():
                # Find existing record
                existing = await collection.find_one({"text_name": text_name})

                if not existing:
                    # No existing record, process group internally
                    if len(op_records) == 1:
                        filtered_ops.append(
                            op_records[0][0]
                        )  # Keep the single operation
                    else:
                        # Multiple new records with same name
                        non_deprecated = [
                            (op, rec)
                            for op, rec in op_records
                            if not rec.get("deprecated", 0)
                        ]
                        if non_deprecated:
                            # Keep non-deprecated one with lowest ID and all deprecated ones
                            min_id_op = min(
                                non_deprecated,
                                key=lambda x: x[1].get("id", float("inf")),
                            )
                            filtered_ops.append(min_id_op[0])
                            # Add all deprecated ones
                            filtered_ops.extend(
                                op for op, rec in op_records if rec.get("deprecated", 0)
                            )
                        else:
                            # All deprecated, keep all
                            filtered_ops.extend(op for op, _ in op_records)
                else:
                    # Have existing record, apply rules
                    if not existing.get("deprecated", 0):
                        # Existing record is not deprecated
                        filtered_ops.extend(
                            op for op, rec in op_records if rec.get("deprecated", 0)
                        )
                    else:
                        # Existing record is deprecated
                        non_deprecated = [
                            (op, rec)
                            for op, rec in op_records
                            if not rec.get("deprecated", 0)
                        ]
                        if non_deprecated:
                            min_id_op = min(
                                non_deprecated,
                                key=lambda x: x[1].get("id", float("inf")),
                            )
                            filtered_ops.append(min_id_op[0])
                        filtered_ops.extend(
                            op for op, rec in op_records if rec.get("deprecated", 0)
                        )

            return filtered_ops

        except Exception as e:
            logger.error(f"Error handling duplicate names: {e}", exc_info=True)
            raise DatabaseError(f"Failed to handle duplicate names: {e}")

    async def initialize_database(self) -> None:
        """Initialize database with required collections and indexes."""
        try:
            # Create collections with validators and indexes
            logger.info("Initializing database collections and indexes...")

            # Initialize names collection (no unique constraint on text_name)
            await self.ensure_names_indexes()

            # Initialize species collection
            await self.ensure_species_indexes()

            # Initialize other collections with basic indexes
            collections_config = {
                "name_classifications": [
                    {"keys": [("name_id", 1)]},
                    {"keys": [("kingdom", 1)]},
                    {"keys": [("phylum", 1)]},
                    {"keys": [("class", 1)]},
                    {"keys": [("order", 1)]},
                    {"keys": [("family", 1)]},
                ],
                "name_descriptions": [
                    {"keys": [("name_id", 1)]},
                    {"keys": [("source_type", 1)]},
                ],
                "locations": [
                    {"keys": [("name", 1)]},
                    {"keys": [("north", 1)]},
                    {"keys": [("south", 1)]},
                    {"keys": [("east", 1)]},
                    {"keys": [("west", 1)]},
                ],
                "location_descriptions": [
                    {"keys": [("location_id", 1)]},
                    {"keys": [("source_type", 1)]},
                ],
                "observations": [
                    {"keys": [("name_id", 1)]},
                    {"keys": [("location_id", 1)]},
                    {"keys": [("when", 1)]},
                ],
                "images": [
                    {"keys": [("content_type", 1)]},
                    {"keys": [("license_id", 1)]},
                    {"keys": [("diagnostic", 1)]},
                ],
                "images_observations": [
                    {"keys": [("image_id", 1)]},
                    {"keys": [("observation_id", 1)]},
                    {"keys": [("rank", -1)]},
                ],
            }

            for collection_name, indexes in collections_config.items():
                collection = self.get_collection(collection_name)
                await self.ensure_indexes(collection, indexes)
                logger.info(f"Initialized {collection_name} collection with indexes")

            logger.info("Database initialization complete")
            return True

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}")


# Helper class for sync->async iteration
class AsyncIterator:
    """Wrap a sync iterator for async usage."""

    def __init__(self, sync_iter):
        self.sync_iter = sync_iter

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.sync_iter)
        except StopIteration:
            raise StopAsyncIteration


async def get_database(config: DataConfig) -> AsyncDatabase:
    """Get database instance and ensure connection."""
    db = AsyncDatabase(config)
    await db.connect()
    return db
