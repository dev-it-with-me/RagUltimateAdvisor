"""Configuration module for the Ultimate Advisor application."""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Database Configuration
    PG_HOST: str = Field(default="localhost", description="PostgreSQL host address")
    PG_PORT: int = Field(default=5432, description="PostgreSQL port number")
    PG_USER: str = Field(description="PostgreSQL username")
    PG_PASSWORD: str = Field(description="PostgreSQL user password")
    PG_DATABASE: str = Field(description="PostgreSQL database name")

    # Vector Store Configuration
    VECTOR_TABLE_NAME: str = Field(
        default="documents", description="Name of the table to store document vectors"
    )
    EMBED_DIM: int = Field(
        default=768,
        description="Dimension of the embedding vectors (auto-detected from model)",
    )

    # Ollama Configuration
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434", description="Base URL for Ollama API"
    )
    CHAT_MODEL: str = Field(
        default="gemma3:4b", description="Name of the chat model to use"
    )
    EMBEDDING_MODEL: str = Field(
        default="embeddinggemma", description="Name of the embedding model to use"
    )

    # Application Configuration
    DATA_FOLDER: Path = BASE_DIR / "data"

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("DATA_FOLDER")
    def validate_directories(cls, v):
        """Ensure that DATA_FOLDER is a valid Path object."""
        if not isinstance(v, Path):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v


# Global settings instance
settings = Settings()  # type: ignore
