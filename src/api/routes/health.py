"""Health check endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import get_async_session
from ...database.schemas import HealthCheckResponse
from ...services.llamaindex_service import get_llamaindex_service
from ...services.privacy_screening import get_privacy_screening_service
from ...services.whisper_service import get_whisper_service
from ...services.language_service import get_language_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=HealthCheckResponse)
async def health_check(db: AsyncSession = Depends(get_async_session)):
    """
    Comprehensive health check for all services.
    
    Returns:
        Health status for all system components
    """
    services = {}
    
    try:
        # Database health
        try:
            await db.execute("SELECT 1")
            services["database"] = "healthy"
        except Exception as e:
            services["database"] = f"error: {str(e)}"
        
        # LlamaIndex service health
        try:
            llamaindex_service = await get_llamaindex_service()
            health = await llamaindex_service.health_check()
            services["llamaindex"] = health.get("overall", "unknown")
        except Exception as e:
            services["llamaindex"] = f"error: {str(e)}"
        
        # Privacy screening service health
        try:
            privacy_service = await get_privacy_screening_service()
            health = await privacy_service.health_check()
            services["privacy_screening"] = health.get("status", "unknown")
        except Exception as e:
            services["privacy_screening"] = f"error: {str(e)}"
        
        # Whisper service health
        try:
            whisper_service = await get_whisper_service()
            health = await whisper_service.health_check()
            services["whisper"] = health.get("overall", "unknown")
        except Exception as e:
            services["whisper"] = f"error: {str(e)}"
        
        # Language service health
        try:
            language_service = get_language_service()
            health = await language_service.health_check()
            services["language_detection"] = health.get("overall", "unknown")
        except Exception as e:
            services["language_detection"] = f"error: {str(e)}"
        
        # Determine overall status
        healthy_services = sum(1 for status in services.values() if status == "healthy")
        total_services = len(services)
        
        if healthy_services == total_services:
            overall_status = "healthy"
        elif healthy_services > 0:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            version="1.0.0",
            services=services,
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.now(timezone.utc),
            version="1.0.0",
            services={"error": str(e)},
        )


@router.get("/database")
async def database_health(db: AsyncSession = Depends(get_async_session)):
    """Check database connectivity."""
    try:
        await db.execute("SELECT 1")
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now(timezone.utc)}


@router.get("/services")
async def services_health():
    """Check all AI services health."""
    services = {}
    
    # Check each service individually
    try:
        llamaindex_service = await get_llamaindex_service()
        services["llamaindex"] = await llamaindex_service.health_check()
    except Exception as e:
        services["llamaindex"] = {"status": "error", "error": str(e)}
    
    try:
        privacy_service = await get_privacy_screening_service()
        services["privacy_screening"] = await privacy_service.health_check()
    except Exception as e:
        services["privacy_screening"] = {"status": "error", "error": str(e)}
    
    try:
        whisper_service = await get_whisper_service()
        services["whisper"] = await whisper_service.health_check()
    except Exception as e:
        services["whisper"] = {"status": "error", "error": str(e)}
    
    try:
        language_service = get_language_service()
        services["language_detection"] = await language_service.health_check()
    except Exception as e:
        services["language_detection"] = {"status": "error", "error": str(e)}
    
    return {
        "timestamp": datetime.now(timezone.utc),
        "services": services,
    }