"""
Application configuration management
Loads environment variables and provides settings
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "StylistAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Firebase Authentication
    FIREBASE_CREDENTIALS_PATH: str
    FIREBASE_PROJECT_ID: str
    FIREBASE_WEB_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///./stylistai.db"

    # ChromaDB
    CHROMA_HOST: str = "http://localhost:8001"  # ChromaDB server URL (Docker or cloud)
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "outfits"

    # Google Cloud Storage
    GCS_BUCKET_NAME: str
    GCS_CREDENTIALS_PATH: str
    GCS_PROJECT_ID: str

    # OpenAI (Primary LLM and Embeddings)
    OPENAI_API_KEY: str = ""
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_LLM_MODEL: str = "gpt-4-turbo-preview"

    # Image Processing
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_FORMATS: str = "jpg,jpeg,png,webp"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Redis (Optional)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # Datadog LLM Observability
    DD_API_KEY: str = ""  # Load from environment variable
    DD_SITE: str = "datadoghq.com"  # or datadoghq.eu for EU
    DD_SERVICE: str = "stylistai-backend"
    DD_ENV: str = "production"  # development, staging, or production
    DD_VERSION: str = "1.0.0"
    DD_LLMOBS_ENABLED: bool = True
    DD_LLMOBS_ML_APP: str = "stylistai"
    DD_TRACE_OPENAI_ENABLED: bool = True
    DD_TRACE_ENABLED: bool = True
    DD_LOGS_INJECTION: bool = True
    DD_AGENT_HOST: str = "localhost"
    DD_TRACE_AGENT_PORT: str = "8126"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def allowed_image_formats_list(self) -> List[str]:
        """Convert comma-separated string to list"""
        return [fmt.strip() for fmt in self.ALLOWED_IMAGE_FORMATS.split(",")]

    @property
    def max_image_size_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024


# Initialize settings instance
settings = Settings()
