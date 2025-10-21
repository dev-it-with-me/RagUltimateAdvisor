"""Configuration module for the Ultimate Advisor application."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # ChromaDB Configuration (Vector Store)
    CHROMA_PERSIST_DIRECTORY: Path = Field(
        default=BASE_DIR / "storage" / "vectors" / "chroma",
        description="Directory for ChromaDB persistent storage",
    )
    CHROMA_COLLECTION_NAME: str = Field(
        default="ultimate_advisor_docs",
        description="Name of the ChromaDB collection for document vectors",
    )

    # SQLite Configuration (Query History)
    HISTORY_DB_PATH: Path = Field(
        default=BASE_DIR / "storage" / "database" / "ultimate_advisor.db",
        description="Path to SQLite database for query history",
    )

    # Embedding Configuration
    EMBED_DIM: int = Field(
        default=1024,
        description="Dimension of the embedding vectors (VoyageAI: 1024)",
    )

    # Anthropic Configuration
    ANTHROPIC_API_KEY: str = Field(description="Anthropic API key")
    ANTHROPIC_MODEL: str = Field(
        default="claude-sonnet-4-0",
        description="Anthropic model to use for chat/generation",
    )

    # VoyageAI Configuration
    VOYAGE_API_KEY: str = Field(description="VoyageAI API key for embeddings")
    VOYAGE_MODEL: str = Field(
        default="voyage-3.5",
        description="VoyageAI embedding model (voyage-3.5 recommended for cost)",
    )

    DATA_FOLDER: Path = BASE_DIR / "data"

    @property
    def history_database_url(self) -> str:
        """Construct SQLite database URL for query history."""
        return f"sqlite:///{self.HISTORY_DB_PATH}"

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("DATA_FOLDER", "CHROMA_PERSIST_DIRECTORY")
    def validate_directories(cls, v):
        """Ensure that directories are valid Path objects and exist."""
        if not isinstance(v, Path):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v


settings = Settings()  # type: ignore
