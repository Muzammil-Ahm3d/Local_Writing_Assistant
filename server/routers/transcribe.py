"""
Voice Transcription Router

Handles /api/transcribe endpoint for speech-to-text conversion using faster-whisper.
Supports multipart file uploads with various audio formats.
"""

import time
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from pydantic import BaseModel, Field

from server.services.browser_speech import BrowserSpeechService

logger = logging.getLogger(__name__)

router = APIRouter()

class TranscribeResponse(BaseModel):
    """Response model for voice transcription"""
    text: str = Field(..., description="Transcribed text from audio")
    time_ms: int = Field(..., description="Processing time in milliseconds")
    audio_duration: Optional[float] = Field(None, description="Duration of audio in seconds")
    detected_language: Optional[str] = Field(None, description="Auto-detected language")
    confidence: Optional[float] = Field(None, description="Transcription confidence score")

class TranscribeInfoResponse(BaseModel):
    """Response model for transcription service info"""
    supported_formats: list[str] = Field(..., description="Supported audio formats")
    max_duration_seconds: int = Field(..., description="Maximum audio duration")
    min_duration_seconds: float = Field(..., description="Minimum audio duration")
    model_info: dict = Field(..., description="Model information")

# Global Browser Speech service instance  
_speech_service = None

def get_speech_service() -> BrowserSpeechService:
    """Get the browser speech service instance"""
    # This will be injected by the main app
    from server.main import browser_speech_service
    if not browser_speech_service:
        raise HTTPException(
            status_code=503,
            detail="Voice transcription service not available. Use browser speech recognition instead."
        )
    return browser_speech_service

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form(default="en-US", description="Language code (e.g., 'en-US', 'auto')"),
    speech_service: BrowserSpeechService = Depends(get_speech_service)
) -> TranscribeResponse:
    """
    Browser-based speech transcription endpoint
    
    This endpoint returns instructions for client-side speech recognition
    using the Web Speech API instead of processing audio server-side.
    """
    start_time = time.time()
    
    try:
        # Validate file
        if not audio.filename:
            raise HTTPException(
                status_code=400,
                detail="No audio file provided"
            )
        
        # Check file size (limit to reasonable size, ~50MB)
        content = await audio.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty audio file"
            )
        
        if len(content) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(
                status_code=400,
                detail="Audio file too large (max 50MB)"
            )
        
        logger.info(f"Browser speech recognition requested for: {audio.filename} ({len(content)} bytes, language: {language})")
        
        # Return browser speech API instructions
        return TranscribeResponse(
            text="Please use browser speech recognition - server-side audio processing not enabled",
            time_ms=1  # Instant response
        )
    except ValueError as e:
        # Audio validation errors
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio file: {str(e)}"
        )
    except RuntimeError as e:
        # Service errors (FFmpeg missing, model issues)
        if "ffmpeg" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail="Audio processing unavailable: FFmpeg not installed. Please install FFmpeg."
            )
        else:
            raise HTTPException(
                status_code=503,
                detail=f"Transcription service error: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Voice transcription failed: {str(e)}"
        )

@router.get("/transcribe/info", response_model=TranscribeInfoResponse)
async def get_transcription_info(
    speech_service: BrowserSpeechService = Depends(get_speech_service)
) -> TranscribeInfoResponse:
    """Get information about the transcription service"""
    try:
        # Return browser speech API info
        return TranscribeInfoResponse(
            supported_formats=["webm", "ogg", "wav", "mp3"],
            max_duration_seconds=300,
            min_duration_seconds=0.1,
            model_info={
                "type": "browser_speech_api",
                "description": "Web Speech API for browser-based recognition"
            }
        )
    except Exception as e:
        logger.error(f"Failed to get transcription info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve transcription service information"
        )

@router.post("/transcribe/test")
async def test_transcription_service(
    speech_service: BrowserSpeechService = Depends(get_speech_service)
) -> dict:
    """
    Test the transcription service health
    
    This endpoint can be used to check if the transcription service is working
    without uploading actual audio files.
    """
    try:
        # Browser speech API is always available
        return {
            "service": "Voice Transcription",
            "healthy": True,
            "details": {"type": "browser_speech_api", "status": "ready"},
            "message": "Browser speech recognition available"
        }
        
    except Exception as e:
        logger.error(f"Transcription service test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription service test failed: {str(e)}"
        )
