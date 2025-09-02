name: "Multimodal Customer Service AI System with Local Privacy Screening"
description: |

## Purpose
Build a comprehensive multimodal customer service AI system featuring LlamaIndex development environment, local security screening with >95% accuracy using Llama/Mistral models, automated ticket management with conversation history, FastAPI backend, and Whisper transcription support for English and Swedish languages in electronic consumer products domain.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Create a production-ready multimodal customer service AI system where customers can submit tickets via text, audio (Whisper transcription), with automatic private information screening before external API calls, comprehensive ticket management with conversation history tracking, and multilingual support for English and Swedish in the electronic consumer products domain.

## Why
- **Business value**: Automates customer service for electronic consumer products while maintaining >95% privacy protection
- **Integration**: Establishes foundation for multimodal AI customer service with local privacy-first architecture
- **Problems solved**: Reduces manual customer service workload while ensuring private information never leaves local environment

## What
A FastAPI-based application where:
- Customers submit tickets via web interface or audio upload
- Local Llama/Mistral models screen for private information (>95% accuracy requirement)
- LlamaIndex manages document processing and retrieval
- SQLite/PostgreSQL stores ticket conversations with history
- Whisper provides local speech-to-text transcription
- System supports English and Swedish language detection and processing

### Success Criteria
- [ ] LlamaIndex development environment configured with proper logging
- [ ] Local Llama/Mistral privacy screening achieves >95% accuracy on validation dataset
- [ ] Ticket system generates unique IDs and tracks conversation context
- [ ] Whisper transcribes audio with format validation and size limits
- [ ] FastAPI backend handles multimodal inputs with proper error handling
- [ ] Electronics product validation (laptops, phones, accessories) functions correctly
- [ ] All tests pass and code meets quality standards

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://docs.llamaindex.ai/en/stable/getting_started/
  why: Core LlamaIndex setup patterns and document processing
  
- url: https://docs.llamaindex.ai/en/stable/module_guides/models/llms/
  why: Local LLM integration patterns for Llama/Mistral models
  
- url: https://docs.llamaindex.ai/en/stable/module_guides/observability/
  why: Observability and logging configuration for development environment
  
- url: https://github.com/openai/whisper
  why: Local Whisper deployment patterns, model variants, and resource requirements
  
- url: https://fastapi.tiangolo.com/tutorial/sql-databases/
  why: FastAPI with SQLAlchemy integration patterns and best practices

- url: https://www.llamaindex.ai/blog/running-mixtral-8x7-locally-with-llamaindex-e6cebeabe0ab
  why: Local Mixtral integration patterns with LlamaIndex and Ollama

- url: https://www.elastic.co/search-labs/blog/rag-security-masking-pii
  why: PII detection and masking patterns in RAG pipelines for privacy protection

- url: https://github.com/zhanymkanov/fastapi-best-practices
  why: FastAPI best practices and conventions for 2025
