"""Configuration module for the Ultimate Advisor application."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

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
    def database_url(self) -> str:
        """Construct PostgreSQL database URL."""
        return f"postgresql://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"

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


settings = Settings()  # type: ignore
