"""
Application configuration
"""
import os
from typing import List

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older versions
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Database
    database_url: str = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'windexai.db')}"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API Keys
    openai_api_key: str = ""

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8003",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8003",
    ]

    # Server
    host: str = "0.0.0.0"
    port: int = 8003

    # AI Models
    default_model: str = "gpt-4o-mini"
    max_tokens_default: int = 16000

    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = [".txt", ".pdf", ".docx", ".md"]

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Override with environment variables if available
if os.getenv("DATABASE_URL"):
    settings.database_url = os.getenv("DATABASE_URL")
if os.getenv("SECRET_KEY"):
    settings.secret_key = os.getenv("SECRET_KEY")
if os.getenv("OPENAI_API_KEY"):
    settings.openai_api_key = os.getenv("OPENAI_API_KEY")
if os.getenv("HOST"):
    settings.host = os.getenv("HOST")
if os.getenv("PORT"):
    settings.port = int(os.getenv("PORT"))
