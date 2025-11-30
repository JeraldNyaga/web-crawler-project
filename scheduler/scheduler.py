"""
Scheduler for running periodic change detection.
"""
import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from config import settings
from database import db
from .change_detector import ChangeDetector


class ChangeDetectionScheduler:
    """Scheduler for periodic change detection."""
    
    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
        self.detector = ChangeDetector()
    
    async def run_change_detection_job(self):
        """Job that runs change detection."""
        logger.info("="*60)
        logger.info(f"Running scheduled change detection: {datetime.now(timezone.utc)}")
        logger.info("="*60)
        
        try:
            # Run change detection
            stats = await self.detector.detect_changes()
            
            # Generate report if there are changes
            if stats['total_changes'] > 0:
                logger.info("Generating change report...")
                
                # Generate JSON report
                json_report = await self.detector.generate_change_report(format='json')
                logger.info(f"JSON Report:\n{json_report}")
                
                # Optionally save reports to files
                await self._save_report(json_report, 'json')
                
                # Generate CSV report
                csv_report = await self.detector.generate_change_report(format='csv')
                await self._save_report(csv_report, 'csv')
                
                logger.success("Change detection completed successfully!")
            else:
                logger.info("No changes detected.")
                
        except Exception as e:
            logger.error(f"Change detection job failed: {e}")
            # In production, you might want to send an alert here
    
    async def _save_report(self, report_content: str, format: str):
        """
        Save report to file.
        
        Args:
            report_content: Report content
            format: Report format (json or csv)
        """
        from pathlib import Path
        
        # Create reports directory
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = reports_dir / f"change_report_{timestamp}.{format}"
        
        # Save report
        with open(filename, 'w') as f:
            f.write(report_content)
        
        logger.info(f"Report saved: {filename}")
    
    def setup_schedule(self):
        """Set up the schedule for change detection."""
        if not settings.scheduler_enabled:
            logger.warning("Scheduler is disabled in settings")
            return
        
        # Parse run time (format: "HH:MM")
        hour, minute = map(int, settings.scheduler_run_time.split(':'))
        
        # Add job to run daily at specified time
        self.scheduler.add_job(
            self.run_change_detection_job,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='change_detection_job',
            name='Daily Change Detection',
            replace_existing=True
        )
        
        logger.info(f"Scheduled change detection for daily at {settings.scheduler_run_time} {settings.scheduler_timezone}")
    
    async def run_once(self):
        """Run change detection once immediately."""
        logger.info("Running change detection once...")
        await self.run_change_detection_job()
    
    async def start(self):
        """Start the scheduler."""
        logger.info("Starting scheduler...")
        
        # Set up schedule
        self.setup_schedule()
        
        # Start scheduler
        self.scheduler.start()
        logger.success("Scheduler started successfully!")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(60)  # Check every minute
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down scheduler...")
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")


async def start_scheduler():
    """
    Start the scheduler for change detection.
    
    This function:
    1. Connects to database
    2. Sets up scheduled jobs
    3. Runs indefinitely until interrupted
    """
    scheduler = ChangeDetectionScheduler()
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        raise


async def run_detection_once():
    """
    Run change detection once (useful for testing).
    """
    scheduler = ChangeDetectionScheduler()
    await scheduler.run_once()


if __name__ == "__main__":
    # For testing
    asyncio.run(run_detection_once())