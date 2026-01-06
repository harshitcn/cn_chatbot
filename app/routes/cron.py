"""
Cron job management routes.
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models import BatchEventResponse
from app.utils.cron_service import CronService
from app.utils.center_service import CenterService

router = APIRouter(prefix="/cron", tags=["Cron Jobs"])
logger = logging.getLogger(__name__)


def get_cron_service() -> CronService:
    """Get the global cron service instance."""
    from app.main import cron_service
    return cron_service


@router.post("/sync-centers")
async def sync_centers():
    """
    Manually trigger center sync from APIs to database.
    Only works if SYNC_TO_DATABASE is enabled.
    
    Returns:
        dict: Sync result with count of synced centers
    """
    try:
        from app.config import get_settings
        settings = get_settings()
        
        if not settings.sync_to_database:
            return {
                "status": "skipped",
                "message": "Database sync is disabled. Set SYNC_TO_DATABASE=true to enable database syncing. Centers are fetched directly from APIs when running batch jobs.",
                "synced_count": 0
            }
        
        logger.info("Manual center sync triggered")
        center_service = CenterService()
        synced_count = await center_service.sync_centers_from_api()
        
        return {
            "status": "success",
            "message": f"Successfully synced {synced_count} centers to database",
            "synced_count": synced_count
        }
    except Exception as e:
        logger.error(f"Error syncing centers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error syncing centers: {str(e)}"
        )


@router.post("/run-batch")
async def run_batch(background_tasks: BackgroundTasks):
    """
    Manually trigger batch run for all active centers.
    Uses database if sync_to_database is True, otherwise fetches directly from APIs.
    
    Returns:
        BatchEventResponse: Batch run information
    """
    try:
        logger.info("Manual batch run triggered")
        
        # Get settings
        from app.config import get_settings
        settings = get_settings()
        
        center_service = CenterService()
        center_infos = []
        
        if settings.sync_to_database:
            # Get all active centers from database
            logger.info("Fetching centers from database...")
            centers = center_service.get_all_active_centers()
            
            if not centers:
                raise HTTPException(
                    status_code=404,
                    detail="No active centers found in database. Please sync centers first or set SYNC_TO_DATABASE=false to fetch from APIs."
                )
            
            # Limit centers in stage environment for testing
            if settings.app_env == "stage" and settings.test_mode_limit_centers > 0:
                original_count = len(centers)
                centers = centers[:settings.test_mode_limit_centers]
                logger.info(f"Stage environment: Limiting to first {len(centers)} centers (out of {original_count} total)")
            
            # Convert to CenterInfo format
            from app.models import CenterInfo
            for center in centers:
                center_info_dict = center_service.convert_center_to_center_info(center)
                center_info = CenterInfo(**center_info_dict)
                center_infos.append(center_info)
        else:
            # Fetch centers directly from APIs
            logger.info("Fetching centers directly from APIs (no database)...")
            center_info_dicts = await center_service.fetch_centers_from_api()
            
            if not center_info_dicts:
                raise HTTPException(
                    status_code=404,
                    detail="No centers found from APIs."
                )
            
            # Convert to CenterInfo format
            from app.models import CenterInfo
            for center_info_dict in center_info_dicts:
                center_info = CenterInfo(**center_info_dict)
                center_infos.append(center_info)
        
        # Create batch run
        from app.utils.event_scheduler import EventScheduler
        scheduler = EventScheduler()
        run_id = scheduler.create_batch_run(len(center_infos))
        
        # Always send emails (email_send_to_owners setting controls recipient, not whether to send)
        send_emails = True
        logger.info(f"Email settings: send_emails={send_emails}, send_to_owners={settings.email_send_to_owners}, test_recipient={settings.email_test_recipient}")
        
        # Start background processing
        from app.routes.events import process_batch_run
        background_tasks.add_task(
            process_batch_run,
            run_id=run_id,
            centers=center_infos,
            send_emails=send_emails
        )
        
        return BatchEventResponse(
            run_id=run_id,
            status="running",
            message=f"Batch run started for {len(center_infos)} centers",
            started_at=scheduler.get_run_status(run_id).started_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running batch: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error running batch: {str(e)}"
        )


@router.post("/sync-and-run")
async def sync_and_run(background_tasks: BackgroundTasks):
    """
    Manually trigger full process: sync centers (if enabled) and run batch.
    If sync_to_database is True, syncs to database first. Otherwise fetches directly from APIs.
    
    Returns:
        dict: Process result
    """
    try:
        logger.info("Manual sync and batch run triggered")
        
        # Get settings
        from app.config import get_settings
        settings = get_settings()
        
        center_service = CenterService()
        center_infos = []
        synced_count = 0
        
        if settings.sync_to_database:
            # Sync centers to database
            logger.info("Syncing centers to database...")
            synced_count = await center_service.sync_centers_from_api()
            logger.info(f"Synced {synced_count} centers to database")
            
            # Get all active centers from database
            centers = center_service.get_all_active_centers()
            
            if not centers:
                return {
                    "status": "success",
                    "message": f"Synced {synced_count} centers, but no active centers found for batch run",
                    "synced_count": synced_count,
                    "batch_run_id": None
                }
            
            # Limit centers in stage environment for testing
            if settings.app_env == "stage" and settings.test_mode_limit_centers > 0:
                original_count = len(centers)
                centers = centers[:settings.test_mode_limit_centers]
                logger.info(f"Stage environment: Limiting to first {len(centers)} centers (out of {original_count} total)")
            
            # Convert to CenterInfo format
            from app.models import CenterInfo
            for center in centers:
                center_info_dict = center_service.convert_center_to_center_info(center)
                center_info = CenterInfo(**center_info_dict)
                center_infos.append(center_info)
        else:
            # Fetch centers directly from APIs (no database sync)
            logger.info("Fetching centers directly from APIs (no database sync)...")
            center_info_dicts = await center_service.fetch_centers_from_api()
            
            if not center_info_dicts:
                return {
                    "status": "success",
                    "message": "No centers found from APIs for batch run",
                    "synced_count": 0,
                    "batch_run_id": None
                }
            
            # Convert to CenterInfo format
            from app.models import CenterInfo
            for center_info_dict in center_info_dicts:
                center_info = CenterInfo(**center_info_dict)
                center_infos.append(center_info)
            
            synced_count = len(center_info_dicts)
        
        # Create batch run
        from app.utils.event_scheduler import EventScheduler
        scheduler = EventScheduler()
        run_id = scheduler.create_batch_run(len(center_infos))
        
        # Always send emails (email_send_to_owners setting controls recipient, not whether to send)
        send_emails = True
        logger.info(f"Email settings: send_emails={send_emails}, send_to_owners={settings.email_send_to_owners}, test_recipient={settings.email_test_recipient}")
        
        # Start background processing
        from app.routes.events import process_batch_run
        background_tasks.add_task(
            process_batch_run,
            run_id=run_id,
            centers=center_infos,
            send_emails=send_emails
        )
        
        return {
            "status": "success",
            "message": f"Synced {synced_count} centers and started batch run for {len(center_infos)} centers",
            "synced_count": synced_count,
            "batch_run_id": run_id,
            "centers_count": len(center_infos)
        }
        
    except Exception as e:
        logger.error(f"Error in sync and run: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error in sync and run: {str(e)}"
        )


@router.get("/status")
async def get_cron_status():
    """
    Get cron service status and next run time.
    
    Returns:
        dict: Cron service status
    """
    cron_service = get_cron_service()
    
    if not cron_service:
        return {
            "enabled": False,
            "message": "Cron service not initialized"
        }
    
    return {
        "enabled": cron_service.scheduler.running,
        "next_run_time": cron_service.get_next_run_time(),
        "is_running": cron_service.is_running
    }

