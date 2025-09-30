from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ConversationHistory(Base):
    """
    Aggregated conversation history for context preservation.
    Maintains the flow of the entire support conversation across all interactions.
    """
    __tablename__ = "conversation_history"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to ticket
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    
    # Conversation flow
    conversation_turn = Column(Integer, nullable=False)  # Sequential turn in conversation
    speaker_type = Column(String, nullable=False)  # 'customer', 'ai_agent', 'human_agent', 'system'
    speaker_id = Column(String)  # Identifier for the speaker (email, agent ID, etc.)
    
    # Message content
    message = Column(Text, nullable=False)
    message_type = Column(String)  # 'question', 'answer', 'clarification', 'solution', 'feedback', 'system'
    
    # Context and analysis
    context_window = Column(JSON)  # Reference to previous relevant messages
    ai_confidence = Column(Float)  # AI confidence in the response (0-1)
    requires_human_review = Column(Boolean, default=False)
    
    # Metadata
    interaction_id = Column(Integer, ForeignKey("interactions.id"))  # Link to specific interaction if applicable
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="conversation_history")
    
    def __repr__(self):
        return f"<ConversationHistory(id={self.id}, ticket_id={self.ticket_id}, turn={self.conversation_turn}, speaker='{self.speaker_type}')>"
    
    @property
    def is_from_customer(self) -> bool:
        """Check if message is from customer"""
        return self.speaker_type == "customer"
    
    @property
    def is_from_ai(self) -> bool:
        """Check if message is from AI agent"""
        return self.speaker_type == "ai_agent"
    
    @property
    def is_from_human(self) -> bool:
        """Check if message is from human agent"""
        return self.speaker_type == "human_agent"
    
    @property
    def is_system_message(self) -> bool:
        """Check if message is a system message"""
        return self.speaker_type == "system"
    
    @property
    def is_low_confidence(self) -> bool:
        """Check if AI confidence is below threshold"""
        return (
            self.ai_confidence is not None and
            self.ai_confidence < 0.6
        )