from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class MediaType(enum.Enum):
    """Types of media files"""
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


class MediaFile(Base):
    """
    Tracks media files associated with specific interactions.
    Integrates with Cloudflare R2 for storage.
    """
    __tablename__ = "media_files"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to interaction
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=False, index=True)
    
    # File metadata
    filename = Column(String, nullable=False)
    original_filename = Column(String)
    media_type = Column(SQLEnum(MediaType), nullable=False)
    file_size = Column(Integer)  # Size in bytes
    mime_type = Column(String)
    
    # Cloudflare R2 integration
    r2_key = Column(String, nullable=False, unique=True)  # R2 object key
    r2_bucket = Column(String, nullable=False)
    r2_url = Column(String)  # Public URL if applicable
    
    # AI processing results (stored as JSON for flexibility)
    transcription = Column(Text)  # For audio files (Whisper output)
    image_analysis = Column(JSON)  # For image files (Vision API output)
    document_analysis = Column(JSON)  # For document files (OCR/parsing output)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_started_at = Column(DateTime(timezone=True))
    processing_error = Column(Text)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    interaction = relationship("Interaction", back_populates="media_files")
    
    def __repr__(self):
        return f"<MediaFile(id={self.id}, filename='{self.filename}', type='{self.media_type.value}')>"
    
    @property
    def is_image(self) -> bool:
        """Check if file is an image"""
        return self.media_type == MediaType.IMAGE
    
    @property
    def is_audio(self) -> bool:
        """Check if file is audio"""
        return self.media_type == MediaType.AUDIO
    
    @property
    def is_document(self) -> bool:
        """Check if file is a document"""
        return self.media_type == MediaType.DOCUMENT
    
    @property
    def needs_processing(self) -> bool:
        """Check if file needs AI processing"""
        return not self.is_processed and not self.processing_error
    
    @property
    def has_processing_error(self) -> bool:
        """Check if processing failed"""
        return bool(self.processing_error)


class FileAttachment(Base):
    """
    General file attachments linked directly to tickets.
    For files that span multiple interactions or are general references.
    """
    __tablename__ = "file_attachments"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to ticket
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    
    # File metadata
    filename = Column(String, nullable=False)
    original_filename = Column(String)
    file_size = Column(Integer)  # Size in bytes
    mime_type = Column(String)
    
    # Cloudflare R2 storage
    r2_key = Column(String, nullable=False, unique=True)  # R2 object key
    r2_bucket = Column(String, nullable=False)
    r2_url = Column(String)  # Public URL if applicable
    
    # Classification
    attachment_type = Column(String)  # 'screenshot', 'log_file', 'manual', 'receipt', 'reference'
    description = Column(Text)
    is_relevant = Column(Boolean, default=True)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="file_attachments")
    
    def __repr__(self):
        return f"<FileAttachment(id={self.id}, ticket_id={self.ticket_id}, filename='{self.filename}')>"
    
    @property
    def is_image_file(self) -> bool:
        """Check if attachment is an image based on mime type"""
        return self.mime_type and self.mime_type.startswith('image/')
    
    @property
    def is_pdf(self) -> bool:
        """Check if attachment is a PDF"""
        return self.mime_type == 'application/pdf'
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0.0