from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.ticket import TicketStatus, TicketPriority


class TicketBase(BaseModel):
    """Base ticket schema with common fields"""
    title: str = Field(..., min_length=5, max_length=200, description="Ticket title")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed description")
    customer_email: EmailStr = Field(..., description="Customer email address")
    customer_name: Optional[str] = Field(None, max_length=100, description="Customer name")
    customer_phone: Optional[str] = Field(None, max_length=20, description="Customer phone number")


class TicketCreate(TicketBase):
    """Schema for creating a new ticket"""
    initial_message: Optional[str] = Field(None, description="Initial customer message")
    channel: str = Field(default="web_form", description="Communication channel")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Laptop screen flickering issue",
                "description": "My laptop screen has been flickering for the past two days",
                "customer_email": "customer@example.com",
                "customer_name": "John Doe",
                "customer_phone": "+1234567890",
                "initial_message": "Hi, my laptop screen keeps flickering and I can't work properly",
                "channel": "email"
            }
        }
    )


class TicketUpdate(BaseModel):
    """Schema for updating an existing ticket"""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    customer_name: Optional[str] = Field(None, max_length=100)
    customer_phone: Optional[str] = Field(None, max_length=20)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "in_progress",
                "priority": "high"
            }
        }
    )


class TicketResponse(BaseModel):
    """Schema for ticket response"""
    id: int
    external_id: str
    title: str
    description: Optional[str]
    customer_email: str
    customer_name: Optional[str]
    customer_phone: Optional[str]
    status: TicketStatus
    priority: TicketPriority
    category: Optional[str]
    product_type: Optional[str]
    context_summary: Optional[str]
    customer_satisfaction_score: Optional[float]
    avg_urgency_score: Optional[float]
    escalation_reason: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    first_response_at: Optional[datetime]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    
    # Computed properties
    is_open: bool
    is_resolved: bool
    requires_action: bool
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "external_id": "TKT-ABC123",
                "title": "Laptop screen flickering issue",
                "description": "My laptop screen has been flickering",
                "customer_email": "customer@example.com",
                "customer_name": "John Doe",
                "status": "open",
                "priority": "medium",
                "created_at": "2025-01-25T10:30:00Z",
                "is_open": True,
                "is_resolved": False,
                "requires_action": False
            }
        }
    )


class InteractionSummary(BaseModel):
    """Summary of an interaction for inclusion in ticket context"""
    id: int
    interaction_type: str
    channel: str
    sequence_number: int
    content_preview: str = Field(..., description="First 200 chars of content")
    urgency_score: Optional[float]
    has_media: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ConversationTurn(BaseModel):
    """Individual conversation turn"""
    turn: int
    speaker: str
    message: str
    message_type: Optional[str]
    timestamp: datetime
    ai_confidence: Optional[float]
    
    model_config = ConfigDict(from_attributes=True)


class SolutionAttempt(BaseModel):
    """Solution attempt information"""
    id: int
    content: str
    confidence: float
    timestamp: str
    result: Optional[str]
    customer_feedback: Optional[str]


class TicketWithContext(TicketResponse):
    """Extended ticket response with full context"""
    interactions: List[InteractionSummary] = Field(default_factory=list)
    conversation_flow: List[ConversationTurn] = Field(default_factory=list)
    solution_attempts: List[SolutionAttempt] = Field(default_factory=list)
    
    # Context metrics
    total_interactions: int = 0
    avg_urgency: float = 0.0
    resolution_attempts: int = 0
    time_since_created_hours: float = 0.0
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "external_id": "TKT-ABC123",
                "title": "Laptop screen flickering",
                "status": "in_progress",
                "priority": "high",
                "customer_email": "customer@example.com",
                "total_interactions": 3,
                "avg_urgency": 0.75,
                "resolution_attempts": 1,
                "interactions": [
                    {
                        "id": 1,
                        "interaction_type": "initial",
                        "channel": "email",
                        "sequence_number": 1,
                        "content_preview": "Hi, my laptop screen keeps flickering...",
                        "urgency_score": 0.7,
                        "has_media": False,
                        "created_at": "2025-01-25T10:30:00Z"
                    }
                ],
                "conversation_flow": [
                    {
                        "turn": 1,
                        "speaker": "customer",
                        "message": "My laptop screen is flickering",
                        "message_type": "initial_request",
                        "timestamp": "2025-01-25T10:30:00Z",
                        "ai_confidence": None
                    }
                ]
            }
        }
    )


class TicketListResponse(BaseModel):
    """Response for list of tickets"""
    tickets: List[TicketResponse]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tickets": [],
                "total": 50,
                "page": 1,
                "page_size": 20,
                "has_more": True
            }
        }
    )