```

### Current Codebase tree
```bash
.
├── .claude/
├── CLAUDE.md                    # Development guidelines and conventions
├── INITIAL.md                  # Feature specification
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md
│   └── EXAMPLE_multi_agent_prp.md
├── README.md
└── install_claude_code_windows.md
```

### Desired Codebase tree with files to be added
```bash
.
├── src/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py             # Environment and configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py           # Database connection and session management
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   └── schemas.py              # Pydantic schemas for API validation
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llamaindex_service.py   # LlamaIndex development environment
│   │   ├── privacy_screening.py   # Local Llama/Mistral PII detection/masking
│   │   ├── ticket_service.py      # Ticket management and conversation tracking
│   │   ├── whisper_service.py     # Audio transcription service
│   │   └── language_service.py    # Language detection for English/Swedish
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── tickets.py          # Ticket management endpoints
│   │   │   ├── audio.py            # Audio upload and transcription endpoints
│   │   │   └── health.py           # Health check endpoints
│   │   └── middleware.py           # Request/response middleware
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── audio.py               # Audio file validation (format, size)
│   │   └── products.py            # Electronics product validation
│   └── utils/
│       ├── __init__.py
│       ├── logging.py             # Structured logging configuration
│       └── exceptions.py          # Custom exception classes
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest configuration and fixtures
│   ├── test_llamaindex_service.py # LlamaIndex service tests
│   ├── test_privacy_screening.py  # Privacy screening accuracy tests
│   ├── test_ticket_service.py     # Ticket management tests
│   ├── test_whisper_service.py    # Whisper transcription tests
│   ├── test_api/
│   │   ├── __init__.py
│   │   └── test_tickets.py        # API endpoint tests
│   └── validation_data/           # Dataset for privacy screening validation
│       ├── pii_samples.json       # Sample data with known PII
│       └── test_audio_files/      # Audio samples for testing
├── models/                        # Local LLM models directory
│   └── .gitkeep
├── data/                         # LlamaIndex document storage
│   └── .gitkeep
├── logs/                         # Application logs
│   └── .gitkeep
├── .env.example                  # Environment variables template
├── pyproject.toml               # UV package management and tool config
├── requirements.txt             # Python dependencies
└── README.md                    # Comprehensive setup and usage documentation
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: LlamaIndex requires specific setup for local LLMs with Ollama
# Pattern: Use Settings.llm = Ollama(model="mixtral") for global LLM config
# GOTCHA: Install ollama separately: curl -fsSL https://ollama.ai/install.sh | sh

# CRITICAL: Whisper models have specific VRAM requirements
# tiny: ~1GB VRAM, turbo: ~6GB VRAM, large: ~10GB VRAM
# Pattern: Start with "turbo" model for English optimization

# CRITICAL: Privacy screening accuracy depends on model size and fine-tuning
# Current state-of-art PII detection: 92-95% accuracy baseline
# Pattern: Combine multiple detection methods for >95% accuracy requirement

# CRITICAL: FastAPI with SQLAlchemy 2.0 requires async session management
# Pattern: Session per async task, use dependency injection for database sessions
# GOTCHA: Don't use sync functions in async context

# CRITICAL: Audio file validation essential for Whisper
# Supported formats: .flac, .mp3, .wav, .m4a
# Pattern: Validate file size (max 25MB), duration (max 10 minutes)

# CRITICAL: Language detection must happen before processing
# Pattern: Use langdetect library first, then route to appropriate model
# GOTCHA: Swedish language detection accuracy varies with text length

# CRITICAL: Conversation history schema design for long-term storage
# Pattern: Use hierarchical message structure with parent_message_id
# GOTCHA: Index on ticket_id and created_at for performance

# CRITICAL: UV package management - never edit pyproject.toml directly
# Pattern: Always use "uv add package" and "uv remove package"
```

## Implementation Blueprint

### Data models and structure

Create the core data models ensuring type safety and consistency across the system.

```python
# database/models.py - SQLAlchemy ORM models
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime, UTC

Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"
    
    ticket_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False)
    customer_phone = Column(String)
    subject = Column(String, nullable=False)
    status = Column(String, default="open")  # open, in_progress, resolved, closed
    priority = Column(String, default="medium")  # low, medium, high, urgent
    category = Column(String)  # laptops, phones, accessories
    language = Column(String, default="en")  # en, sv
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationship to messages
    messages = relationship("TicketMessage", back_populates="ticket")

class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    
    message_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    ticket_id = Column(String, ForeignKey("tickets.ticket_id"), nullable=False)
    sender_type = Column(String, nullable=False)  # customer, agent, system
    content = Column(Text, nullable=False)
    original_content = Column(Text)  # Before privacy screening
    is_screened = Column(Boolean, default=False)
    attachment_info = Column(JSON)  # Audio file metadata
    parent_message_id = Column(String, ForeignKey("ticket_messages.message_id"))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    ticket = relationship("Ticket", back_populates="messages")
    parent_message = relationship("TicketMessage", remote_side=[message_id])

