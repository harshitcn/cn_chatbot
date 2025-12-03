"""
FAQ routes for handling question-answer requests.
"""
from fastapi import APIRouter, HTTPException
from app.models import FAQRequest, FAQResponse
from app.chains import get_retriever

router = APIRouter(prefix="/faq", tags=["FAQ"])


@router.post("/", response_model=FAQResponse)
async def get_faq_answer(request: FAQRequest) -> FAQResponse:
    """
    Endpoint to get FAQ answer for a user question.
    Supports location-based queries by detecting location in the question.
    
    Args:
        request: FAQRequest containing the user's question
    
    Returns:
        FAQResponse: Contains the answer to the question
    
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        retriever = get_retriever()
        answer = await retriever.get_answer(request.question)
        return FAQResponse(answer=answer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

