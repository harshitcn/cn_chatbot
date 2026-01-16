"""
Text-to-Speech (TTS) routes for converting text to speech audio.
"""
import logging
import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from gtts import gTTS
from app.models import TTSRequest

router = APIRouter(prefix="/tts", tags=["TTS"])
logger = logging.getLogger(__name__)


@router.post("/")
async def text_to_speech(request: TTSRequest) -> StreamingResponse:
    """
    Convert text to speech using Google Text-to-Speech (gTTS) and return as MP3 audio stream.
    
    Args:
        request: TTSRequest containing the text to convert
    
    Returns:
        StreamingResponse: MP3 audio file stream
    
    Raises:
        HTTPException: If text is empty or there's an error generating speech
    """
    try:
        # Validate text is not empty (Pydantic should handle this, but double-check)
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text field cannot be empty"
            )
        
        logger.info(f"Converting text to speech: {request.text[:50]}...")
        
        # Generate speech using gTTS
        # Using 'en' for English, can be made configurable if needed
        tts = gTTS(text=request.text, lang='en', slow=False)
        
        # Create in-memory buffer to store audio
        audio_buffer = io.BytesIO()
        
        # Write audio to buffer
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)  # Reset buffer position to beginning
        
        logger.info("Audio generated successfully")
        
        # Return audio as streaming response
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating speech: {str(e)}"
        )

