"""Custom exception classes for the application."""

from typing import Optional, Dict, Any


class BaseCustomException(Exception):
    """Base exception class for custom application exceptions."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationError(BaseCustomException):
    """Exception raised for validation errors."""
    pass


class PrivacyScreeningError(BaseCustomException):
    """Exception raised for privacy screening failures."""
    pass


class AudioTranscriptionError(BaseCustomException):
    """Exception raised for audio transcription failures."""
    pass


class TicketNotFoundError(BaseCustomException):
    """Exception raised when a ticket is not found."""
    pass


class ServiceUnavailableError(BaseCustomException):
    """Exception raised when a service is unavailable."""
    pass


class ConfigurationError(BaseCustomException):
    """Exception raised for configuration errors."""
    pass


class LlamaIndexError(BaseCustomException):
    """Exception raised for LlamaIndex-related errors."""
    pass