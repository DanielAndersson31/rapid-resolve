from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.interaction import InteractionType, InteractionChannel, SolutionAttemptResult


class InteractionCreate(BaseModel):
    """Schema for creating a new interaction"""
    content: str = Field(..., min_length=1, max_length=10000, description="Interaction content")
    interaction_type: InteractionType = Field(default=InteractionType.FOLLOWUP)
    channel: InteractionChannel = Field(default=InteractionChannel.EMAIL)
    media_file_ids: Optional[List[int]] = Field(default=None, description="IDs of uploaded media files")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "I tried restarting the laptop but the screen is still flickering",
                "interaction_type": "followup",
                "channel": "email",
                "media_file_ids": [1, 2]
            }
        }
    )


class AIAnalysisResult(BaseModel):
    """AI analysis results from an interaction"""
    intent: Optional[Dict[str, Any]] = None
    emotion: Optional[Dict[str, Any]] = None
    entities: Optional[Dict[str, Any]] = None
    urgency_score: Optional[float] = None


class MediaFileInfo(BaseModel):
    """Information about media files in an interaction"""
    id: int
    filename: str
    media_type: str
    file_size: int
    r2_url: Optional[str]
    is_processed: bool
    
    model_config = ConfigDict(from_attributes=True)


class InteractionResponse(BaseModel):
    """Schema for interaction response"""
    id: int
    ticket_id: int
    interaction_type: InteractionType
    channel: InteractionChannel
    sequence_number: int
    raw_content: Optional[str]
    processed_content: Optional[str]
    
    # AI analysis
    ai_analysis: Optional[Dict[str, Any]]
    intent_classification: Optional[Dict[str, Any]]
    emotion_analysis: Optional[Dict[str, Any]]
    entity_extraction: Optional[Dict[str, Any]]
    urgency_score: Optional[float]
    
    # Media tracking
    has_audio: bool = False
    has_images: bool = False
    has_documents: bool = False
    media_files: Optional[List[MediaFileInfo]] = None
    
    # Solution tracking
    solution_provided: Optional[str]
    solution_attempt_result: Optional[SolutionAttemptResult]
    customer_feedback: Optional[str]
    
    # Metadata
    is_processed: bool
    created_at: datetime
    processed_at: Optional[datetime]
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 2,
                "ticket_id": 1,
                "interaction_type": "followup",
                "channel": "email",
                "sequence_number": 2,
                "processed_content": "I tried restarting but still flickering",
                "urgency_score": 0.75,
                "has_images": True,
                "is_processed": True,
                "created_at": "2025-01-25T11:00:00Z"
            }
        }
    )


class SolutionRequest(BaseModel):
    """Request for AI-generated solution"""
    additional_context: Optional[str] = Field(None, max_length=1000, description="Additional context for solution")
    prefer_simple_solution: bool = Field(default=True, description="Prefer simpler solutions")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "additional_context": "Customer mentioned they recently updated graphics drivers",
                "prefer_simple_solution": True
            }
        }
    )


class SolutionStep(BaseModel):
    """Individual step in a solution"""
    step_number: int
    instruction: str
    estimated_time: Optional[str]
    requires_restart: bool = False


class SolutionResponse(BaseModel):
    """AI-generated solution response"""
    solution_id: int
    content: str = Field(..., description="Full solution text")
    steps: List[str] = Field(..., description="Step-by-step instructions")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score")
    estimated_difficulty: str = Field(..., description="Difficulty level: easy, medium, hard")
    requires_escalation: bool = Field(default=False)
    escalation_reason: Optional[str] = None
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites needed")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "solution_id": 1,
                "content": "Based on your description, this appears to be a graphics driver issue...",
                "steps": [
                    "Open Device Manager",
                    "Locate Display Adapters",
                    "Right-click your graphics card",
                    "Select 'Update Driver'"
                ],
                "confidence": 0.85,
                "estimated_difficulty": "medium",
                "requires_escalation": False,
                "prerequisites": ["Administrator access", "Internet connection"]
            }
        }
    )


class FeedbackRequest(BaseModel):
    """Customer feedback on a solution"""
    solution_id: int = Field(..., description="ID of the solution being reviewed")
    result: SolutionAttemptResult = Field(..., description="Outcome of the solution attempt")
    feedback_text: Optional[str] = Field(None, max_length=2000, description="Detailed feedback")
    specific_issues: Optional[List[str]] = Field(None, description="Specific issues encountered")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "solution_id": 1,
                "result": "failed",
                "feedback_text": "I followed all the steps but the screen is still flickering",
                "specific_issues": [
                    "Driver update completed but no change",
                    "Flickering persists even after restart"
                ]
            }
        }
    )


class FeedbackResponse(BaseModel):
    """Response after submitting feedback"""
    message: str
    feedback_recorded: bool
    next_steps: Optional[str]
    escalation_triggered: bool = False
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Thank you for your feedback",
                "feedback_recorded": True,
                "next_steps": "We'll analyze alternative solutions based on your feedback",
                "escalation_triggered": False
            }
        }
    )