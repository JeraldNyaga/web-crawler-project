"""
Main entry point for the web crawler project.
Provides CLI commands to run different components.
"""
import sys
import asyncio
from loguru import logger

from config import settings


def setup_logging():
    """Configure logging for the application."""
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # File handler
    if settings.log_file_enabled:
        logger.add(
            f"{settings.log_dir}/app.log",
            rotation="10 MB",
            retention="1 week",
            level=settings.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
        )


def print_banner():
    """Print application banner."""
    banner = """
    ╔═══════════════════════════════════════════╗
    ║   Web Crawler - Books Scraper Project    ║
    ║          Production Grade System          ║
    ╚═══════════════════════════════════════════╝
    """
    print(banner)


async def run_crawler():
    """Run the web crawler."""
    from crawler.scraper import BookCrawler
    from database import db
    
    logger.info("Starting crawler...")
    
    try:
        await db.connect()
        crawler = BookCrawler()
        await crawler.crawl()
        logger.success("Crawling completed successfully!")
    except Exception as e:
        logger.error(f"Crawler failed: {e}")
        raise
    finally:
        await db.disconnect()


def run_api():
    """Run the FastAPI server."""
    import uvicorn
    from api.main import app
    
    logger.info(f"Starting API server on {settings.api_host}:{settings.api_port}")
    
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )


async def run_scheduler():
    """Run the scheduler for change detection."""
    from scheduler.scheduler import start_scheduler
    from database import db
    
    logger.info("Starting scheduler...")
    
    try:
        await db.connect()
        await start_scheduler()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler failed: {e}")
        raise
    finally:
        await db.disconnect()


def print_usage():
    """Print usage information."""
    usage = """
Usage: python main.py [command]

Commands:
  crawl      - Run the web crawler
  api        - Start the REST API server
  schedule   - Run the scheduler for change detection
  help       - Show this help message

Examples:
  python main.py crawl       # Crawl the website
  python main.py api         # Start API on port 8000
  python main.py schedule    # Run daily scheduler

For more information, see README.md
    """
    print(usage)


def main():
    """Main entry point."""
    setup_logging()
    print_banner()
    
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "crawl":
            asyncio.run(run_crawler())
        elif command == "api":
            run_api()
        elif command == "schedule":
            asyncio.run(run_scheduler())
        elif command in ["help", "-h", "--help"]:
            print_usage()
        else:
            logger.error(f"Unknown command: {command}")
            print_usage()
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.exception(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()