from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database import Base


class TicketStatus(enum.Enum):
    """Ticket status states"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(enum.Enum):
    """Ticket priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Ticket(Base):
    """
    Core ticket entity tracking the entire customer support journey
    across multiple interactions with context preservation.
    """
    __tablename__ = "tickets"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Unique customer-facing ticket ID
    external_id = Column(String, unique=True, index=True, nullable=False)
    
    # Customer information
    customer_email = Column(String, index=True, nullable=False)
    customer_name = Column(String)
    customer_phone = Column(String)
    
    # Ticket metadata
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.OPEN, nullable=False, index=True)
    priority = Column(SQLEnum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False)
    
    # Categorization
    category = Column(String, index=True)  # electronics, software, hardware, etc.
    product_type = Column(String)  # laptop, phone, accessory
    
    # Context tracking fields
    context_summary = Column(Text)  # AI-generated summary of all interactions
    solution_attempts = Column(JSON)  # Array of solution attempts with results
    
    # Metrics
    customer_satisfaction_score = Column(Float)
    avg_urgency_score = Column(Float)
    
    # Escalation
    escalation_reason = Column(String)
    escalated_to = Column(String)  # Agent or team ID
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    first_response_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    
    # Relationships
    interactions = relationship(
        "Interaction",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="Interaction.sequence_number"
    )
    
    conversation_history = relationship(
        "ConversationHistory",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="ConversationHistory.conversation_turn"
    )
    
    file_attachments = relationship(
        "FileAttachment",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Ticket(id={self.id}, external_id='{self.external_id}', status='{self.status.value}')>"
    
    @property
    def is_open(self) -> bool:
        """Check if ticket is in an open state"""
        return self.status in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.WAITING_CUSTOMER]
    
    @property
    def is_resolved(self) -> bool:
        """Check if ticket is resolved"""
        return self.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]
    
    @property
    def requires_action(self) -> bool:
        """Check if ticket requires immediate action"""
        return (
            self.status == TicketStatus.ESCALATED or
            self.priority == TicketPriority.URGENT or
            (self.avg_urgency_score and self.avg_urgency_score > 0.8)
        )