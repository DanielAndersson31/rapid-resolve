"""
API Schemas Package

Pydantic models for request/response validation in the API.
"""

from schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketWithContext,
    TicketListResponse
)

from schemas.interaction import (
    InteractionCreate,
    InteractionResponse,
    SolutionRequest,
    SolutionResponse,
    FeedbackRequest
)

from schemas.media import (
    MediaUploadResponse,
    MediaAnalysisResponse,
    TranscriptionResponse
)

__all__ = [
    # Ticket schemas
    "TicketCreate",
    "TicketUpdate",
    "TicketResponse",
    "TicketWithContext",
    "TicketListResponse",
    
    # Interaction schemas
    "InteractionCreate",
    "InteractionResponse",
    "SolutionRequest",
    "SolutionResponse",
    "FeedbackRequest",
    
    # Media schemas
    "MediaUploadResponse",
    "MediaAnalysisResponse",
    "TranscriptionResponse",
]