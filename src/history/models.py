"""
Database models for the Ultimate Advisor application.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class QueryHistory(SQLModel, table=True):
    """Model to track RAG query history."""

    id: None | UUID = Field(default_factory=uuid4, primary_key=True)
    query: str = Field(..., description="The user's query string")
    chat_response: str = Field(..., description="The AI's response")
    top_k: int = Field(description="Number of documents retrieved")
    response_time_ms: None | int = Field(
        default=None, description="Response time in milliseconds"
    )
    source_document_count: int = Field(description="Number of source documents used")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = Field(default=True, description="Whether the query was successful")
    error_message: None | str = Field(
        default=None, description="Error message if query failed"
    )


class SourceDocumentHistory(SQLModel, table=True):
    """Model to track which source documents were used for each query."""

    id: None | UUID = Field(default_factory=uuid4, primary_key=True)
    query_id: UUID = Field(
        foreign_key="queryhistory.id", description="Reference to the query"
    )
    content_preview: str = Field(
        ..., description="Preview of the source document content (first 500 chars)"
    )
    similarity_score: float = Field(
        ..., description="Similarity score of the document to the query"
    )
    document_metadata: None | str = Field(
        default=None, description="JSON string of document metadata"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