# database/schemas.py - Pydantic models
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    subject: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    category: Optional[str] = None
    language: str = Field(default="en", pattern="^(en|sv)$")

class AudioUpload(BaseModel):
    ticket_id: str
    language: str = Field(default="en", pattern="^(en|sv)$")

class PrivacyScreeningResult(BaseModel):
    original_text: str
    screened_text: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    detected_entities: List[str]
    is_safe: bool
```

### List of tasks to be completed to fulfill the PRP in the order they should be completed

```yaml
Task 1: Setup Development Environment and Configuration
CREATE pyproject.toml:
  - PATTERN: Follow CLAUDE.md UV package management guidelines
  - Add all required dependencies with specific versions
  - Configure ruff, mypy, pytest settings

CREATE .env.example:
  - Include all environment variables with descriptions
  - Database URLs, model paths, API keys for development

CREATE src/config/settings.py:
  - PATTERN: Use pydantic-settings for environment management
  - Validate required configurations on startup
  - Include database, model, and service configurations

Task 2: Implement Database Layer
CREATE src/database/connection.py:
  - PATTERN: Follow async SQLAlchemy 2.0 patterns from research
  - Implement session management with dependency injection
  - Connection pooling for performance

CREATE src/database/models.py:
  - PATTERN: Mirror the exact schema design from FastAPI best practices
  - Implement ticket and message models with proper relationships
  - Add indexes for performance on ticket_id, created_at

CREATE src/database/schemas.py:
  - PATTERN: Pydantic v2 models for request/response validation
  - Separate schemas for create, update, response operations
  - Include validators for email, phone, language codes

Task 3: Implement LlamaIndex Development Environment
CREATE src/services/llamaindex_service.py:
  - PATTERN: Follow LlamaIndex getting started guide setup
  - Configure local document processing with SimpleDirectoryReader
  - Implement VectorStoreIndex with proper observability logging
  - Support both Ollama integration and fallback configurations

Task 4: Implement Privacy Screening Service
CREATE src/services/privacy_screening.py:
  - PATTERN: Local Llama/Mistral via Ollama integration
  - Implement PII detection using multiple techniques for >95% accuracy
  - Create validation dataset from tests/validation_data/
  - Mask detected entities while preserving message meaning
  - CRITICAL: Validate accuracy before allowing external API calls

Task 5: Implement Whisper Transcription Service
CREATE src/services/whisper_service.py:
  - PATTERN: Follow Whisper GitHub implementation guide
  - Load turbo model for English, medium for Swedish
  - Implement file validation (format, size, duration)
  - Handle async processing with proper error handling
  - Store audio metadata in message attachments

Task 6: Implement Ticket Management Service
CREATE src/services/ticket_service.py:
  - PATTERN: Repository pattern with async SQLAlchemy
  - Generate unique ticket IDs with proper formatting
  - Implement conversation history with threading support
  - Track status changes and updates with timestamps

Task 7: Implement Language Detection Service
CREATE src/services/language_service.py:
  - PATTERN: Use langdetect library for initial detection
  - Route to appropriate models based on detected language
  - Handle edge cases where detection confidence is low
  - Support fallback to English for unknown languages

Task 8: Create Product Validation
CREATE src/validators/products.py:
  - PATTERN: Enum-based validation for electronics categories
  - Support laptops, phones, accessories categories
  - Validate product model numbers and specifications

CREATE src/validators/audio.py:
  - PATTERN: File type and size validation before processing
  - Check supported formats (.mp3, .wav, .flac, .m4a)
  - Validate duration limits (max 10 minutes)
  - Audio quality checks for transcription accuracy

Task 9: Implement FastAPI Backend
CREATE src/main.py:
  - PATTERN: FastAPI application with proper middleware setup
  - Configure CORS, logging, exception handling
  - Include all routers and startup/shutdown events

