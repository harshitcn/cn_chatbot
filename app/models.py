"""
Pydantic models for request/response validation.
"""
from typing import Optional
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

