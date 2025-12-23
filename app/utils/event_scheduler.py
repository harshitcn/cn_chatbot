"""
Event scheduler for batch processing and tracking runs.
Manages batch runs, status tracking, and parallel processing.
"""
import logging
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from app.models import CenterInfo, EventDiscoveryResponse, BatchRunStatus, EventItem

logger = logging.getLogger(__name__)


class EventScheduler:
    """
    Scheduler for managing batch event discovery runs.
    Tracks run status and manages parallel processing.
    """
    
    def __init__(self):
        """Initialize the event scheduler."""
        self.active_runs: Dict[str, BatchRunStatus] = {}
        self.completed_runs: Dict[str, BatchRunStatus] = {}
    
    def create_batch_run(self, total_centers: int) -> str:
        """
        Create a new batch run and return its ID.
        
        Args:
            total_centers: Total number of centers to process
            
        Returns:
            str: Unique run ID
        """
        run_id = str(uuid.uuid4())
        
        run_status = BatchRunStatus(
            run_id=run_id,
            status="running",
            total_centers=total_centers,
            processed_centers=0,
            successful_centers=0,
            failed_centers=0,
            started_at=datetime.now()
        )
        
        self.active_runs[run_id] = run_status
        logger.info(f"Created batch run {run_id} for {total_centers} centers")
        
        return run_id
    
    def get_run_status(self, run_id: str) -> Optional[BatchRunStatus]:
        """
        Get status of a batch run.
        
        Args:
            run_id: The run ID to check
            
        Returns:
            Optional[BatchRunStatus]: Run status or None if not found
        """
        # Check active runs first
        if run_id in self.active_runs:
            return self.active_runs[run_id]
        
        # Check completed runs
        if run_id in self.completed_runs:
            return self.completed_runs[run_id]
        
        return None
    
    def update_run_status(
        self,
        run_id: str,
        result: Optional[EventDiscoveryResponse] = None,
        error: Optional[str] = None
    ):
        """
        Update the status of a batch run with a new result.
        
        Args:
            run_id: The run ID
            result: Optional successful result
            error: Optional error message
        """
        if run_id not in self.active_runs:
            logger.warning(f"Run {run_id} not found in active runs")
            return
        
        run_status = self.active_runs[run_id]
        run_status.processed_centers += 1
        
        if result:
            run_status.successful_centers += 1
            run_status.results.append(result)
        elif error:
            run_status.failed_centers += 1
            run_status.errors.append(error)
        
        # Check if run is complete
        if run_status.processed_centers >= run_status.total_centers:
            run_status.status = "completed"
            run_status.completed_at = datetime.now()
            # Move to completed runs
            self.completed_runs[run_id] = run_status
            del self.active_runs[run_id]
            logger.info(f"Batch run {run_id} completed: {run_status.successful_centers} succeeded, {run_status.failed_centers} failed")
    
    def mark_run_failed(self, run_id: str, error: str):
        """
        Mark a batch run as failed.
        
        Args:
            run_id: The run ID
            error: Error message
        """
        if run_id not in self.active_runs:
            logger.warning(f"Run {run_id} not found in active runs")
            return
        
        run_status = self.active_runs[run_id]
        run_status.status = "failed"
        run_status.completed_at = datetime.now()
        run_status.errors.append(error)
        
        # Move to completed runs
        self.completed_runs[run_id] = run_status
        del self.active_runs[run_id]
        logger.error(f"Batch run {run_id} failed: {error}")
    
    async def process_center_async(
        self,
        center: CenterInfo,
        discovery_func
    ) -> EventDiscoveryResponse:
        """
        Process a single center asynchronously.
        
        Args:
            center: Center information
            discovery_func: Async function to call for discovery
            
        Returns:
            EventDiscoveryResponse: Discovery result
        """
        try:
            logger.info(f"Processing center: {center.center_name} ({center.center_id})")
            result = await discovery_func(center)
            return result
        except Exception as e:
            logger.error(f"Error processing center {center.center_id}: {str(e)}", exc_info=True)
            # Return error response
            return EventDiscoveryResponse(
                center_id=center.center_id,
                center_name=center.center_name,
                events=[],
                event_count=0,
                status="failed",
                message=f"Error: {str(e)}"
            )
    
    async def process_batch_async(
        self,
        centers: List[CenterInfo],
        discovery_func,
        max_concurrent: int = 5
    ) -> List[EventDiscoveryResponse]:
        """
        Process multiple centers in parallel with concurrency control.
        
        Args:
            centers: List of centers to process
            discovery_func: Async function to call for each center
            max_concurrent: Maximum number of concurrent requests
            
        Returns:
            List[EventDiscoveryResponse]: List of results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(center: CenterInfo):
            async with semaphore:
                return await self.process_center_async(center, discovery_func)
        
        tasks = [process_with_semaphore(center) for center in centers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                center = centers[i]
                logger.error(f"Exception processing center {center.center_id}: {str(result)}")
                processed_results.append(EventDiscoveryResponse(
                    center_id=center.center_id,
                    center_name=center.center_name,
                    events=[],
                    event_count=0,
                    status="failed",
                    message=f"Exception: {str(result)}"
                ))
            else:
                processed_results.append(result)
        
        return processed_results

