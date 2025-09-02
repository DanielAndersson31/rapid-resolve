"""Structured logging configuration for the application."""

import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from ..config.settings import get_settings


class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = getattr(self, '_correlation_id', 'unknown')
        return True
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """Set the correlation ID for this filter."""
        self._correlation_id = correlation_id


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_entry["correlation_id"] = record.correlation_id
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'exc_info', 'exc_text',
                'stack_info', 'correlation_id', 'message'
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as readable text."""
        # Base format
        formatted = super().format(record)
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            formatted = f"[{record.correlation_id}] {formatted}"
        
        return formatted


def setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set log level
    log_level = getattr(logging, settings.logging.level.upper())
    root_logger.setLevel(log_level)
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Configure formatter based on format setting
    if settings.logging.format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    handler.setFormatter(formatter)
    
    # Add correlation ID filter if enabled
    if settings.logging.enable_correlation_id:
        correlation_filter = CorrelationIdFilter()
        handler.addFilter(correlation_filter)
    
    root_logger.addHandler(handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # Our application loggers
    logging.getLogger("src").setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


class LoggingContextManager:
    """Context manager for setting correlation ID in logs."""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid4())
        self._original_correlation_id = None
    
    def __enter__(self) -> str:
        """Enter the context and set correlation ID."""
        # Find the correlation ID filter and set the ID
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            for filter_obj in handler.filters:
                if isinstance(filter_obj, CorrelationIdFilter):
                    self._original_correlation_id = getattr(filter_obj, '_correlation_id', None)
                    filter_obj.set_correlation_id(self.correlation_id)
                    break
        
        return self.correlation_id
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context and restore original correlation ID."""
        # Restore original correlation ID
        if self._original_correlation_id is not None:
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                for filter_obj in handler.filters:
                    if isinstance(filter_obj, CorrelationIdFilter):
                        filter_obj.set_correlation_id(self._original_correlation_id)
                        break


def log_execution_time(func_name: str):
    """Decorator to log function execution time."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger = get_logger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"Function {func_name} completed",
                    extra={"execution_time": execution_time}
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Function {func_name} failed",
                    extra={"execution_time": execution_time, "error": str(e)}
                )
                raise
        
        return wrapper
    return decorator


async def log_async_execution_time(func_name: str):
    """Decorator to log async function execution time."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            logger = get_logger(func.__module__)
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"Async function {func_name} completed",
                    extra={"execution_time": execution_time}
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Async function {func_name} failed",
                    extra={"execution_time": execution_time, "error": str(e)}
                )
                raise
        
        return wrapper
    return decorator