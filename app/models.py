"""
Pydantic models for request/response validation.
"""
from typing import Optional
from pydantic import BaseModel, Field


class FAQRequest(BaseModel):
    """Request model for FAQ endpoint."""
    question: str = Field(..., description="User's question", min_length=1)
    location_slug: Optional[str] = Field(None, description="Optional location slug for location-specific queries")


class FAQResponse(BaseModel):
    """Response model for FAQ endpoint."""
    answer: str = Field(..., description="Answer to the user's question")


class WelcomeResponse(BaseModel):
    """Response model for root endpoint."""
    message: str = Field(..., description="Welcome message")

