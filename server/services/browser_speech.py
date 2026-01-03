"""
Browser-Based Speech Recognition Service

Uses the Web Speech API through the browser instead of heavy server-side models.
This provides fast, accurate speech recognition without requiring Whisper/FFmpeg.
"""

import logging
from typing import Dict, Any, Tuple


class BrowserSpeechService:
    """Browser-based speech recognition service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def transcribe_audio(self, audio_data: bytes, filename: str = None, language: str = "en-US") -> str:
        """
        This service doesn't process audio server-side.
        Instead, it provides instructions for client-side speech recognition.
        
        Args:
            audio_data: Not used - kept for API compatibility
            filename: Not used - kept for API compatibility  
            language: Language code for transcription
            
        Returns:
            Instructions for client-side implementation
        """
        
        self.logger.info("Browser speech recognition requested")
        
        # Return a message indicating this should be handled client-side
        return "BROWSER_SPEECH_API_REQUIRED"
    
    async def health_check(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if the browser speech service is configured
        
        Returns:
            Tuple of (is_healthy: bool, details: dict)
        """
        return True, {
            "service": "BrowserSpeech",
            "status": "healthy",
            "implementation": "client_side",
            "supported_languages": ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE"],
            "api": "Web Speech API",
            "note": "Uses browser's built-in speech recognition"
        }
