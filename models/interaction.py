from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class InteractionType(enum.Enum):
    """Types of customer interactions"""
    INITIAL = "initial"
    FOLLOWUP = "followup"
    CLARIFICATION = "clarification"
    SOLUTION_FEEDBACK = "solution_feedback"
    ESCALATION = "escalation"


class InteractionChannel(enum.Enum):
    """Communication channels for interactions"""
    EMAIL = "email"
    PHONE = "phone"
    CHAT = "chat"
    WEB_FORM = "web_form"
    SMS = "sms"


class SolutionAttemptResult(enum.Enum):
    """Results of solution attempts"""
    SUCCESSFUL = "successful"
    FAILED = "failed"
    PARTIALLY_SUCCESSFUL = "partially_successful"
    NOT_ATTEMPTED = "not_attempted"


class Interaction(Base):
    """
    Individual customer interactions within a ticket.
    Each interaction can contain multiple media types and AI analysis.
    """
    __tablename__ = "interactions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to ticket
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    
    # Interaction metadata
    interaction_type = Column(SQLEnum(InteractionType), nullable=False)
    channel = Column(SQLEnum(InteractionChannel), nullable=False)
    sequence_number = Column(Integer, nullable=False)  # Order within the ticket
    
    # Content
    raw_content = Column(Text)  # Original customer input
    processed_content = Column(Text)  # Cleaned/processed version
    
    # AI analysis results (JSON structure for flexibility)
    ai_analysis = Column(JSON)  # Complete AI analysis
    intent_classification = Column(JSON)  # What the customer wants to achieve
    emotion_analysis = Column(JSON)  # Customer sentiment and emotion
    entity_extraction = Column(JSON)  # Extracted entities (products, error codes, etc.)
    urgency_score = Column(Float)  # AI-calculated urgency (0-1)
    
    # Multimodal content tracking
    media_types = Column(JSON)  # List of media types present ['image', 'audio']
    has_audio = Column(Boolean, default=False)
    has_images = Column(Boolean, default=False)
    has_documents = Column(Boolean, default=False)
    
    # Solution tracking
    solution_provided = Column(Text)  # Solution given to customer
    solution_attempt_result = Column(SQLEnum(SolutionAttemptResult))
    customer_feedback = Column(Text)  # Customer's feedback on solution
    
    # Processing metadata
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    ticket = relationship("Ticket", back_populates="interactions")
    
    media_files = relationship(
        "MediaFile",
        back_populates="interaction",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Interaction(id={self.id}, ticket_id={self.ticket_id}, type='{self.interaction_type.value}', seq={self.sequence_number})>"
    
    @property
    def has_media(self) -> bool:
        """Check if interaction has any media files"""
        return self.has_audio or self.has_images or self.has_documents
    
    @property
    def is_high_urgency(self) -> bool:
        """Check if interaction is marked as high urgency"""
        return self.urgency_score and self.urgency_score > 0.7
    
    @property
    def needs_followup(self) -> bool:
        """Check if interaction needs followup"""
        return (
            self.interaction_type == InteractionType.SOLUTION_FEEDBACK and
            self.solution_attempt_result in [
                SolutionAttemptResult.FAILED,
                SolutionAttemptResult.PARTIALLY_SUCCESSFUL
            ]
        )