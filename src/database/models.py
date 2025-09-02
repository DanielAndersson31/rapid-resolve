"""SQLAlchemy ORM models for the ticket system."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid4())


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class Ticket(Base):
    """Ticket model for customer service tickets."""
    
    __tablename__ = "tickets"
    
    # Primary key with entity-specific naming
    ticket_id = Column(String(255), primary_key=True, default=generate_uuid)
    
    # Customer information
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_phone = Column(String(50))
    
    # Ticket details
    subject = Column(String(500), nullable=False)
    status = Column(String(50), default="open", nullable=False)  # open, in_progress, resolved, closed
    priority = Column(String(50), default="medium", nullable=False)  # low, medium, high, urgent
    category = Column(String(100))  # laptops, phones, accessories
    language = Column(String(10), default="en", nullable=False)  # en, sv
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        default=utc_now, 
        onupdate=utc_now, 
        nullable=False
    )
    
    # Relationships
    messages: List["TicketMessage"] = relationship(
        "TicketMessage", 
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketMessage.created_at"
    )
    
    def __repr__(self) -> str:
        return f"<Ticket(ticket_id={self.ticket_id}, subject={self.subject!r})>"


class TicketMessage(Base):
    """Message model for ticket conversation history."""
    
    __tablename__ = "ticket_messages"
    
    # Primary key with entity-specific naming
    message_id = Column(String(255), primary_key=True, default=generate_uuid)
    
    # Foreign key to ticket
    ticket_id = Column(String(255), ForeignKey("tickets.ticket_id"), nullable=False)
    
    # Message details
    sender_type = Column(String(50), nullable=False)  # customer, agent, system
    content = Column(Text, nullable=False)
    original_content = Column(Text)  # Before privacy screening
    is_screened = Column(Boolean, default=False, nullable=False)
    
    # Attachment information (for audio files, etc.)
    attachment_info = Column(JSON)
    
    # Threading support
    parent_message_id = Column(String(255), ForeignKey("ticket_messages.message_id"))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    ticket: Ticket = relationship("Ticket", back_populates="messages")
    parent_message: Optional["TicketMessage"] = relationship(
        "TicketMessage", 
        remote_side=[message_id],
        back_populates="child_messages"
    )
    child_messages: List["TicketMessage"] = relationship(
        "TicketMessage",
        back_populates="parent_message",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<TicketMessage(message_id={self.message_id}, ticket_id={self.ticket_id})>"


# Indexes for performance optimization
Index("idx_tickets_created_at", Ticket.created_at)
Index("idx_tickets_status", Ticket.status)
Index("idx_tickets_category", Ticket.category)
Index("idx_tickets_customer_email", Ticket.customer_email)

Index("idx_ticket_messages_ticket_id", TicketMessage.ticket_id)
Index("idx_ticket_messages_created_at", TicketMessage.created_at)
Index("idx_ticket_messages_sender_type", TicketMessage.sender_type)
Index("idx_ticket_messages_parent_id", TicketMessage.parent_message_id)