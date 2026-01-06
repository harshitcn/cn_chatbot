"""
Cron job service for automated batch processing of centers.
"""
import logging
import asyncio
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import get_settings
from app.utils.center_service import CenterService
from app.models import CenterInfo, BatchEventRequest
from app.routes.events import process_batch_run
from app.utils.event_scheduler import EventScheduler

logger = logging.getLogger(__name__)


class CronService:
    """Service for managing cron jobs."""
    
    def __init__(self):
        """Initialize the cron service."""
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler()
        self.center_service = CenterService()
        self.event_scheduler = EventScheduler()
        self.is_running = False
    
    async def sync_and_run_batch(self):
        """
        Main cron job function:
        If sync_to_database is True:
            1. Sync centers from APIs to database
            2. Get all active centers from database
            3. Run batch process for all centers
        If sync_to_database is False:
            1. Fetch centers directly from APIs (no database)
            2. Run batch process for all centers
        """
        if self.is_running:
            logger.warning("Batch job is already running, skipping this execution")
            return
        
        self.is_running = True
        logger.info("=" * 80)
        logger.info("Starting scheduled batch job: Sync centers and run batch process")
        logger.info(f"Database sync mode: {self.settings.sync_to_database}")
        logger.info("=" * 80)
        
        try:
            center_infos = []
            
            if self.settings.sync_to_database:
                # Step 1: Sync centers from APIs to database
                logger.info("Step 1: Syncing centers from APIs to database...")
                synced_count = await self.center_service.sync_centers_from_api()
                logger.info(f"Synced {synced_count} centers to database")
                
                # Step 2: Get all active centers from database
                logger.info("Step 2: Fetching active centers from database...")
                centers = self.center_service.get_all_active_centers()
                logger.info(f"Found {len(centers)} active centers")
                
                if not centers:
                    logger.warning("No active centers found, skipping batch run")
                    return
                
                # Step 2.5: Limit centers in stage environment for testing
                if self.settings.app_env == "stage" and self.settings.test_mode_limit_centers > 0:
                    original_count = len(centers)
                    centers = centers[:self.settings.test_mode_limit_centers]
                    logger.info(f"Stage environment: Limiting to first {len(centers)} centers (out of {original_count} total)")
                
                # Step 3: Convert centers to CenterInfo format
                logger.info("Step 3: Converting centers to batch format...")
                for center in centers:
                    center_info_dict = self.center_service.convert_center_to_center_info(center)
                    center_info = CenterInfo(**center_info_dict)
                    center_infos.append(center_info)
            else:
                # Step 1: Fetch centers directly from APIs (no database)
                logger.info("Step 1: Fetching centers directly from APIs (no database sync)...")
                center_info_dicts = await self.center_service.fetch_centers_from_api()
                logger.info(f"Fetched {len(center_info_dicts)} centers from APIs")
                
                if not center_info_dicts:
                    logger.warning("No centers found from APIs, skipping batch run")
                    return
                
                # Step 2: Convert to CenterInfo format
                logger.info("Step 2: Converting centers to batch format...")
                for center_info_dict in center_info_dicts:
                    center_info = CenterInfo(**center_info_dict)
                    center_infos.append(center_info)
            
            # Step 4 (or Step 3 if not using database): Create batch run and process
            step_num = "Step 4" if self.settings.sync_to_database else "Step 3"
            logger.info(f"{step_num}: Starting batch run for {len(center_infos)} centers...")
            run_id = self.event_scheduler.create_batch_run(len(center_infos))
            logger.info(f"Created batch run with ID: {run_id}")
            
            # Always send emails (email_send_to_owners setting controls recipient, not whether to send)
            send_emails = True
            logger.info(f"Email settings: send_emails={send_emails}, send_to_owners={self.settings.email_send_to_owners}, test_recipient={self.settings.email_test_recipient}")
            
            # Process batch run asynchronously
            await process_batch_run(
                run_id=run_id,
                centers=center_infos,
                send_emails=send_emails
            )
            
            logger.info(f"Batch run {run_id} completed")
            logger.info("=" * 80)
            logger.info("Scheduled batch job completed successfully")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error in scheduled batch job: {str(e)}", exc_info=True)
        finally:
            self.is_running = False
    
    def start_scheduler(self, cron_expression: str = "0 2 * * *"):
        """
        Start the cron scheduler with the specified schedule.
        
        Args:
            cron_expression: Cron expression (default: "0 2 * * *" = daily at 2 AM)
                            Format: minute hour day month day_of_week
                            Examples:
                            - "0 2 * * *" = Daily at 2 AM
                            - "0 */6 * * *" = Every 6 hours
                            - "0 0 * * 0" = Weekly on Sunday at midnight
        """
        if self.scheduler.running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            # Parse cron expression
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValueError(f"Invalid cron expression: {cron_expression}. Expected 5 parts (minute hour day month day_of_week)")
            
            minute, hour, day, month, day_of_week = parts
            
            # Add cron job
            self.scheduler.add_job(
                self.sync_and_run_batch,
                trigger=CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                ),
                id="sync_and_batch_job",
                name="Sync Centers and Run Batch Process",
                replace_existing=True
            )
            
            # Start scheduler
            self.scheduler.start()
            logger.info(f"Cron scheduler started with schedule: {cron_expression}")
            logger.info("Next run times:")
            for job in self.scheduler.get_jobs():
                logger.info(f"  - {job.name}: {job.next_run_time}")
            
        except Exception as e:
            logger.error(f"Error starting cron scheduler: {str(e)}", exc_info=True)
            raise
    
    def stop_scheduler(self):
        """Stop the cron scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Cron scheduler stopped")
        else:
            logger.warning("Scheduler is not running")
    
    def get_next_run_time(self) -> str:
        """Get the next scheduled run time."""
        jobs = self.scheduler.get_jobs()
        if jobs:
            next_run = jobs[0].next_run_time
            return str(next_run) if next_run else "Not scheduled"
        return "No jobs scheduled"

