"""
Whisper ASR Service for Local Writing Assistant

Provides voice-to-text transcription using faster-whisper (CTranslate2).
Optimized for CPU-only inference with int8 quantization.
Handles audio file conversion using FFmpeg.
"""

import os
import asyncio
import tempfile
import logging
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import subprocess


class WhisperService:
    """Service for speech recognition using faster-whisper"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._model = None
        self._is_loaded = False
        self._models_dir = Path(__file__).parent.parent / "models"
        self._model_size = os.getenv("WHISPER_MODEL", "base.en")
        self._compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        
        # Supported audio formats
        self._supported_formats = {'.wav', '.mp3', '.m4a', '.ogg', '.webm', '.flac'}
    
    async def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available on the system"""
        try:
            result = await asyncio.create_subprocess_exec(
                "ffmpeg", "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                version_output = stdout.decode('utf-8')
                version_line = version_output.split('\n')[0] if version_output else "Unknown"
                self.logger.info(f"FFmpeg detected: {version_line}")
                return True
            else:
                self.logger.error("FFmpeg not found or not working properly")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to check FFmpeg availability: {e}")
            return False
    
    async def _load_model(self) -> None:
        """Lazy load the Whisper model"""
        if self._is_loaded:
            return
        
        self.logger.info(f"Loading Whisper {self._model_size} model...")
        
        try:
            # Import here to avoid loading dependencies until needed
            from faster_whisper import WhisperModel
            
            # Check FFmpeg availability
            if not await self._check_ffmpeg():
                raise RuntimeError("FFmpeg is required for audio processing but not found. Please install FFmpeg.")
            
            # Load in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self._model = await loop.run_in_executor(
                None,
                lambda: WhisperModel(
                    self._model_size,
                    device="cpu",
                    compute_type=self._compute_type,
                    download_root=str(self._models_dir / "whisper")
                )
            )
            
            self._is_loaded = True
            self.logger.info(f"✓ Whisper {self._model_size} model loaded successfully")
            
        except ImportError as e:
            self.logger.error(f"Missing dependencies for Whisper: {e}")
            raise RuntimeError("Whisper dependencies not installed. Please install: pip install faster-whisper")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    async def _convert_audio_to_wav(self, input_path: Path, output_path: Path) -> bool:
        """Convert audio file to WAV format using FFmpeg"""
        try:
            # Use FFmpeg to convert to 16kHz mono WAV (Whisper's preferred format)
            result = await asyncio.create_subprocess_exec(
                "ffmpeg",
                "-i", str(input_path),
                "-ar", "16000",  # 16kHz sample rate
                "-ac", "1",      # Mono
                "-c:a", "pcm_s16le",  # 16-bit PCM
                "-f", "wav",
                "-y",  # Overwrite output
                str(output_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                self.logger.debug(f"Successfully converted {input_path} to WAV")
                return True
            else:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown FFmpeg error"
                self.logger.error(f"FFmpeg conversion failed: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Audio conversion failed: {e}")
            return False
    
    async def _validate_audio_file(self, file_path: Path) -> Tuple[bool, str]:
        """Validate audio file and get basic info"""
        try:
            # Use FFprobe to get audio info
            result = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(file_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                return False, "Invalid or corrupted audio file"
            
            # Parse JSON output to get duration
            import json
            info = json.loads(stdout.decode('utf-8'))
            
            # Check duration (limit to reasonable length)
            duration = float(info.get('format', {}).get('duration', 0))
            if duration > 300:  # 5 minutes max
                return False, f"Audio file too long: {duration:.1f}s (max 300s)"
            
            if duration < 0.1:  # At least 0.1 seconds
                return False, f"Audio file too short: {duration:.1f}s"
            
            # Check if there are audio streams
            streams = info.get('streams', [])
            audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
            
            if not audio_streams:
                return False, "No audio streams found in file"
            
            return True, f"Valid audio file: {duration:.1f}s"
            
        except Exception as e:
            self.logger.error(f"Audio validation failed: {e}")
            return False, f"Validation error: {str(e)}"
    
    async def transcribe_audio(self, audio_data: bytes, filename: str = None, language: str = "en") -> str:
        """
        Transcribe audio data to text
        
        Args:
            audio_data: Audio file data as bytes
            filename: Original filename (for format detection)
            language: Language code for transcription
            
        Returns:
            Transcribed text
        """
        # Ensure model is loaded
        await self._load_model()
        
        # Create temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Determine file extension
            if filename:
                file_ext = Path(filename).suffix.lower()
                if file_ext not in self._supported_formats:
                    file_ext = '.wav'  # Default fallback
            else:
                file_ext = '.wav'
            
            # Save audio data to temporary file
            input_path = temp_path / f"input{file_ext}"
            with open(input_path, 'wb') as f:
                f.write(audio_data)
            
            # Validate audio file
            is_valid, message = await self._validate_audio_file(input_path)
            if not is_valid:
                raise ValueError(f"Invalid audio file: {message}")
            
            self.logger.info(f"Audio validation: {message}")
            
            # Convert to WAV if needed
            wav_path = temp_path / "converted.wav"
            if file_ext == '.wav':
                wav_path = input_path
            else:
                if not await self._convert_audio_to_wav(input_path, wav_path):
                    raise RuntimeError("Failed to convert audio to WAV format")
            
            # Transcribe using faster-whisper
            try:
                return await self._transcribe_wav(wav_path, language)
            except Exception as e:
                self.logger.error(f"Transcription failed: {e}")
                raise
    
    async def _transcribe_wav(self, wav_path: Path, language: str) -> str:
        """Transcribe WAV file using faster-whisper (runs in thread pool)"""
        try:
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None,
                self._run_transcription,
                str(wav_path),
                language
            )
            
            # Combine all segments into text
            text_segments = []
            for segment in segments:
                text_segments.append(segment.text.strip())
            
            full_text = " ".join(text_segments).strip()
            
            # Log transcription info
            self.logger.info(f"Transcription completed: {len(full_text)} characters")
            self.logger.debug(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
            
            return full_text
            
        except Exception as e:
            self.logger.error(f"Whisper transcription failed: {e}")
            raise
    
    def _run_transcription(self, wav_path: str, language: str):
        """Run the actual transcription (blocking, for thread pool)"""
        try:
            # Set language to None for auto-detection if not specified
            lang_param = language if language and language != "auto" else None
            
            segments, info = self._model.transcribe(
                wav_path,
                language=lang_param,
                beam_size=1,  # Faster transcription
                best_of=1,
                temperature=0.0,
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6,
                condition_on_previous_text=True,
                initial_prompt=None,
                word_timestamps=False,
                prepend_punctuations="\"'([{-",
                append_punctuations="\"'.,:)]}",
            )
            
            return list(segments), info
            
        except Exception as e:
            self.logger.error(f"Whisper model transcription failed: {e}")
            raise
    
    async def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        return sorted(list(self._supported_formats))
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_size": self._model_size,
            "compute_type": self._compute_type,
            "is_loaded": self._is_loaded,
            "supported_languages": ["en", "auto"],  # Simplified for now
            "max_duration_seconds": 300,
            "min_duration_seconds": 0.1
        }
    
    async def health_check(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if the Whisper service is healthy
        
        Returns:
            Tuple of (is_healthy: bool, details: dict)
        """
        details = {
            "model_loaded": self._is_loaded,
            "model_size": self._model_size,
            "compute_type": self._compute_type,
            "ffmpeg_available": False
        }
        
        try:
            # Check FFmpeg availability
            details["ffmpeg_available"] = await self._check_ffmpeg()
            
            if not details["ffmpeg_available"]:
                return False, details
            
            # Try to load the model if not already loaded
            if not self._is_loaded:
                await self._load_model()
            
            details["model_loaded"] = self._is_loaded
            
            # For full health check, we would need a test audio file
            # For now, we consider it healthy if FFmpeg is available and model is loaded
            is_healthy = details["ffmpeg_available"] and details["model_loaded"]
            
            return is_healthy, details
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            details["error"] = str(e)
            return False, details
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self._model:
            try:
                # Clear model from memory
                del self._model
                
                # Force garbage collection
                import gc
                gc.collect()
                
                self.logger.info("Whisper service cleaned up")
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
            finally:
                self._model = None
                self._is_loaded = False
