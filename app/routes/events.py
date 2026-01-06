"""
Events discovery routes for local event discovery and distribution.
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models import (
    EventDiscoveryRequest,
    EventDiscoveryResponse,
    BatchEventRequest,
    BatchEventResponse,
    CenterInfo,
    BatchRunStatus
)
from app.utils.llm_client import LLMClient
from app.utils.event_parser import EventParser
from app.utils.csv_generator import CSVGenerator
from app.utils.email_service import EmailService
from app.utils.event_scheduler import EventScheduler

router = APIRouter(prefix="/events", tags=["Events"])
logger = logging.getLogger(__name__)

# Initialize services
llm_client = LLMClient()
event_parser = EventParser()
csv_generator = CSVGenerator()
email_service = EmailService()
scheduler = EventScheduler()


async def discover_events_for_center(center: CenterInfo) -> EventDiscoveryResponse:
    """
    Discover events for a single center.
    
    Args:
        center: Center information
        
    Returns:
        EventDiscoveryResponse: Discovery result
    """
    try:
        # Build location string
        location_parts = []
        if center.zip_code:
            location_parts.append(center.zip_code)
        if center.city:
            location_parts.append(center.city)
        if center.state:
            location_parts.append(center.state)
        location = ", ".join(location_parts) if location_parts else center.city or center.zip_code or "Unknown"
        
        # Generate prompt
        prompt = llm_client.generate_events_prompt(
            location=location,
            radius=center.radius,
            country=center.country
        )
        logger.info(f"Generated prompt: {prompt}")
        # Query LLM
        logger.info(f"Querying LLM for center {center.center_name} ({location})...")
        llm_response = await llm_client.query_llm(prompt)
        if not llm_response:
            logger.warning(f"LLM returned empty response for center {center.center_id}")
            try:
                csv_path = csv_generator.generate_fallback_csv(
                    center_name=center.center_name,
                    message="No events found or AI failed for this run."
                )
            except Exception as csv_error:
                logger.error(f"Failed to generate fallback CSV: {str(csv_error)}", exc_info=True)
                csv_path = None
            return EventDiscoveryResponse(
                center_id=center.center_id,
                center_name=center.center_name,
                events=[],
                event_count=0,
                csv_path=csv_path,
                status="failed",
                message="LLM API returned empty response"
            )
        
        # Log LLM response for debugging
        logger.info(f"LLM response length: {len(llm_response)} characters")
        logger.debug(f"LLM response preview (first 1000 chars):\n{llm_response[:1000]}")
        logger.debug(f"LLM response preview (last 500 chars):\n{llm_response[-500:]}")
        
        # Parse events from response
        try:
            events = event_parser.parse_ai_response(llm_response)
            logger.info(f"Parsed {len(events)} events from LLM response for center {center.center_id}")
            if len(events) == 0:
                logger.warning(f"No events were parsed from LLM response. Full response:\n{llm_response}")
        except Exception as parse_error:
            logger.error(f"Error parsing LLM response: {str(parse_error)}", exc_info=True)
            logger.error(f"LLM response that caused error:\n{llm_response}")
            events = []

        # Generate CSV - always try to generate, even if no events
        csv_path = None
        try:
            if events:
                csv_path = csv_generator.generate_csv(
                    events=events,
                    center_name=center.center_name
                )
                logger.info(f"Successfully generated CSV with {len(events)} events: {csv_path}")
            else:
                logger.warning(f"No events parsed from LLM response for center {center.center_id}")
                logger.info(f"LLM response sample: {llm_response[:1000]}...")
                csv_path = csv_generator.generate_fallback_csv(
                    center_name=center.center_name,
                    message="No events found or could not parse events from AI response."
                )
                logger.info(f"Generated fallback CSV: {csv_path}")
        except Exception as csv_error:
            logger.error(f"Error generating CSV file: {str(csv_error)}", exc_info=True)
            # Try fallback CSV if main CSV generation failed
            try:
                csv_path = csv_generator.generate_fallback_csv(
                    center_name=center.center_name,
                    message=f"Error generating CSV: {str(csv_error)}"
                )
            except Exception as fallback_error:
                logger.error(f"Failed to generate fallback CSV: {str(fallback_error)}", exc_info=True)
                csv_path = None
        
        # Determine status and message
        if events and csv_path:
            status = "success"
            message = f"Successfully found {len(events)} events"
        elif csv_path:
            status = "partial"
            message = "No events could be parsed from AI response, but CSV was generated"
        else:
            status = "failed"
            message = "Failed to generate CSV file"
        
        logger.info(f"Discovery complete for center {center.center_id}: status={status}, events={len(events)}, csv_path={csv_path}")
        
        return EventDiscoveryResponse(
            center_id=center.center_id,
            center_name=center.center_name,
            events=events,
            event_count=len(events),
            csv_path=csv_path,
            status=status,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error discovering events for center {center.center_id}: {str(e)}", exc_info=True)
        # Generate fallback CSV
        try:
            csv_path = csv_generator.generate_fallback_csv(
                center_name=center.center_name,
                message=f"Error during discovery: {str(e)}"
            )
        except:
            csv_path = None
        
        return EventDiscoveryResponse(
            center_id=center.center_id,
            center_name=center.center_name,
            events=[],
            event_count=0,
            csv_path=csv_path,
            status="failed",
            message=f"Error: {str(e)}"
        )


async def process_batch_run(run_id: str, centers: list, send_emails: bool):
    """
    Background task to process a batch run.
    
    Args:
        run_id: Batch run ID
        centers: List of CenterInfo objects
        send_emails: Whether to send email notifications
    """
    try:
        logger.info(f"Starting batch run {run_id} for {len(centers)} centers")
        
        # Process centers in parallel
        results = await scheduler.process_batch_async(
            centers=centers,
            discovery_func=discover_events_for_center,
            max_concurrent=5
        )
        
        # Update run status for each result
        for result in results:
            if result.status == "success":
                scheduler.update_run_status(run_id, result=result)
            else:
                scheduler.update_run_status(
                    run_id,
                    error=f"Center {result.center_id}: {result.message}"
                )
        
        # Send emails if requested
        if send_emails:
            from app.config import get_settings
            settings = get_settings()
            
            logger.info(f"Sending emails for batch run {run_id}...")
            logger.info(f"Email mode: send_to_owners={settings.email_send_to_owners}, test_recipient={settings.email_test_recipient}")
            logger.info(f"Email service enabled: {email_service.enabled}")
            if not email_service.enabled:
                logger.warning("⚠️  Email service is not configured! Check EMAIL_SMTP_HOST, EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD, and EMAIL_FROM settings.")
            
            email_reports = []
            for result in results:
                # Send email if CSV was generated (even if no events or errors occurred)
                if result.csv_path:
                    # Try to get email from center info
                    center = next((c for c in centers if c.center_id == result.center_id), None)
                    
                    # Determine recipient email based on settings
                    if settings.email_send_to_owners:
                        # Send to center owner
                        recipient_email = center.owner_email if center else None
                        if not recipient_email:
                            logger.warning(f"No owner email for center {result.center_id}, skipping email")
                            continue
                    else:
                        # Send to test email
                        recipient_email = settings.email_test_recipient
                        if not recipient_email:
                            logger.warning("Email test mode enabled but EMAIL_TEST_RECIPIENT not set, skipping email")
                            continue
                        logger.info(f"Test mode: Sending email for center {result.center_name} to test recipient {recipient_email}")
                    
                    # Create subject with test mode indicator if needed
                    subject = None
                    if not settings.email_send_to_owners:
                        subject = f"[TEST] Code Ninjas {result.center_name} - Local Events Report"
                    
                    # Add status indicator to subject if no events or error occurred
                    if result.status != "success" or result.event_count == 0:
                        if subject:
                            subject = subject.replace(" - Local Events Report", " - Local Events Report (No Events Found)")
                        else:
                            subject = f"Code Ninjas {result.center_name} - Local Events Report (No Events Found)"
                    
                    email_reports.append({
                        "recipient_email": recipient_email,
                        "csv_path": result.csv_path,
                        "center_name": result.center_name,
                        "event_count": result.event_count,
                        "radius": center.radius if center else 5,
                        "location": f"{center.city or ''}, {center.state or ''}".strip() if center else "Unknown",
                        "subject": subject
                    })
                else:
                    logger.warning(f"No CSV generated for center {result.center_id} ({result.center_name}), skipping email. Status: {result.status}, Message: {result.message}")
            
            if email_reports:
                logger.info(f"Preparing to send {len(email_reports)} email(s) for batch run {run_id}")
                email_result = email_service.send_batch_reports(email_reports)
                logger.info(f"Email send result: {email_result['success_count']} succeeded, {email_result['failed_count']} failed for batch run {run_id}")
                if email_result['failed_count'] > 0:
                    logger.warning(f"⚠️  {email_result['failed_count']} email(s) failed to send. Check email configuration and logs above for details.")
            else:
                logger.warning(f"No email reports generated for batch run {run_id} - check if CSV files were generated for centers")
        
        logger.info(f"Batch run {run_id} completed")
        
    except Exception as e:
        logger.error(f"Error in batch run {run_id}: {str(e)}", exc_info=True)
        scheduler.mark_run_failed(run_id, str(e))


@router.post("/discover", response_model=EventDiscoveryResponse)
async def discover_events(request: EventDiscoveryRequest) -> EventDiscoveryResponse:
    """
    Discover events for a single center.
    Optionally sends email notification to center owner.
    
    Args:
        request: Event discovery request with center information
        
    Returns:
        EventDiscoveryResponse: Discovery results with email status
    """
    try:
        logger.info(f"Processing event discovery request for center: {request.center_name}")
        
        # Convert request to CenterInfo
        center = CenterInfo(
            center_id=request.center_id,
            center_name=request.center_name,
            zip_code=request.zip_code,
            city=request.city,
            state=request.state,
            country=request.country,
            radius=request.radius,
            owner_email=request.owner_email
        )
        
        # Discover events
        result = await discover_events_for_center(center)
        
        # Send email if requested and email address provided
        # Always send email if CSV was generated, even if no events found or errors occurred
        email_sent = False
        email_message = None
        
        if request.send_email and request.owner_email:
            if result.csv_path:
                # Build location string for email
                location_parts = []
                if request.city:
                    location_parts.append(request.city)
                if request.state:
                    location_parts.append(request.state)
                location = ", ".join(location_parts) if location_parts else request.zip_code or "Unknown"
                
                # Create subject with status indicator if no events or error
                subject = None
                if result.status != "success" or result.event_count == 0:
                    subject = f"Code Ninjas {request.center_name} - Local Events Report (No Events Found)"
                
                logger.info(f"Sending email to {request.owner_email} for center {request.center_name} (Status: {result.status}, Events: {result.event_count})")
                email_sent = email_service.send_events_report(
                    recipient_email=request.owner_email,
                    csv_path=result.csv_path,
                    center_name=request.center_name,
                    event_count=result.event_count,
                    radius=request.radius,
                    location=location,
                    subject=subject
                )
                
                if email_sent:
                    email_message = f"Email successfully sent to {request.owner_email}"
                    logger.info(email_message)
                else:
                    email_message = f"Failed to send email to {request.owner_email}. Check email configuration."
                    logger.warning(email_message)
            else:
                email_message = "Cannot send email: CSV file was not generated"
                logger.warning(email_message)
        elif request.send_email and not request.owner_email:
            email_message = "Email requested but no owner_email provided"
            logger.warning(email_message)
        
        # Update result with email status
        result.email_sent = email_sent
        result.email_message = email_message
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing discovery request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing discovery request: {str(e)}"
        )


@router.post("/batch", response_model=BatchEventResponse)
async def batch_discover_events(
    request: BatchEventRequest,
    background_tasks: BackgroundTasks
) -> BatchEventResponse:
    """
    Start a batch event discovery run for multiple centers.
    
    Args:
        request: Batch event discovery request
        background_tasks: FastAPI background tasks
        
    Returns:
        BatchEventResponse: Batch run information
    """
    try:
        logger.info(f"Starting batch discovery for {len(request.centers)} centers")
        
        # Create batch run
        run_id = scheduler.create_batch_run(len(request.centers))
        
        # Start background processing
        background_tasks.add_task(
            process_batch_run,
            run_id=run_id,
            centers=request.centers,
            send_emails=request.send_emails
        )
        
        return BatchEventResponse(
            run_id=run_id,
            status="running",
            message=f"Batch run started for {len(request.centers)} centers",
            started_at=scheduler.get_run_status(run_id).started_at
        )
        
    except Exception as e:
        logger.error(f"Error starting batch discovery: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error starting batch discovery: {str(e)}"
        )


@router.get("/status/{run_id}", response_model=BatchRunStatus)
async def get_batch_status(run_id: str) -> BatchRunStatus:
    """
    Get the status of a batch run.
    
    Args:
        run_id: The batch run ID
        
    Returns:
        BatchRunStatus: Current run status
    """
    run_status = scheduler.get_run_status(run_id)
    
    if not run_status:
        raise HTTPException(
            status_code=404,
            detail=f"Batch run {run_id} not found"
        )
    
    return run_status

