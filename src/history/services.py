"""
Service layer for handling query history tracking.
"""

import logging
from uuid import UUID

from src.schemas import QueryRequest, QueryResponse

from .repositories import HistoryRepository
from .schemas import (
    QueryHistoryListResponse,
    QueryHistoryResponse,
    QueryStatisticsResponse,
    SourceDocumentHistoryResponse,
)

logger = logging.getLogger(__name__)


class HistoryService:
    """Service for tracking RAG query history."""

    def __init__(self, repository: HistoryRepository):
        self.repository = repository

    def save_query_history(
        self,
        query_request: QueryRequest,
        query_response: QueryResponse,
        response_time_ms: None | int = None,
        success: bool = True,
        error_message: None | str = None,
    ) -> None | UUID:
        """Save a query and its response to the history."""
        try:
            query_history = self.repository.create_query_history(
                query=query_request.query,
                chat_response=query_response.chat_response,
                top_k=query_request.top_k,
                response_time_ms=response_time_ms,
                source_document_count=len(query_response.source_documents),
                success=success,
                error_message=error_message,
            )
            if not query_history or not query_history.id:
                return None
            for doc in query_response.source_documents:
                self.repository.create_source_document_history(
                    query_id=query_history.id,
                    content_preview=doc.content[:500],
                    similarity_score=doc.score,
                    document_metadata=doc.metadata,
                )
            logger.info(f"Saved query history with ID: {query_history.id}")
            return query_history.id
        except Exception as e:
            logger.error(f"Failed to save query history: {e}")
            return None

    def get_query_history(
        self, limit: int = 10, offset: int = 0
    ) -> QueryHistoryListResponse:
        """Get recent query history."""
        return self.repository.get_query_history_paginated(limit=limit, offset=offset)

    def get_query_by_id(self, query_id: UUID) -> QueryHistoryResponse | None:
        """Get a specific query by ID."""
        return self.repository.get_query_history_by_id(query_id)

    def get_source_documents_for_query(
        self, query_id: UUID
    ) -> list[SourceDocumentHistoryResponse]:
        """Get source documents used for a specific query."""
        return self.repository.get_source_documents_by_query_id(query_id)

    def get_query_statistics(self) -> QueryStatisticsResponse:
        """Get statistics about query history."""
        try:
            total_queries = self.repository.get_total_query_count()
            successful_queries = self.repository.get_successful_query_count()
            queries_with_time = self.repository.get_queries_with_response_time()
            avg_response_time = None
            if queries_with_time:
                total_time = sum(
                    q.response_time_ms for q in queries_with_time if q.response_time_ms
                )
                avg_response_time = total_time / len(queries_with_time)
            success_rate = (
                (successful_queries / total_queries * 100) if total_queries > 0 else 0
            )
            return QueryStatisticsResponse(
                total_queries=total_queries,
                successful_queries=successful_queries,
                success_rate_percent=round(success_rate, 2),
                average_response_time_ms=(
                    round(avg_response_time, 2) if avg_response_time else None
                ),
            )
        except Exception as e:
            logger.error(f"Failed to get query statistics: {e}")
            return QueryStatisticsResponse(
                total_queries=0,
                successful_queries=0,
                success_rate_percent=0,
                average_response_time_ms=None,
            )
