"""Async database operations module."""

from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import UpdateOne
from dataclasses import asdict
import asyncio
import logging

from exceptions import DatabaseError
from monitoring import measure_performance
from config import DataConfig

logger = logging.getLogger(__name__)

class AsyncDatabase:
    """Async database operations handler."""
    
    def __init__(self, config: DataConfig):
        self.config = config
        self.client: Optional[AsyncIOMotorClient] = None
        
    async def connect(self) -> None:
        """Connect to the database."""
        try:
            self.client = AsyncIOMotorClient(self.config.MONGODB_URI)
            # Ping database to verify connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            raise DatabaseError(f"Failed to connect to MongoDB: {e}")
    
    async def close(self) -> None:
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")
    
    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """Get a collection by name."""
        if not self.client:
            raise DatabaseError("Database not connected")
        return self.client[self.config.DATABASE_NAME][name]
    
    @measure_performance
    async def batch_upsert(
        self,
        collection: AsyncIOMotorCollection,
        items: List[Any],
        batch_size: Optional[int] = None
    ) -> None:
        """Batch upsert items into collection."""
        if not items:
            return
            
        batch_size = batch_size or self.config.BATCH_SIZE
        operations = []
        
        try:
            for item in items:
                # Convert dataclass instances to dictionaries
                item_dict = asdict(item) if hasattr(item, '__dataclass_fields__') else item
                
                operations.append(
                    UpdateOne(
                        {"_id": item_dict.get("_id")},
                        {"$set": item_dict},
                        upsert=True
                    )
                )
                
                if len(operations) >= batch_size:
                    await collection.bulk_write(operations, ordered=False)
                    operations = []
            
            if operations:
                await collection.bulk_write(operations, ordered=False)
                
        except Exception as e:
            raise DatabaseError(f"Batch upsert failed: {e}")
    
    @measure_performance
    async def batch_delete(
        self,
        collection: AsyncIOMotorCollection,
        filter_query: Dict[str, Any]
    ) -> int:
        """Delete documents matching the filter query."""
        try:
            result = await collection.delete_many(filter_query)
            return result.deleted_count
        except Exception as e:
            raise DatabaseError(f"Batch delete failed: {e}")
    
    @measure_performance
    async def ensure_indexes(
        self,
        collection: AsyncIOMotorCollection,
        indexes: List[Dict[str, Any]]
    ) -> None:
        """Create indexes if they don't exist."""
        try:
            for index in indexes:
                await collection.create_index(**index)
        except Exception as e:
            raise DatabaseError(f"Failed to create indexes: {e}")

async def get_database(config: DataConfig) -> AsyncDatabase:
    """Get database instance and ensure connection."""
    db = AsyncDatabase(config)
    await db.connect()
    return db 