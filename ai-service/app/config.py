"""
MemoraAI - Configuration Management
Handles environment variables and application settings.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "MemoraAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")

    # API Keys
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GOOGLE_API_KEY: str = Field(default="", description="Google AI API key for embeddings")

    # Database
    DATABASE_URL: str = Field(default="postgresql://user:password@localhost:5432/memora", description="PostgreSQL connection string")
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # Vector Search
    VECTOR_DIMENSION: int = 768
    TOP_K_RETRIEVAL: int = 10
    TOP_K_RERANKED: int = 5
    SIMILARITY_THRESHOLD: float = 0.7

    # BM25 Parameters
    BM25_K1: float = 1.5
    BM25_B: float = 0.75

    # RRF Parameters
    RRF_K: int = 60

    # Chunking
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP: int = 100

    # Reranking
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_TOP_K: int = 5

    # Embedding Model
    EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIMENSION: int = 768

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000

    # Memory
    SHORT_TERM_MEMORY_LIMIT: int = 20
    EPISODIC_MEMORY_RETENTION: int = 50

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Timeouts (seconds)
    REQUEST_TIMEOUT: int = 120
    EMBEDDING_TIMEOUT: int = 30
    GENERATION_TIMEOUT: int = 60

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:4000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


class DatabaseConfig:
    """Database connection configuration."""

    def __init__(self, settings: Settings):
        self.url = settings.DATABASE_URL
        self.pool_size = settings.DB_POOL_SIZE
        self.max_overflow = settings.DB_MAX_OVERFLOW
        self.pool_timeout = settings.DB_POOL_TIMEOUT

    @property
    def async_url(self) -> str:
        """Convert sync URL to async URL for asyncpg."""
        return self.url.replace("postgresql://", "postgresql+asyncpg://")


class VectorConfig:
    """Vector search configuration."""

    def __init__(self, settings: Settings):
        self.dimension = settings.VECTOR_DIMENSION
        self.top_k = settings.TOP_K_RETRIEVAL
        self.top_k_reranked = settings.TOP_K_RERANKED
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        self.reranker_model = settings.RERANKER_MODEL


class RetrievalConfig:
    """Retrieval pipeline configuration."""

    def __init__(self, settings: Settings):
        self.bm25_k1 = settings.BM25_K1
        self.bm25_b = settings.BM25_B
        self.rrf_k = settings.RRF_K
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP


class ConfigManager:
    """Central configuration manager."""

    _instance: Optional["ConfigManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.settings = Settings()
        self.database = DatabaseConfig(self.settings)
        self.vector = VectorConfig(self.settings)
        self.retrieval = RetrievalConfig(self.settings)

    def reload(self) -> None:
        """Reload configuration from environment."""
        self.settings = Settings()
        self.database = DatabaseConfig(self.settings)
        self.vector = VectorConfig(self.settings)
        self.retrieval = RetrievalConfig(self.settings)

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if not self.settings.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required")

        if self.settings.CHUNK_SIZE < 100:
            errors.append("CHUNK_SIZE must be at least 100")

        if self.settings.CHUNK_OVERLAP >= self.settings.CHUNK_SIZE:
            errors.append("CHUNK_OVERLAP must be less than CHUNK_SIZE")

        if self.settings.RRF_K <= 0:
            errors.append("RRF_K must be positive")

        return errors


config = ConfigManager()