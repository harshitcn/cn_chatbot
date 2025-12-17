"""
FAQ routes for handling question-answer requests.
"""
import logging
from fastapi import APIRouter, HTTPException
from app.models import FAQRequest, FAQResponse
from app.chains import get_retriever

router = APIRouter(prefix="/faq", tags=["FAQ"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=FAQResponse)
async def get_faq_answer(request: FAQRequest) -> FAQResponse:
    """
    Endpoint to get FAQ answer for a user question.
    Supports location-based queries by detecting location in the question or using location_slug parameter.
    
    Args:
        request: FAQRequest containing the user's question and optional location_slug
    
    Returns:
        FAQResponse: Contains the answer to the question
    
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        logger.info(f"Processing FAQ request: {request.question[:50]}...")
        
        # Lazy load retriever on first request (saves memory on startup)
        logger.info("Loading retriever (first request may take 30-60 seconds to download models)...")
        retriever = get_retriever()
        
        # Check if retriever is initialized
        if not retriever.vector_store:
            logger.warning("Retriever vector store not initialized, attempting to initialize...")
            retriever._initialize_vector_store()
        
        answer = await retriever.get_answer(request.question, location_slug=request.location_slug)
        logger.info("FAQ request processed successfully")
        return FAQResponse(answer=answer)
        
    except MemoryError as e:
        logger.error(f"Out of memory error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable due to memory constraints. Please try again in a moment or contact support."
        )
    except Exception as e:
        logger.error(f"Error processing FAQ request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