CREATE src/api/routes/tickets.py:
  - PATTERN: RESTful API design with proper HTTP status codes
  - POST /tickets - create new ticket
  - GET /tickets/{ticket_id} - retrieve ticket with messages
  - PUT /tickets/{ticket_id}/messages - add message to ticket
  - Include proper error handling and validation

CREATE src/api/routes/audio.py:
  - PATTERN: File upload handling with FastAPI
  - POST /tickets/{ticket_id}/audio - upload and transcribe
  - Async processing with status endpoints
  - Proper cleanup of temporary files

Task 10: Implement Comprehensive Testing
CREATE tests/conftest.py:
  - PATTERN: Pytest fixtures for database, services
  - Mock external dependencies (Ollama, Whisper models)
  - Test data fixtures for consistent testing

CREATE tests/test_privacy_screening.py:
  - PATTERN: Test accuracy requirements with validation dataset
  - Benchmark against >95% accuracy requirement
  - Test edge cases and false positives/negatives

CREATE tests/validation_data/:
  - Create PII samples with known entities
  - Include Swedish and English text samples
  - Audio files for transcription testing

Task 11: Add Logging and Observability
CREATE src/utils/logging.py:
  - PATTERN: Structured logging with correlation IDs
  - Different log levels for development/production
  - Integration with LlamaIndex observability

Task 12: Create Comprehensive Documentation
UPDATE README.md:
  - Installation and setup instructions
  - Environment configuration guide
  - API documentation with examples
  - Architecture diagrams and explanations
```

### Per task pseudocode

```python
# Task 4: Privacy Screening Service
class PrivacyScreeningService:
    def __init__(self):
        # PATTERN: Initialize Ollama client with local model
        self.llm = Ollama(model="mixtral:7b")  # GOTCHA: Model must be pulled first
        self.confidence_threshold = 0.95
        
    async def screen_content(self, text: str, language: str) -> PrivacyScreeningResult:
        # PATTERN: Multi-stage detection for >95% accuracy
        # Stage 1: Regex patterns for common PII
        regex_entities = self._detect_with_regex(text)
        
        # Stage 2: NER model detection
        ner_entities = self._detect_with_ner(text, language)
        
        # Stage 3: LLM-based contextual detection
        llm_entities = await self._detect_with_llm(text)
        
        # CRITICAL: Combine results and calculate confidence
        all_entities = self._merge_detections(regex_entities, ner_entities, llm_entities)
        confidence = self._calculate_confidence(all_entities)
        
        if confidence < self.confidence_threshold:
            raise ValueError(f"Privacy screening confidence {confidence} below threshold")
        
        # PATTERN: Mask entities while preserving context
        screened_text = self._mask_entities(text, all_entities)
        
        return PrivacyScreeningResult(
            original_text=text,
            screened_text=screened_text,
            confidence_score=confidence,
            detected_entities=all_entities,
            is_safe=confidence >= self.confidence_threshold
        )

# Task 5: Whisper Service
class WhisperService:
    def __init__(self):
        # PATTERN: Load models based on language requirements
        self.models = {
            "en": whisper.load_model("turbo"),      # Optimized for English
            "sv": whisper.load_model("medium"),     # Better for Swedish
        }
        self.max_duration = 600  # 10 minutes
        self.max_file_size = 25 * 1024 * 1024  # 25MB
        
    async def transcribe_audio(self, file_path: Path, language: str) -> dict:
        # PATTERN: Validate before processing
        await self._validate_audio_file(file_path)
        
        # GOTCHA: Whisper expects specific model for language
        model = self.models.get(language, self.models["en"])
        
        # PATTERN: Async processing with timeout
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            model.transcribe, 
            str(file_path)
        )
        
        return {
            "text": result["text"],
            "language": result.get("language"),
            "segments": result["segments"],
            "confidence": self._calculate_average_confidence(result["segments"])
        }

