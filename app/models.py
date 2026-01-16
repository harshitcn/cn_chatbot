"""
Pydantic models for request/response validation.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class FAQRequest(BaseModel):
    """Request model for FAQ endpoint."""
    question: str = Field(..., description="User's question", min_length=1)
    location_slug: Optional[str] = Field(None, description="Optional location slug for location-specific queries")
    location: Optional[str] = Field(None, description="Alias for location_slug (deprecated, use location_slug)")
    
    class Config:
        populate_by_name = True  # Allow both 'location' and 'location_slug' field names
    
    def __init__(self, **data):
        """Initialize with support for both 'location' and 'location_slug'."""
        # If 'location' is provided but 'location_slug' is not, use 'location' as location_slug
        if 'location' in data and 'location_slug' not in data:
            data['location_slug'] = data.get('location')
        super().__init__(**data)


class FAQResponse(BaseModel):
    """Response model for FAQ endpoint."""
    answer: str = Field(..., description="Answer to the user's question")


class WelcomeResponse(BaseModel):
    """Response model for root endpoint."""
    message: str = Field(..., description="Welcome message")


# Event Discovery Models

class EventItem(BaseModel):
    """Model for a single event item."""
    event_name: str = Field(..., description="Name of the event")
    event_date: Optional[str] = Field(None, description="Date of the event")
    website_url: Optional[str] = Field(None, description="Event website or URL")
    location: Optional[str] = Field(None, description="Venue or general area")
    organizer_contact: Optional[str] = Field(None, description="Organizer contact information (email, phone, or link)")
    fees: Optional[str] = Field(None, description="Participation fees if any")
    notes: Optional[str] = Field(None, description="Freeform observations or notes")


class EventDiscoveryRequest(BaseModel):
    """Request model for single center event discovery."""
    center_id: str = Field(..., description="Unique identifier for the center")
    center_name: str = Field(..., description="Name of the Code Ninjas center")
    zip_code: Optional[str] = Field(None, description="ZIP code or postal code")
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State or province")
    country: str = Field(default="USA", description="Country (default: USA)")
    radius: int = Field(default=5, description="Search radius in miles (default: 5)", ge=1, le=50)
    owner_email: Optional[str] = Field(None, description="Center owner email address for sending the report")
    send_email: bool = Field(default=False, description="Whether to send email notification to the owner")


class EventDiscoveryResponse(BaseModel):
    """Response model for event discovery."""
    center_id: str = Field(..., description="Center identifier")
    center_name: str = Field(..., description="Center name")
    events: List[EventItem] = Field(default_factory=list, description="List of discovered events")
    event_count: int = Field(..., description="Number of events found")
    csv_path: Optional[str] = Field(None, description="Path to generated CSV file")
    status: str = Field(..., description="Status of the discovery (success, partial, failed)")
    message: Optional[str] = Field(None, description="Status message or error details")
    generated_at: datetime = Field(default_factory=datetime.now, description="Timestamp when report was generated")
    email_sent: bool = Field(default=False, description="Whether email was successfully sent")
    email_message: Optional[str] = Field(None, description="Email sending status message")


class CenterInfo(BaseModel):
    """Model for center information in batch requests."""
    center_id: str = Field(..., description="Unique identifier for the center")
    center_name: str = Field(..., description="Name of the Code Ninjas center")
    zip_code: Optional[str] = Field(None, description="ZIP code or postal code")
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State or province")
    country: str = Field(default="USA", description="Country (default: USA)")
    radius: int = Field(default=5, description="Search radius in miles (default: 5)", ge=1, le=50)
    owner_email: Optional[str] = Field(None, description="Center owner email for distribution")


class BatchEventRequest(BaseModel):
    """Request model for batch event discovery."""
    centers: List[CenterInfo] = Field(..., description="List of centers to process", min_length=1)
    send_emails: bool = Field(default=False, description="Whether to send email notifications")


class BatchRunStatus(BaseModel):
    """Model for tracking batch run status."""
    run_id: str = Field(..., description="Unique identifier for the batch run")
    status: str = Field(..., description="Overall status (running, completed, failed)")
    total_centers: int = Field(..., description="Total number of centers to process")
    processed_centers: int = Field(default=0, description="Number of centers processed")
    successful_centers: int = Field(default=0, description="Number of successful discoveries")
    failed_centers: int = Field(default=0, description="Number of failed discoveries")
    started_at: datetime = Field(default_factory=datetime.now, description="When the batch run started")
    completed_at: Optional[datetime] = Field(None, description="When the batch run completed")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    results: List[EventDiscoveryResponse] = Field(default_factory=list, description="Individual center results")


class BatchEventResponse(BaseModel):
    """Response model for batch event discovery."""
    run_id: str = Field(..., description="Unique identifier for the batch run")
    status: str = Field(..., description="Status of the batch run")
    message: str = Field(..., description="Status message")
    started_at: datetime = Field(..., description="When the batch run started")


# Text-to-Speech Models

class TTSRequest(BaseModel):
    """Request model for Text-to-Speech endpoint."""
    text: str = Field(..., description="Text to convert to speech", min_length=1)
