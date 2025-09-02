"""Audio file validation for Whisper transcription service."""

import logging
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import magic
    PYTHON_MAGIC_AVAILABLE = True
except ImportError:
    PYTHON_MAGIC_AVAILABLE = False

try:
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class AudioValidationError(Exception):
    """Custom exception for audio validation errors."""
    pass


class AudioValidator:
    """Validator for audio files used with Whisper transcription."""
    
    def __init__(self) -> None:
        """Initialize the audio validator."""
        self.settings = get_settings()
        
        # Audio constraints
        self.max_file_size = self.settings.application.max_audio_size_mb * 1024 * 1024
        self.max_duration = self.settings.application.max_audio_duration_seconds
        self.supported_formats = set(self.settings.application.supported_audio_formats)
        
        # MIME type mapping
        self.mime_to_extension = {
            "audio/mpeg": ".mp3",
            "audio/mp3": ".mp3",
            "audio/wav": ".wav",
            "audio/wave": ".wav",
            "audio/x-wav": ".wav",
            "audio/flac": ".flac",
            "audio/x-flac": ".flac",
            "audio/mp4": ".m4a",
            "audio/x-m4a": ".m4a",
            "audio/aac": ".m4a",
        }
        
        # Quality thresholds
        self.min_sample_rate = 8000  # Hz
        self.max_sample_rate = 48000  # Hz
        self.min_bitrate = 32  # kbps
        self.recommended_sample_rate = 16000  # Hz for Whisper
    
    def validate_file_existence(self, file_path: Path) -> None:
        """
        Validate that the file exists and is readable.
        
        Args:
            file_path: Path to audio file
            
        Raises:
            AudioValidationError: If file doesn't exist or isn't readable
        """
        if not file_path.exists():
            raise AudioValidationError(f"Audio file not found: {file_path}")
        
        if not file_path.is_file():
            raise AudioValidationError(f"Path is not a file: {file_path}")
        
        try:
            with open(file_path, "rb") as f:
                f.read(1024)  # Try to read first 1KB
        except (IOError, OSError) as e:
            raise AudioValidationError(f"Cannot read audio file: {e}")
    
    def validate_file_size(self, file_path: Path) -> int:
        """
        Validate file size against limits.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            File size in bytes
            
        Raises:
            AudioValidationError: If file is too large
        """
        file_size = file_path.stat().st_size
        
        if file_size == 0:
            raise AudioValidationError("Audio file is empty")
        
        if file_size > self.max_file_size:
            max_mb = self.max_file_size / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            raise AudioValidationError(
                f"File size {actual_mb:.1f}MB exceeds maximum {max_mb:.1f}MB"
            )
        
        return file_size
    
    def validate_file_format(self, file_path: Path) -> str:
        """
        Validate file format and return the detected extension.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Detected file extension
            
        Raises:
            AudioValidationError: If format is not supported
        """
        # Check file extension
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_formats:
            raise AudioValidationError(
                f"Unsupported file extension '{file_extension}'. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )
        
        # Additional MIME type validation if available
        if PYTHON_MAGIC_AVAILABLE:
            try:
                mime = magic.from_file(str(file_path), mime=True)
                if mime in self.mime_to_extension:
                    detected_ext = self.mime_to_extension[mime]
                    if detected_ext != file_extension:
                        logger.warning(
                            f"Extension mismatch: file has '{file_extension}' "
                            f"but MIME type suggests '{detected_ext}'"
                        )
                else:
                    logger.warning(f"Unknown MIME type: {mime}")
            except Exception as e:
                logger.warning(f"MIME type detection failed: {e}")
        
        # Use mimetypes as fallback
        else:
            mime, _ = mimetypes.guess_type(str(file_path))
            if mime and mime not in self.mime_to_extension:
                logger.warning(f"Unsupported MIME type: {mime}")
        
        return file_extension
    
    def get_audio_metadata(self, file_path: Path) -> Dict[str, any]:
        """
        Extract audio metadata using mutagen.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio metadata
        """
        metadata = {
            "duration": None,
            "bitrate": None,
            "sample_rate": None,
            "channels": None,
            "format": None,
            "metadata_available": False,
        }
        
        if not MUTAGEN_AVAILABLE:
            logger.debug("Mutagen not available, skipping metadata extraction")
            return metadata
        
        try:
            audio_file = MutagenFile(str(file_path))
            
            if audio_file is None:
                logger.warning(f"Could not read audio metadata from {file_path}")
                return metadata
            
            info = audio_file.info
            if info:
                metadata.update({
                    "duration": getattr(info, "length", None),
                    "bitrate": getattr(info, "bitrate", None),
                    "sample_rate": getattr(info, "sample_rate", None),
                    "channels": getattr(info, "channels", None),
                    "format": info.__class__.__name__,
                    "metadata_available": True,
                })
            
        except Exception as e:
            logger.warning(f"Failed to extract audio metadata: {e}")
        
        return metadata
    
    def validate_audio_quality(self, metadata: Dict[str, any]) -> List[str]:
        """
        Validate audio quality parameters.
        
        Args:
            metadata: Audio metadata dictionary
            
        Returns:
            List of quality warnings
        """
        warnings = []
        
        # Check duration
        duration = metadata.get("duration")
        if duration:
            if duration > self.max_duration:
                max_minutes = self.max_duration / 60
                actual_minutes = duration / 60
                warnings.append(
                    f"Duration {actual_minutes:.1f}min exceeds maximum {max_minutes:.1f}min"
                )
            elif duration < 1:
                warnings.append("Audio duration is less than 1 second")
        
        # Check sample rate
        sample_rate = metadata.get("sample_rate")
        if sample_rate:
            if sample_rate < self.min_sample_rate:
                warnings.append(
                    f"Low sample rate {sample_rate}Hz (minimum: {self.min_sample_rate}Hz)"
                )
            elif sample_rate > self.max_sample_rate:
                warnings.append(
                    f"High sample rate {sample_rate}Hz (maximum: {self.max_sample_rate}Hz)"
                )
            elif sample_rate != self.recommended_sample_rate:
                warnings.append(
                    f"Sample rate {sample_rate}Hz differs from Whisper optimal {self.recommended_sample_rate}Hz"
                )
        
        # Check bitrate
        bitrate = metadata.get("bitrate")
        if bitrate and bitrate < self.min_bitrate * 1000:  # Convert to bps
            warnings.append(f"Low bitrate {bitrate//1000}kbps (minimum: {self.min_bitrate}kbps)")
        
        # Check channels
        channels = metadata.get("channels")
        if channels and channels > 2:
            warnings.append(f"Multi-channel audio ({channels} channels) will be converted to mono")
        
        return warnings
    
    def validate_audio_file(self, file_path: Path) -> Dict[str, any]:
        """
        Comprehensive audio file validation.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Validation result dictionary
            
        Raises:
            AudioValidationError: If validation fails
        """
        result = {
            "is_valid": False,
            "file_path": str(file_path),
            "file_size": 0,
            "format": None,
            "metadata": {},
            "quality_warnings": [],
            "validation_errors": [],
        }
        
        try:
            # Basic file validation
            self.validate_file_existence(file_path)
            result["file_size"] = self.validate_file_size(file_path)
            result["format"] = self.validate_file_format(file_path)
            
            # Extract metadata
            result["metadata"] = self.get_audio_metadata(file_path)
            
            # Validate quality
            result["quality_warnings"] = self.validate_audio_quality(result["metadata"])
            
            # Check for critical duration issues
            duration = result["metadata"].get("duration")
            if duration and duration > self.max_duration:
                raise AudioValidationError(
                    f"Audio duration {duration:.1f}s exceeds maximum {self.max_duration}s"
                )
            
            result["is_valid"] = True
            
        except AudioValidationError as e:
            result["validation_errors"].append(str(e))
            result["is_valid"] = False
        except Exception as e:
            result["validation_errors"].append(f"Unexpected validation error: {str(e)}")
            result["is_valid"] = False
        
        return result
    
    def validate_audio_bytes(self, audio_data: bytes, filename: str) -> Dict[str, any]:
        """
        Validate audio data from bytes.
        
        Args:
            audio_data: Audio data as bytes
            filename: Original filename for format detection
            
        Returns:
            Validation result dictionary
        """
        result = {
            "is_valid": False,
            "filename": filename,
            "data_size": len(audio_data),
            "format": None,
            "validation_errors": [],
        }
        
        try:
            # Check data size
            if len(audio_data) == 0:
                raise AudioValidationError("Audio data is empty")
            
            if len(audio_data) > self.max_file_size:
                max_mb = self.max_file_size / (1024 * 1024)
                actual_mb = len(audio_data) / (1024 * 1024)
                raise AudioValidationError(
                    f"Data size {actual_mb:.1f}MB exceeds maximum {max_mb:.1f}MB"
                )
            
            # Check format based on filename
            file_path = Path(filename)
            file_extension = file_path.suffix.lower()
            
            if file_extension not in self.supported_formats:
                raise AudioValidationError(
                    f"Unsupported file extension '{file_extension}'. "
                    f"Supported formats: {', '.join(self.supported_formats)}"
                )
            
            result["format"] = file_extension
            
            # Additional validation could be done by writing to temp file
            # and using mutagen, but we'll keep it simple for now
            
            result["is_valid"] = True
            
        except AudioValidationError as e:
            result["validation_errors"].append(str(e))
            result["is_valid"] = False
        except Exception as e:
            result["validation_errors"].append(f"Unexpected validation error: {str(e)}")
            result["is_valid"] = False
        
        return result
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported audio formats.
        
        Returns:
            List of supported file extensions
        """
        return list(self.supported_formats)
    
    def get_format_info(self) -> Dict[str, Dict[str, any]]:
        """
        Get detailed information about supported formats.
        
        Returns:
            Dictionary with format information
        """
        return {
            ".mp3": {
                "name": "MP3 (MPEG-1 Audio Layer III)",
                "mime_types": ["audio/mpeg", "audio/mp3"],
                "description": "Widely supported compressed audio format",
                "recommended": True,
            },
            ".wav": {
                "name": "WAV (Waveform Audio File Format)",
                "mime_types": ["audio/wav", "audio/wave", "audio/x-wav"],
                "description": "Uncompressed audio format, high quality",
                "recommended": True,
            },
            ".flac": {
                "name": "FLAC (Free Lossless Audio Codec)",
                "mime_types": ["audio/flac", "audio/x-flac"],
                "description": "Lossless compressed audio format",
                "recommended": False,
            },
            ".m4a": {
                "name": "M4A (MPEG-4 Audio)",
                "mime_types": ["audio/mp4", "audio/x-m4a", "audio/aac"],
                "description": "MPEG-4 audio format, used by iTunes",
                "recommended": True,
            },
        }
    
    def get_constraints(self) -> Dict[str, any]:
        """
        Get audio validation constraints.
        
        Returns:
            Dictionary with validation constraints
        """
        return {
            "max_file_size_mb": self.max_file_size / (1024 * 1024),
            "max_duration_seconds": self.max_duration,
            "supported_formats": list(self.supported_formats),
            "min_sample_rate": self.min_sample_rate,
            "max_sample_rate": self.max_sample_rate,
            "recommended_sample_rate": self.recommended_sample_rate,
            "min_bitrate_kbps": self.min_bitrate,
        }


# Global validator instance
_audio_validator: Optional[AudioValidator] = None


def get_audio_validator() -> AudioValidator:
    """Get the global audio validator instance."""
    global _audio_validator
    if _audio_validator is None:
        _audio_validator = AudioValidator()
    return _audio_validator