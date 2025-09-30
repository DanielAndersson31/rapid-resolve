from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.media import MediaType


class MediaUploadResponse(BaseModel):
    """Response after uploading a media file"""
    id: int
    filename: str
    media_type: MediaType
    file_size: int
    r2_key: str
    r2_url: Optional[str]
    uploaded_at: datetime
    is_processed: bool = False
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "filename": "screenshot_20250125.png",
                "media_type": "image",
                "file_size": 1024567,
                "r2_key": "tickets/1/interactions/2/20250125_120000_abc123.png",
                "r2_url": "https://files.rapidresolve.com/...",
                "uploaded_at": "2025-01-25T12:00:00Z",
                "is_processed": False
            }
        }
    )


class ImageAnalysisResult(BaseModel):
    """Result of image analysis"""
    content_type: str = Field(..., description="Type of image: screenshot, photo, diagram, etc.")
    detected_text: List[str] = Field(default_factory=list, description="OCR extracted text")
    visual_elements: List[str] = Field(default_factory=list, description="Detected visual elements")
    technical_details: Dict[str, Any] = Field(default_factory=dict, description="Technical details extracted")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance to support case")
    error_indicators: List[str] = Field(default_factory=list, description="Detected error indicators")


class MediaAnalysisResponse(BaseModel):
    """Response after analyzing media file"""
    media_file_id: int
    media_type: MediaType
    analysis_complete: bool
    
    # Image analysis (if image)
    image_analysis: Optional[ImageAnalysisResult] = None
    
    # Audio transcription (if audio)
    transcription: Optional[str] = None
    
    # Document analysis (if document)
    document_analysis: Optional[Dict[str, Any]] = None
    
    # Processing metadata
    processed_at: datetime
    processing_time_seconds: float
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "media_file_id": 1,
                "media_type": "image",
                "analysis_complete": True,
                "image_analysis": {
                    "content_type": "screenshot",
                    "detected_text": ["Error Code: 0x80070057", "Display Driver Stopped Responding"],
                    "visual_elements": ["error_dialog", "windows_interface"],
                    "technical_details": {
                        "error_code": "0x80070057",
                        "application": "Display Driver"
                    },
                    "relevance_score": 0.95,
                    "error_indicators": ["error_dialog", "stop_code"]
                },
                "processed_at": "2025-01-25T12:01:00Z",
                "processing_time_seconds": 2.5
            }
        }
    )


class TranscriptionResponse(BaseModel):
    """Response after transcribing audio"""
    media_file_id: int
    transcription: str = Field(..., description="Full transcription text")
    language: str = Field(default="en", description="Detected language")
    duration_seconds: float = Field(..., description="Audio duration")
    word_count: int
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence")
    
    # Extracted information
    key_phrases: List[str] = Field(default_factory=list, description="Key phrases detected")
    sentiment: Optional[str] = Field(None, description="Overall sentiment")
    
    # Processing metadata
    processed_at: datetime
    processing_time_seconds: float
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "media_file_id": 2,
                "transcription": "Hi, I'm calling about my laptop. The screen keeps flickering and I can't get any work done. I've tried restarting it multiple times but nothing helps.",
                "language": "en",
                "duration_seconds": 15.3,
                "word_count": 28,
                "confidence": 0.92,
                "key_phrases": ["laptop", "screen flickering", "restarting", "nothing helps"],
                "sentiment": "frustrated",
                "processed_at": "2025-01-25T12:02:00Z",
                "processing_time_seconds": 8.1
            }
        }
    )


class FileAttachmentResponse(BaseModel):
    """Response for general file attachment"""
    id: int
    ticket_id: int
    filename: str
    file_size: int
    mime_type: Optional[str]
    r2_url: Optional[str]
    attachment_type: Optional[str]
    description: Optional[str]
    is_relevant: bool
    uploaded_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "ticket_id": 1,
                "filename": "laptop_manual.pdf",
                "file_size": 2048576,
                "mime_type": "application/pdf",
                "r2_url": "https://files.rapidresolve.com/...",
                "attachment_type": "manual",
                "description": "Product manual for reference",
                "is_relevant": True,
                "uploaded_at": "2025-01-25T10:35:00Z"
            }
        }
    )


class BatchUploadRequest(BaseModel):
    """Request for uploading multiple files"""
    ticket_id: int
    interaction_id: Optional[int] = None
    file_descriptions: Optional[Dict[str, str]] = Field(
        None,
        description="Optional descriptions for each file, keyed by filename"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticket_id": 1,
                "interaction_id": 2,
                "file_descriptions": {
                    "screenshot1.png": "Error message screenshot",
                    "logs.txt": "System error logs"
                }
            }
        }
    )


class BatchUploadResponse(BaseModel):
    """Response after batch upload"""
    total_files: int
    successful_uploads: int
    failed_uploads: int
    uploaded_files: List[MediaUploadResponse]
    errors: List[Dict[str, str]] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_files": 3,
                "successful_uploads": 2,
                "failed_uploads": 1,
                "uploaded_files": [],
                "errors": [
                    {
                        "filename": "video.mp4",
                        "error": "File size exceeds maximum limit"
                    }
                ]
            }
        }
    )