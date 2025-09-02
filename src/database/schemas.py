"""Pydantic schemas for API validation and serialization."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, EmailStr, Field, validator


class TicketStatus(str, Enum):
    """Ticket status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Ticket priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ProductCategory(str, Enum):
    """Product category enumeration."""
    LAPTOPS = "laptops"
    PHONES = "phones"
    ACCESSORIES = "accessories"


class SenderType(str, Enum):
    """Message sender type enumeration."""
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"


class Language(str, Enum):
    """Supported language enumeration."""
    ENGLISH = "en"
    SWEDISH = "sv"


# Base schemas
class TicketBase(BaseModel):
    """Base ticket schema with common fields."""
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_email: EmailStr
    customer_phone: Optional[str] = Field(None, max_length=50)
    subject: str = Field(..., min_length=1, max_length=500)
    category: Optional[ProductCategory] = None
    language: Language = Language.ENGLISH
    priority: TicketPriority = TicketPriority.MEDIUM

    @validator('customer_phone')
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) == 0:
            return None
        return v

    @validator('customer_name', 'subject')
    def validate_strings(cls, v: str) -> str:
        return v.strip()


class TicketCreate(TicketBase):
    """Schema for creating a new ticket."""
    content: str = Field(..., min_length=1, max_length=10000)

    @validator('content')
    def validate_content(cls, v: str) -> str:
        return v.strip()


class TicketUpdate(BaseModel):
    """Schema for updating a ticket."""
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    category: Optional[ProductCategory] = None

    @validator('subject')
    def validate_subject(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else None


# Message schemas
class TicketMessageBase(BaseModel):
    """Base message schema with common fields."""
    content: str = Field(..., min_length=1, max_length=10000)
    sender_type: SenderType = SenderType.CUSTOMER
    parent_message_id: Optional[str] = None

    @validator('content')
    def validate_content(cls, v: str) -> str:
        return v.strip()


class TicketMessageCreate(TicketMessageBase):
    """Schema for creating a new ticket message."""
    pass


class TicketMessageResponse(TicketMessageBase):
    """Schema for ticket message response."""
    message_id: str
    ticket_id: str
    is_screened: bool
    attachment_info: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Audio upload schemas
class AudioUpload(BaseModel):
    """Schema for audio upload metadata."""
    ticket_id: str
    language: Language = Language.ENGLISH


class AudioTranscriptionResult(BaseModel):
    """Schema for audio transcription result."""
    text: str
    language: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    duration: float
    file_size: int


# Privacy screening schemas
class PrivacyScreeningResult(BaseModel):
    """Schema for privacy screening result."""
    original_text: str
    screened_text: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    detected_entities: List[str]
    is_safe: bool
    processing_time: float


# Response schemas
class TicketResponse(TicketBase):
    """Schema for ticket response."""
    ticket_id: str
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    messages: List[TicketMessageResponse] = []

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    """Schema for ticket list response."""
    tickets: List[TicketResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class TicketSummaryResponse(BaseModel):
    """Schema for ticket summary response."""
    ticket_id: str
    customer_name: str
    customer_email: str
    subject: str
    status: TicketStatus
    priority: TicketPriority
    category: Optional[ProductCategory]
    language: Language
    message_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# API response wrappers
class APIResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None
    errors: Optional[Dict[str, str]] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = False
    message: str
    errors: Optional[Dict[str, str]] = None
    error_code: Optional[str] = None


# Health check schema
class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]  # service_name: status