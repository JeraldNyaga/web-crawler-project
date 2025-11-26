"""
Test script to verify MongoDB connection and basic setup.
Run this after setup to ensure everything is configured correctly.
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

# Configure simple logging
logger.remove()
logger.add(sys.stdout, format="<level>{level: <8}</level> | {message}", level="INFO")


async def test_mongodb_connection():
    """Test MongoDB connection."""
    try:
        from config import settings
        
        logger.info("Testing MongoDB connection...")
        logger.info(f"Connection URI: {settings.mongodb_uri[:50]}...")
        
        # Create client
        client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000
        )
        
        # Test connection
        await client.admin.command('ping')
        logger.success("✓ MongoDB connection successful!")
        
        # Get database
        db = client[settings.mongodb_db_name]
        logger.info(f"✓ Database: {settings.mongodb_db_name}")
        
        # List collections
        collections = await db.list_collection_names()
        logger.info(f"✓ Existing collections: {collections if collections else 'None (new database)'}")
        
        # Test write operation
        test_collection = db.test_connection
        result = await test_collection.insert_one({"test": "connection", "status": "success"})
        logger.success(f"✓ Write test successful! Inserted ID: {result.inserted_id}")
        
        # Test read operation
        doc = await test_collection.find_one({"_id": result.inserted_id})
        logger.success(f"✓ Read test successful! Document: {doc}")
        
        # Cleanup
        await test_collection.delete_one({"_id": result.inserted_id})
        logger.info("✓ Test document cleaned up")
        
        # Close connection
        client.close()
        logger.success("✓ All MongoDB tests passed!")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ MongoDB connection failed: {e}")
        logger.error("\nTroubleshooting tips:")
        logger.error("1. Check your MONGODB_URI in .env file")
        logger.error("2. Verify MongoDB Atlas IP whitelist (should include 0.0.0.0/0)")
        logger.error("3. Confirm database user credentials are correct")
        logger.error("4. Check your internet connection")
        return False


async def test_packages():
    """Test that all required packages are installed."""
    logger.info("\nTesting required packages...")
    
    packages = [
        ("fastapi", "FastAPI web framework"),
        ("httpx", "Async HTTP client"),
        ("motor", "Async MongoDB driver"),
        ("pydantic", "Data validation"),
        ("apscheduler", "Task scheduler"),
        ("loguru", "Logging"),
        ("pytest", "Testing framework"),
    ]
    
    all_ok = True
    for package, description in packages:
        try:
            __import__(package)
            logger.success(f"✓ {package:20} - {description}")
        except ImportError:
            logger.error(f"✗ {package:20} - MISSING")
            all_ok = False
    
    if all_ok:
        logger.success("\n✓ All packages installed correctly!")
    else:
        logger.error("\n✗ Some packages are missing. Run: pip install -r requirements.txt")
    
    return all_ok


async def test_config():
    """Test configuration loading."""
    logger.info("\nTesting configuration...")
    
    try:
        from config import settings
        
        # Check critical settings
        checks = [
            ("MONGODB_URI", settings.mongodb_uri),
            ("API_SECRET_KEY", settings.api_secret_key),
            ("API_KEYS", settings.api_keys),
        ]

        all_ok = True
        for name, value in checks:
            if not value or value.strip() == "":
                logger.error(f"✗ {name} not properly configured in .env")
                all_ok = False
            else:
                logger.success(f"✓ {name} configured")

        
        if all_ok:
            logger.success("✓ Configuration loaded successfully!")
        else:
            logger.error("✗ Please update your .env file")
        
        return all_ok
        
    except Exception as e:
        logger.error(f"✗ Configuration error: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("=" * 50)
    logger.info("Web Crawler - Connection Test Suite")
    logger.info("=" * 50)
    
    # Test packages
    packages_ok = await test_packages()
    
    if not packages_ok:
        logger.error("\nPlease install missing packages first!")
        sys.exit(1)
    
    # Test config
    config_ok = await test_config()
    
    if not config_ok:
        logger.error("\nPlease configure .env file first!")
        sys.exit(1)
    
    # Test MongoDB
    mongo_ok = await test_mongodb_connection()
    
    # Summary
    logger.info("\n" + "=" * 50)
    if packages_ok and config_ok and mongo_ok:
        logger.success("✓ ALL TESTS PASSED!")
        logger.success("\nYou're ready to start development!")
        logger.info("\nNext steps:")
        logger.info("1. Run crawler: python main.py crawl")
        logger.info("2. Start API: python main.py api")
        logger.info("3. Run scheduler: python main.py schedule")
    else:
        logger.error("✗ SOME TESTS FAILED")
        logger.error("\nPlease fix the errors above before continuing.")
        sys.exit(1)
    
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())