"""Audio transcription API routes."""

import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import get_async_session
from ...database.schemas import APIResponse, AudioTranscriptionResult, SenderType
from ...services.ticket_service import TicketService
from ...services.whisper_service import get_whisper_service
from ...validators.audio import get_audio_validator
from ...utils.exceptions import AudioTranscriptionError, ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/{ticket_id}/transcribe",
    response_model=APIResponse,
    summary="Transcribe audio and add to ticket",
    description="Upload audio file, transcribe it, and add the transcription as a message to the ticket"
)
async def transcribe_audio_for_ticket(
    ticket_id: str,
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form("en", description="Language code (en, sv)"),
    task: str = Form("transcribe", description="Task type (transcribe or translate)"),
    db: AsyncSession = Depends(get_async_session)
) -> APIResponse:
    """Transcribe audio file and add to ticket conversation."""
    temp_file_path = None
    
    try:
        # Validate audio file
        audio_validator = get_audio_validator()
        
        # Read audio data
        audio_data = await audio_file.read()
        
        # Validate audio bytes
        validation_result = audio_validator.validate_audio_bytes(
            audio_data, 
            audio_file.filename or "audio.wav"
        )
        
        if not validation_result["is_valid"]:
            raise ValidationError(
                message="Invalid audio file",
                error_code="INVALID_AUDIO_FILE",
                details=validation_result
            )
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix=validation_result["format"],
            delete=False
        )
        temp_file_path = Path(temp_file.name)
        
        # Write audio data to temporary file
        temp_file.write(audio_data)
        temp_file.close()
        
        # Validate the temporary file
        file_validation = audio_validator.validate_audio_file(temp_file_path)
        if not file_validation["is_valid"]:
            raise ValidationError(
                message="Audio file validation failed",
                error_code="AUDIO_VALIDATION_FAILED",
                details=file_validation
            )
        
        # Transcribe audio
        whisper_service = await get_whisper_service()
        transcription_result = await whisper_service.transcribe_audio(
            file_path=temp_file_path,
            language=language,
            task=task
        )
        
        if not transcription_result.get("text"):
            raise AudioTranscriptionError(
                message="Audio transcription produced no text",
                error_code="TRANSCRIPTION_EMPTY",
                details=transcription_result
            )
        
        # Check if ticket exists and add message
        ticket_service = TicketService(db)
        
        # Prepare attachment info
        attachment_info = {
            "original_filename": audio_file.filename,
            "file_size": len(audio_data),
            "duration": transcription_result.get("duration"),
            "transcription_confidence": transcription_result.get("confidence"),
            "language_detected": transcription_result.get("language"),
            "model_used": transcription_result.get("model_used"),
            "processing_time": transcription_result.get("processing_time"),
        }
        
        # Add transcribed message to ticket
        from ...database.schemas import TicketMessageCreate
        
        message_data = TicketMessageCreate(
            content=transcription_result["text"],
            sender_type=SenderType.CUSTOMER,
        )
        
        message = await ticket_service.add_message(
            ticket_id=ticket_id,
            message_data=message_data,
            sender_type=SenderType.CUSTOMER,
            attachment_info=attachment_info
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Ticket not found",
                    "error_code": "TICKET_NOT_FOUND",
                }
            )
        
        logger.info(f"Transcribed audio for ticket {ticket_id}")
        
        # Prepare response data
        response_data = {
            "transcription": {
                "text": transcription_result["text"],
                "language": transcription_result.get("language"),
                "confidence": transcription_result.get("confidence"),
                "duration": transcription_result.get("duration"),
            },
            "message": message.model_dump(),
            "file_info": {
                "filename": audio_file.filename,
                "size": len(audio_data),
                "format": validation_result["format"],
            }
        }
        
        return APIResponse(
            success=True,
            message="Audio transcribed and added to ticket successfully",
            data=response_data
        )
        
    except ValidationError as e:
        logger.warning(f"Audio validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": e.message,
                "error_code": e.error_code,
                "details": e.details,
            }
        )
    except AudioTranscriptionError as e:
        logger.error(f"Audio transcription error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "message": e.message,
                "error_code": e.error_code,
                "details": e.details,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to transcribe audio for ticket {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Audio transcription failed",
                "error_code": "TRANSCRIPTION_FAILED",
            }
        )
    finally:
        # Clean up temporary file
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")


@router.post(
    "/transcribe",
    response_model=APIResponse,
    summary="Transcribe audio file",
    description="Transcribe an audio file without adding to a ticket"
)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form("en", description="Language code (en, sv)"),
    task: str = Form("transcribe", description="Task type (transcribe or translate)"),
) -> APIResponse:
    """Transcribe audio file without adding to ticket."""
    temp_file_path = None
    
    try:
        # Validate audio file
        audio_validator = get_audio_validator()
        
        # Read audio data
        audio_data = await audio_file.read()
        
        # Validate audio bytes
        validation_result = audio_validator.validate_audio_bytes(
            audio_data, 
            audio_file.filename or "audio.wav"
        )
        
        if not validation_result["is_valid"]:
            raise ValidationError(
                message="Invalid audio file",
                error_code="INVALID_AUDIO_FILE",
                details=validation_result
            )
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix=validation_result["format"],
            delete=False
        )
        temp_file_path = Path(temp_file.name)
        
        # Write audio data to temporary file
        temp_file.write(audio_data)
        temp_file.close()
        
        # Validate the temporary file
        file_validation = audio_validator.validate_audio_file(temp_file_path)
        if not file_validation["is_valid"]:
            raise ValidationError(
                message="Audio file validation failed",
                error_code="AUDIO_VALIDATION_FAILED",
                details=file_validation
            )
        
        # Transcribe audio
        whisper_service = await get_whisper_service()
        transcription_result = await whisper_service.transcribe_audio(
            file_path=temp_file_path,
            language=language,
            task=task
        )
        
        if not transcription_result.get("text"):
            raise AudioTranscriptionError(
                message="Audio transcription produced no text",
                error_code="TRANSCRIPTION_EMPTY",
                details=transcription_result
            )
        
        logger.info("Audio transcription completed")
        
        # Prepare response data
        response_data = {
            "transcription": {
                "text": transcription_result["text"],
                "language": transcription_result.get("language"),
                "confidence": transcription_result.get("confidence"),
                "duration": transcription_result.get("duration"),
                "segments": transcription_result.get("segments", []),
            },
            "file_info": {
                "filename": audio_file.filename,
                "size": len(audio_data),
                "format": validation_result["format"],
            },
            "processing_info": {
                "processing_time": transcription_result.get("processing_time"),
                "model_used": transcription_result.get("model_used"),
                "device_used": transcription_result.get("device_used"),
            }
        }
        
        return APIResponse(
            success=True,
            message="Audio transcribed successfully",
            data=response_data
        )
        
    except ValidationError as e:
        logger.warning(f"Audio validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": e.message,
                "error_code": e.error_code,
                "details": e.details,
            }
        )
    except AudioTranscriptionError as e:
        logger.error(f"Audio transcription error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "message": e.message,
                "error_code": e.error_code,
                "details": e.details,
            }
        )
    except Exception as e:
        logger.error(f"Failed to transcribe audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Audio transcription failed",
                "error_code": "TRANSCRIPTION_FAILED",
            }
        )
    finally:
        # Clean up temporary file
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")