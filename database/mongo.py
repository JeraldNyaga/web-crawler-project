"""
MongoDB database connection and operations.
Uses Motor for async operations.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from loguru import logger
from config import settings


class MongoDB:
    """MongoDB database manager with async operations."""
    
    def __init__(self):
        """Initialize MongoDB connection variables."""
        self.client = None
        self.db = None
    
    async def connect(self):
        """Establish connection to MongoDB."""
        from motor.motor_asyncio import AsyncIOMotorClient
        
        try:
            self.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[settings.mongodb_db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.mongodb_db_name}")
            
            # Create indexes
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self):
        """Create database indexes for efficient querying."""
        try:
            # Books collection indexes
            await self.db.books.create_index("url", unique=True)
            await self.db.books.create_index("category")
            await self.db.books.create_index("price_incl_tax")
            await self.db.books.create_index("rating")
            await self.db.books.create_index("crawl_timestamp")
            await self.db.books.create_index("content_hash")
            
            # Changes collection indexes
            await self.db.changes.create_index("book_id")
            await self.db.changes.create_index("changed_at")
            await self.db.changes.create_index([("changed_at", -1)])  # Descending for recent changes
            
            # Crawl state collection
            await self.db.crawl_state.create_index("state_type", unique=True)
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    async def insert_book(self, book_data: Dict[str, Any]) -> Optional[str]:
        """
        Insert a new book into the database.
        
        Args:
            book_data: Dictionary containing book information
            
        Returns:
            Inserted document ID or None if duplicate
        """
        try:
            result = await self.db.books.insert_one(book_data)
            logger.info(f"Inserted book: {book_data.get('title', 'Unknown')}")
            return str(result.inserted_id)
        except DuplicateKeyError:
            logger.debug(f"Book already exists: {book_data.get('url')}")
            return None
        except Exception as e:
            logger.error(f"Error inserting book: {e}")
            raise
    
    async def update_book(self, url: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing book.
        
        Args:
            url: Book URL (unique identifier)
            update_data: Fields to update
            
        Returns:
            True if updated, False otherwise
        """
        try:
            result = await self.db.books.update_one(
                {"url": url},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating book: {e}")
            raise
    
    async def get_book_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get book by URL."""
        try:
            return await self.db.books.find_one({"url": url})
        except Exception as e:
            logger.error(f"Error fetching book: {e}")
            return None
    
    async def get_all_books(self) -> List[Dict[str, Any]]:
        """Get all books from database."""
        try:
            cursor = self.db.books.find({})
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error fetching all books: {e}")
            return []
    
    async def log_change(self, change_data: Dict[str, Any]) -> Optional[str]:
        """
        Log a change in the changes collection.
        
        Args:
            change_data: Change information
            
        Returns:
            Inserted change ID
        """
        try:
            change_data["changed_at"] = datetime.utcnow()
            result = await self.db.changes.insert_one(change_data)
            logger.info(f"Logged change: {change_data.get('change_type')}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error logging change: {e}")
            raise
    
    async def get_recent_changes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent changes, sorted by date descending."""
        try:
            cursor = self.db.changes.find().sort("changed_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error fetching changes: {e}")
            return []
    
    async def save_crawl_state(self, state_data: Dict[str, Any]):
        """Save crawler state for resume capability."""
        try:
            await self.db.crawl_state.update_one(
                {"state_type": "crawler"},
                {"$set": state_data},
                upsert=True
            )
            logger.debug("Crawl state saved")
        except Exception as e:
            logger.error(f"Error saving crawl state: {e}")
            raise
    
    async def get_crawl_state(self) -> Optional[Dict[str, Any]]:
        """Get last crawl state."""
        try:
            return await self.db.crawl_state.find_one({"state_type": "crawler"})
        except Exception as e:
            logger.error(f"Error fetching crawl state: {e}")
            return None
    
    async def clear_crawl_state(self):
        """Clear crawl state after successful completion."""
        try:
            await self.db.crawl_state.delete_one({"state_type": "crawler"})
            logger.debug("Crawl state cleared")
        except Exception as e:
            logger.error(f"Error clearing crawl state: {e}")


# Global database instance (initialize as None, will be set in connect)
_db_instance: Optional[MongoDB] = None


def get_db() -> MongoDB:
    """Get the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = MongoDB()
    return _db_instance


# Convenience reference
db = get_db()