# Task 6: Ticket Service
class TicketService:
    def __init__(self, db: AsyncSession, privacy_service: PrivacyScreeningService):
        self.db = db
        self.privacy_service = privacy_service
        
    async def create_ticket(self, ticket_data: TicketCreate) -> Ticket:
        # PATTERN: Privacy screening before storage
        screened_subject = await self.privacy_service.screen_content(
            ticket_data.subject, 
            ticket_data.language
        )
        screened_content = await self.privacy_service.screen_content(
            ticket_data.content, 
            ticket_data.language
        )
        
        # PATTERN: Generate unique ticket ID with readable format
        ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
        
        # CRITICAL: Store both original and screened content for audit
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_name=ticket_data.customer_name,
            customer_email=str(ticket_data.customer_email),
            customer_phone=ticket_data.customer_phone,
            subject=screened_subject.screened_text,
            category=ticket_data.category,
            language=ticket_data.language
        )
        
        # Add initial message
        initial_message = TicketMessage(
            ticket_id=ticket_id,
            sender_type="customer",
            content=screened_content.screened_text,
            original_content=ticket_data.content,
            is_screened=True
        )
        
        self.db.add(ticket)
        self.db.add(initial_message)
        await self.db.commit()
        
        return ticket
```

### Integration Points
```yaml
DATABASE:
  - migration: "Create tickets and ticket_messages tables with indexes"
  - indexes: |
      CREATE INDEX idx_tickets_created_at ON tickets(created_at);
      CREATE INDEX idx_ticket_messages_ticket_id ON ticket_messages(ticket_id);
      CREATE INDEX idx_ticket_messages_created_at ON ticket_messages(created_at);
  
CONFIGURATION:
  - add to: .env
  - pattern: |
      # Database
      DATABASE_URL=sqlite:///./tickets.db
      
      # Ollama Configuration  
      OLLAMA_BASE_URL=http://localhost:11434
      PRIVACY_SCREENING_MODEL=mixtral:7b
      
      # Whisper Configuration
      WHISPER_MODEL_PATH=./models/
      AUDIO_UPLOAD_PATH=./uploads/audio/
      
      # Application
      MAX_AUDIO_SIZE_MB=25
      MAX_AUDIO_DURATION_SECONDS=600
      PRIVACY_CONFIDENCE_THRESHOLD=0.95

EXTERNAL_DEPENDENCIES:
  - Ollama installation and model pulling:
    - curl -fsSL https://ollama.ai/install.sh | sh
    - ollama pull mixtral:7b
  - FFmpeg for audio processing:
    - brew install ffmpeg (macOS)
    - apt install ffmpeg (Ubuntu)
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
uv run ruff check --fix src/        # Auto-fix style issues
uv run mypy src/                     # Type checking
uv run pytest tests/ -x --tb=short  # Stop on first test failure

# Expected: No errors. If errors exist, read and fix before continuing.
```

### Level 2: Unit Tests with Accuracy Validation
```python
# tests/test_privacy_screening.py
async def test_privacy_screening_accuracy_requirement():
    """Test that privacy screening meets >95% accuracy requirement"""
    screening_service = PrivacyScreeningService()
    
    # Load validation dataset
    with open("tests/validation_data/pii_samples.json") as f:
        test_cases = json.load(f)
    
    correct_detections = 0
    total_cases = len(test_cases)
    
    for case in test_cases:
        result = await screening_service.screen_content(
            case["text"], 
            case["language"]
        )
        
        # Check if all expected entities were detected
        expected_entities = set(case["expected_entities"])
        detected_entities = set(result.detected_entities)
        
        if expected_entities.issubset(detected_entities):
            correct_detections += 1
    
    accuracy = correct_detections / total_cases
    assert accuracy >= 0.95, f"Privacy screening accuracy {accuracy} below 95% requirement"

