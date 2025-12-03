"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field


class FAQRequest(BaseModel):
    """Request model for FAQ endpoint."""
    question: str = Field(..., description="User's question", min_length=1)


class FAQResponse(BaseModel):
    """Response model for FAQ endpoint."""
    answer: str = Field(..., description="Answer to the user's question")


class WelcomeResponse(BaseModel):
    """Response model for root endpoint."""
    message: str = Field(..., description="Welcome message")

