"""
Schemas for query history endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ..schemas import DocumentMetadata


class QueryHistoryResponse(BaseModel):
    """Schema for query history response."""

    id: UUID
    query: str
    chat_response: str
    top_k: int
    response_time_ms: None | int = None
    source_document_count: int
    created_at: datetime
    success: bool
    error_message: None | str = None

    class Config:
        from_attributes = True


class SourceDocumentHistoryResponse(BaseModel):
    """Schema for source document history response."""

    id: UUID
    content_preview: str
    similarity_score: float
    document_metadata: DocumentMetadata | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class QueryHistoryListResponse(BaseModel):
    """Schema for paginated query history list."""

    items: list[QueryHistoryResponse]
    total_count: int
    limit: int
    offset: int


class QueryStatisticsResponse(BaseModel):
    """Schema for query statistics response."""

    total_queries: int = Field(..., description="Total number of queries")
    successful_queries: int = Field(..., description="Number of successful queries")
    success_rate_percent: float = Field(..., description="Success rate as percentage")
    average_response_time_ms: None | float = Field(
        default=None, description="Average response time in milliseconds"
    )


class QueryDetailResponse(BaseModel):
    """Schema for detailed query response including source documents."""

    query_history: QueryHistoryResponse
    source_documents: list[SourceDocumentHistoryResponse]
