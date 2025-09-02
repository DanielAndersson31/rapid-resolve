"""
Whisper transcription service for local speech-to-text processing.

Supports English and Swedish languages with appropriate model selection.
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

import whisper
import torch

from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class WhisperService:
    """Service for audio transcription using OpenAI Whisper models."""
    
    def __init__(self) -> None:
        """Initialize the Whisper service."""
        self.settings = get_settings()
        
        # Model configuration
        self.max_duration = self.settings.application.max_audio_duration_seconds
        self.max_file_size = self.settings.application.max_audio_size_mb * 1024 * 1024
        
        # Model cache
        self._models: Dict[str, Any] = {}
        self._device = self._get_device()
        
        logger.info(f"Whisper service initialized with device: {self._device}")
    
    def _get_device(self) -> str:
        """Determine the best device for Whisper processing."""
        device_setting = self.settings.whisper.device
        
        if device_setting == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        
        return device_setting
    
    async def _load_model(self, language: str) -> Any:
        """
        Load the appropriate Whisper model for the given language.
        
        Args:
            language: Language code (en, sv)
            
        Returns:
            Loaded Whisper model
        """
        if language == "en":
            model_name = self.settings.whisper.english_model
        elif language == "sv":
            model_name = self.settings.whisper.swedish_model
        else:
            # Default to English model for unknown languages
            model_name = self.settings.whisper.english_model
            logger.warning(f"Unknown language {language}, using English model")
        
        # Check if model is already loaded
        cache_key = f"{model_name}_{self._device}"
        if cache_key not in self._models:
            logger.info(f"Loading Whisper model: {model_name} on device: {self._device}")
            
            try:
                # Load model in executor to avoid blocking
                loop = asyncio.get_event_loop()
                model = await loop.run_in_executor(
                    None,
                    lambda: whisper.load_model(model_name, device=self._device)
                )
                self._models[cache_key] = model
                logger.info(f"Model {model_name} loaded successfully")
                
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                raise
        
        return self._models[cache_key]
    
    async def _validate_audio_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate audio file format, size, and duration.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Validation result with metadata
            
        Raises:
            ValueError: If file is invalid
        """
        if not file_path.exists():
            raise ValueError(f"Audio file not found: {file_path}")
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            raise ValueError(
                f"File size {file_size} bytes exceeds maximum {self.max_file_size} bytes"
            )
        
        # Check file extension
        supported_formats = self.settings.application.supported_audio_formats
        file_extension = file_path.suffix.lower()
        if file_extension not in supported_formats:
            raise ValueError(
                f"Unsupported audio format {file_extension}. "
                f"Supported formats: {supported_formats}"
            )
        
        # Get audio metadata using mutagen
        try:
            from mutagen import File as MutagenFile
            
            audio_file = MutagenFile(file_path)
            if audio_file is None:
                raise ValueError("Could not read audio file metadata")
            
            duration = getattr(audio_file.info, 'length', 0)
            
            # Check duration
            if duration > self.max_duration:
                raise ValueError(
                    f"Audio duration {duration:.1f}s exceeds maximum {self.max_duration}s"
                )
            
            return {
                "file_size": file_size,
                "duration": duration,
                "format": file_extension,
                "bitrate": getattr(audio_file.info, 'bitrate', None),
                "channels": getattr(audio_file.info, 'channels', None),
            }
            
        except ImportError:
            logger.warning("Mutagen not available, skipping detailed audio validation")
            return {
                "file_size": file_size,
                "duration": None,
                "format": file_extension,
            }
        except Exception as e:
            logger.warning(f"Audio metadata extraction failed: {e}")
            return {
                "file_size": file_size,
                "duration": None,
                "format": file_extension,
            }
    
    def _calculate_average_confidence(self, segments: list) -> float:
        """
        Calculate average confidence score from Whisper segments.
        
        Args:
            segments: List of transcription segments
            
        Returns:
            Average confidence score
        """
        if not segments:
            return 0.0
        
        # Whisper doesn't provide confidence scores in all segments
        # We'll use a heuristic based on segment characteristics
        total_confidence = 0.0
        valid_segments = 0
        
        for segment in segments:
            # Use presence of punctuation and length as confidence indicators
            text = segment.get("text", "").strip()
            if not text:
                continue
            
            # Base confidence
            confidence = 0.7
            
            # Boost for longer segments (more context)
            if len(text) > 20:
                confidence += 0.1
            
            # Boost for proper punctuation
            if any(punct in text for punct in ['.', '!', '?', ',']):
                confidence += 0.1
            
            # Reduce for excessive repetition
            words = text.lower().split()
            if len(words) > 1:
                unique_ratio = len(set(words)) / len(words)
                confidence *= unique_ratio
            
            total_confidence += min(confidence, 1.0)
            valid_segments += 1
        
        return total_confidence / valid_segments if valid_segments > 0 else 0.5
    
    async def transcribe_audio(
        self, 
        file_path: Path, 
        language: str = "en",
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.
        
        Args:
            file_path: Path to audio file
            language: Language code (en, sv)
            task: Task type ("transcribe" or "translate")
            
        Returns:
            Transcription result with metadata
        """
        start_time = time.time()
        
        try:
            # Validate audio file
            file_metadata = await self._validate_audio_file(file_path)
            
            # Load appropriate model
            model = await self._load_model(language)
            
            # Perform transcription in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            transcription_options = {
                "language": language if language != "auto" else None,
                "task": task,
                "fp16": False if self._device == "cpu" else True,
            }
            
            result = await loop.run_in_executor(
                None,
                lambda: model.transcribe(str(file_path), **transcription_options)
            )
            
            # Calculate confidence score
            confidence = self._calculate_average_confidence(result.get("segments", []))
            
            # Extract processing metadata
            processing_time = time.time() - start_time
            
            # Clean up transcribed text
            transcribed_text = result["text"].strip()
            
            return {
                "text": transcribed_text,
                "language": result.get("language", language),
                "segments": result.get("segments", []),
                "confidence": confidence,
                "processing_time": processing_time,
                "file_metadata": file_metadata,
                "model_used": model.get("name", "unknown"),
                "device_used": self._device,
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Audio transcription failed: {e}")
            
            return {
                "text": "",
                "language": language,
                "segments": [],
                "confidence": 0.0,
                "processing_time": processing_time,
                "error": str(e),
                "file_metadata": {},
            }
    
    async def transcribe_audio_stream(
        self,
        audio_data: bytes,
        language: str = "en",
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        Transcribe audio from bytes data.
        
        Args:
            audio_data: Audio data as bytes
            language: Language code (en, sv)
            task: Task type ("transcribe" or "translate")
            
        Returns:
            Transcription result
        """
        # Write audio data to temporary file
        temp_dir = self.settings.file_storage.temp_dir
        temp_file = temp_dir / f"temp_audio_{int(time.time())}.wav"
        
        try:
            # Write audio data to temporary file
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            
            # Transcribe the temporary file
            result = await self.transcribe_audio(temp_file, language, task)
            
            return result
            
        finally:
            # Clean up temporary file
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file}: {e}")
    
    async def get_supported_languages(self) -> Dict[str, str]:
        """
        Get list of supported languages.
        
        Returns:
            Dictionary of language codes and names
        """
        # Based on Whisper's supported languages
        return {
            "en": "English",
            "sv": "Swedish",
            "es": "Spanish",
            "fr": "French", 
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            # Add more as needed
        }
    
    async def health_check(self) -> Dict[str, str]:
        """
        Perform health check on Whisper service.
        
        Returns:
            Health status information
        """
        try:
            status = {
                "device": self._device,
                "models_loaded": len(self._models),
                "cuda_available": str(torch.cuda.is_available()),
            }
            
            # Check if we can load a model
            try:
                await self._load_model("en")
                status["model_loading"] = "healthy"
                status["overall"] = "healthy"
            except Exception as e:
                status["model_loading"] = f"error: {str(e)}"
                status["overall"] = "degraded"
            
            return status
            
        except Exception as e:
            logger.error(f"Whisper health check failed: {e}")
            return {
                "overall": "unhealthy",
                "error": str(e)
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about loaded models.
        
        Returns:
            Model information
        """
        return {
            "loaded_models": list(self._models.keys()),
            "device": self._device,
            "english_model": self.settings.whisper.english_model,
            "swedish_model": self.settings.whisper.swedish_model,
            "max_duration": self.max_duration,
            "max_file_size": self.max_file_size,
            "supported_formats": self.settings.application.supported_audio_formats,
        }


# Global service instance
_whisper_service: Optional[WhisperService] = None


async def get_whisper_service() -> WhisperService:
    """Get the global Whisper service instance."""
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = WhisperService()
    return _whisper_service