async def test_whisper_transcription_accuracy():
    """Test Whisper transcription for both languages"""
    whisper_service = WhisperService()
    
    # Test English audio
    en_result = await whisper_service.transcribe_audio(
        Path("tests/validation_data/test_audio_files/english_sample.wav"),
        "en"
    )
    assert en_result["text"]
    assert en_result["confidence"] > 0.8
    
    # Test Swedish audio  
    sv_result = await whisper_service.transcribe_audio(
        Path("tests/validation_data/test_audio_files/swedish_sample.wav"),
        "sv"
    )
    assert sv_result["text"]
    assert sv_result["confidence"] > 0.7  # Swedish might be slightly lower

def test_ticket_lifecycle():
    """Test complete ticket creation and message flow"""
    ticket_data = TicketCreate(
        customer_name="John Doe",
        customer_email="john@example.com",
        subject="Laptop screen flickering",
        content="My laptop screen keeps flickering. Model: XPS 13 2024",
        category="laptops",
        language="en"
    )
    
    # This should create ticket, screen content, generate ID
    ticket = await ticket_service.create_ticket(ticket_data)
    
    assert ticket.ticket_id.startswith("TKT-")
    assert ticket.category == "laptops"
    assert len(ticket.messages) == 1
    assert ticket.messages[0].is_screened is True
```

```bash
# Run tests iteratively until passing:
uv run pytest tests/test_privacy_screening.py -v
uv run pytest tests/test_whisper_service.py -v  
uv run pytest tests/test_ticket_service.py -v

# Full test suite with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Expected: >95% accuracy on privacy screening, >80% coverage, all tests pass
```

### Level 3: Integration Tests
```bash
# Start Ollama service
ollama serve

# Pull required models
ollama pull mixtral:7b

# Start the FastAPI application
uv run python -m src.main

# Test API endpoints
curl -X POST http://localhost:8000/api/v1/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test Customer",
    "customer_email": "test@example.com", 
    "subject": "Audio transcription test",
    "content": "Testing the multimodal system",
    "category": "phones",
    "language": "en"
  }'

# Test audio upload
curl -X POST http://localhost:8000/api/v1/tickets/{ticket_id}/audio \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@test_audio.wav" \
  -F "language=en"

# Expected responses:
# - Ticket creation: 201 Created with ticket ID
# - Audio upload: 200 OK with transcription result
# - Privacy screening: All PII masked in responses
```

## Final Validation Checklist
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check src/`
- [ ] No type errors: `uv run mypy src/`
- [ ] Privacy screening achieves >95% accuracy on validation dataset
- [ ] Whisper transcribes English and Swedish audio correctly
- [ ] Ticket system creates unique IDs and tracks conversations
- [ ] LlamaIndex environment configured with proper logging
- [ ] FastAPI serves all endpoints without errors
- [ ] Product validation works for electronics categories
- [ ] Database schema supports conversation history
- [ ] Audio file validation prevents invalid uploads
- [ ] Error handling graceful across all services
- [ ] Documentation includes setup and usage instructions

---

## Anti-Patterns to Avoid
- ❌ Don't skip privacy screening validation - accuracy requirement is critical
- ❌ Don't use sync functions in async FastAPI context
- ❌ Don't store unscreened content without original for audit trail
- ❌ Don't ignore audio file validation - invalid files crash Whisper
- ❌ Don't hardcode model paths - use configuration management
- ❌ Don't forget to index database tables for conversation history queries
- ❌ Don't assume language detection is 100% accurate - provide fallbacks
- ❌ Don't skip Ollama model pulling in setup instructions
- ❌ Don't commit model files or audio uploads to repository

## Confidence Score: 8.5/10

High confidence due to:
- Comprehensive research on all required technologies and integration patterns
- Clear examples from LlamaIndex, FastAPI, and Whisper documentation
- Established patterns for privacy screening and PII detection
- Well-defined validation criteria including accuracy requirements
- Complete implementation blueprint with specific gotchas identified

Minor uncertainty around:
- Achieving exactly >95% privacy screening accuracy (current SOTA is 92-95%)
- Swedish language support quality with Whisper medium model
- Performance optimization for simultaneous audio processing

These can be addressed through iterative testing and model fine-tuning during implementation.