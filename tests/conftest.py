"""Pytest configuration and fixtures for the test suite."""

import asyncio
import json
import pytest
import pytest_asyncio
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, Mock

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.models import Base
from src.config.settings import Settings
from src.services.privacy_screening import PrivacyScreeningService
from src.services.whisper_service import WhisperService
from src.services.language_service import LanguageDetectionService
from src.services.ticket_service import TicketService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings with in-memory database."""
    settings = Settings(
        database={"url": "sqlite+aiosqlite:///:memory:"},
        ollama={"base_url": "http://localhost:11434", "privacy_screening_model": "test"},
        whisper={"model_path": Path("./test_models"), "english_model": "base", "swedish_model": "base"},
        application={
            "max_audio_size_mb": 1,
            "max_audio_duration_seconds": 30,
            "privacy_confidence_threshold": 0.95,
            "supported_audio_formats": [".wav", ".mp3"],
            "supported_categories": ["laptops", "phones", "accessories"],
            "supported_languages": ["en", "sv"],
        },
        debug=True,
    )
    return settings


@pytest_asyncio.fixture
async def db_session(test_settings: Settings) -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session."""
    engine = create_async_engine(
        test_settings.database.url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session_maker() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def mock_privacy_screening_service():
    """Mock privacy screening service."""
    service = Mock(spec=PrivacyScreeningService)
    service.screen_content = AsyncMock(return_value=Mock(
        screened_text="Test content [REDACTED]",
        confidence_score=0.98,
        detected_entities=["EMAIL"],
        is_safe=True
    ))
    service.health_check = AsyncMock(return_value={"status": "healthy"})
    return service


@pytest.fixture
def mock_whisper_service():
    """Mock whisper service."""
    service = Mock(spec=WhisperService)
    service.transcribe_audio = AsyncMock(return_value={
        "text": "This is a test transcription",
        "language": "en",
        "confidence": 0.95,
        "duration": 10.5,
        "processing_time": 2.3,
        "model_used": "turbo",
    })
    service.health_check = AsyncMock(return_value={"overall": "healthy"})
    return service


@pytest.fixture
def mock_language_service():
    """Mock language detection service."""
    service = Mock(spec=LanguageDetectionService)
    service.detect_language_simple = Mock(return_value="en")
    service.detect_language = Mock(return_value=("en", 0.95))
    service.health_check = AsyncMock(return_value={"overall": "healthy"})
    return service


@pytest.fixture
def sample_ticket_data() -> Dict[str, Any]:
    """Sample ticket creation data."""
    return {
        "customer_name": "John Doe",
        "customer_email": "john.doe@example.com",
        "customer_phone": "+1-555-123-4567",
        "subject": "Laptop screen flickering",
        "content": "My laptop screen keeps flickering when I open it. It's a Dell XPS 13.",
        "category": "laptops",
        "language": "en",
        "priority": "medium"
    }


@pytest.fixture
def pii_samples() -> Dict[str, Any]:
    """Sample PII data for testing privacy screening."""
    return {
        "test_cases": [
            {
                "text": "My email is john.doe@example.com and phone is 555-123-4567",
                "language": "en",
                "expected_entities": ["EMAIL", "PHONE"]
            },
            {
                "text": "Contact me at jane@company.org or call 555-987-6543",
                "language": "en", 
                "expected_entities": ["EMAIL", "PHONE"]
            },
            {
                "text": "Min e-post är användare@exempel.se",
                "language": "sv",
                "expected_entities": ["EMAIL"]
            },
            {
                "text": "Call John Smith at 123-456-7890",
                "language": "en",
                "expected_entities": ["PERSON", "PHONE"]
            },
            {
                "text": "Credit card 4111-1111-1111-1111 expires 12/25",
                "language": "en",
                "expected_entities": ["CREDIT_CARD", "DATE"]
            }
        ]
    }


@pytest.fixture
def audio_test_data() -> bytes:
    """Generate mock audio data for testing."""
    # Generate simple WAV header + silence
    sample_rate = 16000
    duration = 1  # 1 second
    channels = 1
    bits_per_sample = 16
    
    # WAV header (44 bytes)
    wav_header = bytearray(44)
    
    # RIFF header
    wav_header[0:4] = b'RIFF'
    wav_header[8:12] = b'WAVE'
    
    # fmt chunk
    wav_header[12:16] = b'fmt '
    wav_header[16:20] = (16).to_bytes(4, 'little')  # fmt chunk size
    wav_header[20:22] = (1).to_bytes(2, 'little')   # PCM format
    wav_header[22:24] = channels.to_bytes(2, 'little')
    wav_header[24:28] = sample_rate.to_bytes(4, 'little')
    
    bytes_per_second = sample_rate * channels * bits_per_sample // 8
    wav_header[28:32] = bytes_per_second.to_bytes(4, 'little')
    wav_header[32:34] = (channels * bits_per_sample // 8).to_bytes(2, 'little')
    wav_header[34:36] = bits_per_sample.to_bytes(2, 'little')
    
    # data chunk
    wav_header[36:40] = b'data'
    data_size = sample_rate * duration * channels * bits_per_sample // 8
    wav_header[40:44] = data_size.to_bytes(4, 'little')
    
    # File size
    file_size = 36 + data_size
    wav_header[4:8] = file_size.to_bytes(4, 'little')
    
    # Generate silent audio data
    audio_data = bytearray(data_size)
    
    return bytes(wav_header + audio_data)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running test"
    )
    config.addinivalue_line(
        "markers", "requires_ollama: mark test as requiring Ollama service"
    )
    config.addinivalue_line(
        "markers", "requires_whisper: mark test as requiring Whisper models"
    )