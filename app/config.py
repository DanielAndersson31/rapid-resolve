from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "RapidResolve"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str
    
    # ChromaDB
    chromadb_host: str = "localhost"
    chromadb_port: int = 8001
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4-turbo"
    openai_vision_model: str = "gpt-4-turbo"
    
    # Anthropic (optional)
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    
    # Cloudflare R2
    cloudflare_r2_endpoint: str
    cloudflare_r2_access_key: str
    cloudflare_r2_secret_key: str
    cloudflare_r2_bucket: str
    
    # File Upload Limits
    max_file_size_mb: int = 50
    allowed_image_types: list[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    allowed_audio_types: list[str] = [".mp3", ".wav", ".m4a", ".ogg"]
    allowed_document_types: list[str] = [".pdf", ".txt", ".doc", ".docx"]
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Whisper Settings
    whisper_model: str = "base"  # tiny, base, small, medium, large
    
    # Context Settings
    max_context_turns: int = 20
    embedding_model: str = "text-embedding-3-small"
    
    # Ticket Settings
    default_ticket_priority: str = "medium"
    auto_escalate_threshold: float = 0.8
    
    @property
    def r2_endpoint_url(self) -> str:
        """Format R2 endpoint URL"""
        return f"https://{self.cloudflare_r2_endpoint}"


# Global settings instance
settings = Settings()