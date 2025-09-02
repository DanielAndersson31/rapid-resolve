"""Application configuration settings using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """Database configuration settings."""
    
    url: str = Field(default="sqlite+aiosqlite:///./tickets.db")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=20, ge=1)
    max_overflow: int = Field(default=30, ge=0)


class OllamaSettings(BaseModel):
    """Ollama LLM configuration settings."""
    
    base_url: str = Field(default="http://localhost:11434")
    privacy_screening_model: str = Field(default="mixtral:7b")
    llamaindex_llm_model: str = Field(default="mixtral:7b")
    request_timeout: float = Field(default=60.0, gt=0)


class WhisperSettings(BaseModel):
    """Whisper transcription configuration settings."""
    
    model_path: Path = Field(default=Path("./models/"))
    english_model: str = Field(default="turbo")
    swedish_model: str = Field(default="medium")
    device: str = Field(default="auto")  # auto, cpu, cuda


class ApplicationSettings(BaseModel):
    """General application settings."""
    
    max_audio_size_mb: int = Field(default=25, ge=1, le=100)
    max_audio_duration_seconds: int = Field(default=600, ge=1)
    privacy_confidence_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    supported_audio_formats: List[str] = Field(
        default=[".mp3", ".wav", ".flac", ".m4a"]
    )
    supported_categories: List[str] = Field(
        default=["laptops", "phones", "accessories"]
    )
    supported_languages: List[str] = Field(default=["en", "sv"])
    default_language: str = Field(default="en")


class LoggingSettings(BaseModel):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO")
    format: str = Field(default="json")  # json or text
    enable_correlation_id: bool = Field(default=True)


class SecuritySettings(BaseModel):
    """Security configuration settings."""
    
    secret_key: str = Field(default="change-this-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1)


class LlamaIndexSettings(BaseModel):
    """LlamaIndex configuration settings."""
    
    data_path: Path = Field(default=Path("./data/"))
    vector_store: str = Field(default="simple")
    enable_observability: bool = Field(default=True)
    chunk_size: int = Field(default=1024, ge=100)
    chunk_overlap: int = Field(default=200, ge=0)


class FileStorageSettings(BaseModel):
    """File storage configuration settings."""
    
    upload_dir: Path = Field(default=Path("./uploads/"))
    temp_dir: Path = Field(default=Path("./temp/"))
    log_dir: Path = Field(default=Path("./logs/"))
    audio_upload_path: Path = Field(default=Path("./uploads/audio/"))


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    reload: bool = Field(default=True)
    
    # CORS
    enable_cors: bool = Field(default=True)
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    whisper: WhisperSettings = Field(default_factory=WhisperSettings)
    application: ApplicationSettings = Field(default_factory=ApplicationSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    llamaindex: LlamaIndexSettings = Field(default_factory=LlamaIndexSettings)
    file_storage: FileStorageSettings = Field(default_factory=FileStorageSettings)
    
    def __init__(self, **kwargs):  # type: ignore
        super().__init__(**kwargs)
        self._ensure_directories_exist()
    
    def _ensure_directories_exist(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.file_storage.upload_dir,
            self.file_storage.temp_dir,
            self.file_storage.log_dir,
            self.file_storage.audio_upload_path,
            self.whisper.model_path,
            self.llamaindex.data_path,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()