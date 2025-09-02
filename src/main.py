"""FastAPI application entry point for the multimodal customer service AI system."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from .api.routes.health import router as health_router
from .api.routes.tickets import router as tickets_router
from .api.routes.audio import router as audio_router
from .config.settings import get_settings
from .database.connection import init_database, close_database
from .utils.logging import setup_logging, LoggingContextManager
from .utils.exceptions import BaseCustomException

# Configure logging first
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting multimodal customer service AI system")
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized")
        
        # Initialize services (they will be lazy-loaded on first use)
        logger.info("Services ready for initialization")
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    try:
        await close_database()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Multimodal Customer Service AI",
    description="AI-powered customer service system with privacy screening and multimodal support",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add middleware
if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*"] if settings.debug else ["localhost", "127.0.0.1"]
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Add correlation ID and request logging."""
    # Generate correlation ID
    correlation_id = request.headers.get("X-Correlation-ID")
    
    with LoggingContextManager(correlation_id) as corr_id:
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = corr_id
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "response_size": response.headers.get("content-length"),
            }
        )
        
        return response


@app.exception_handler(BaseCustomException)
async def custom_exception_handler(request: Request, exc: BaseCustomException):
    """Handle custom application exceptions."""
    logger.error(
        f"Custom exception: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )
    
    # Don't expose internal errors in production
    if settings.debug:
        error_detail = str(exc)
    else:
        error_detail = "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": error_detail,
            "error_code": "INTERNAL_ERROR",
        }
    )


# Include routers
app.include_router(health_router, prefix="/api/v1/health", tags=["Health"])
app.include_router(tickets_router, prefix="/api/v1/tickets", tags=["Tickets"])
app.include_router(audio_router, prefix="/api/v1/audio", tags=["Audio"])


@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "name": "Multimodal Customer Service AI",
        "version": "1.0.0",
        "description": "AI-powered customer service with privacy screening",
        "status": "operational",
        "features": [
            "Multimodal input processing",
            "Local privacy screening (>95% accuracy)",
            "Ticket management with conversation history",
            "Audio transcription (English/Swedish)",
            "LlamaIndex document processing",
        ],
        "docs_url": "/docs" if settings.debug else None,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload and settings.debug,
        log_config=None,  # We handle logging ourselves
    )