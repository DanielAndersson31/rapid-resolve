"""
Database Models Package

All SQLAlchemy ORM models for the RapidResolve ticketing system.
"""

from app.database import Base

# Import all models to ensure they are registered with Base
from models.ticket import Ticket
from models.interaction import Interaction
from models.conversation import ConversationHistory
from models.media import MediaFile, FileAttachment

__all__ = [
    "Base",
    "Ticket",
    "Interaction",
    "ConversationHistory",
    "MediaFile",
    "FileAttachment"
]