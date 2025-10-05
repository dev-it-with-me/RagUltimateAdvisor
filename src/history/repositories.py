"""
Repository layer for query history data access.
"""

import ast
import json
import logging
from typing import Any
from uuid import UUID

from sqlmodel import Session, create_engine, desc, select

from src.config import settings
from src.schemas import DocumentMetadata

from .models import QueryHistory, SourceDocumentHistory
from .schemas import (
    QueryHistoryListResponse,
    QueryHistoryResponse,
    SourceDocumentHistoryResponse,
)

logger = logging.getLogger(__name__)


class HistoryRepository:
    """Repository for query history database operations."""

    def __init__(self):
        self.engine = create_engine(settings.database_url)

    @staticmethod
    def _parse_document_metadata(
        raw_metadata: Any,
    ) -> DocumentMetadata | None:
        """Convert stored metadata into a DocumentMetadata instance."""

        if raw_metadata is None:
            return None
        if isinstance(raw_metadata, DocumentMetadata):
            return raw_metadata
        if isinstance(raw_metadata, dict):
            return DocumentMetadata.model_validate(raw_metadata)
        if isinstance(raw_metadata, str):
            try:
                metadata_dict = json.loads(raw_metadata)
            except json.JSONDecodeError:
                metadata_dict = ast.literal_eval(raw_metadata)
            return DocumentMetadata.model_validate(metadata_dict)

        raise ValueError("Unsupported metadata format")

    def create_query_history(
        self,
        query: str,
        chat_response: str,
        top_k: int,
        response_time_ms: None | int = None,
        source_document_count: int = 0,
        success: bool = True,
        error_message: None | str = None,
    ) -> None | QueryHistoryResponse:
        """Create a new query history record.

        Args:
            query: The user's query string
            chat_response: The AI's response
            top_k: Number of documents retrieved
            response_time_ms: Response time in milliseconds
            source_document_count: Number of source documents used
            success: Whether the query was successful
            error_message: Error message if query failed

        Returns:
            QueryHistoryResponse: The created query history record, or None if failed
        """
        try:
            with Session(self.engine) as session:
                query_history = QueryHistory(
                    query=query,
                    chat_response=chat_response,
                    top_k=top_k,
                    response_time_ms=response_time_ms,
                    source_document_count=source_document_count,
                    success=success,
                    error_message=error_message,
                )

                session.add(query_history)
                session.commit()
                session.refresh(query_history)

                logger.info(f"Created query history with ID: {query_history.id}")
                return QueryHistoryResponse.model_validate(query_history)

        except Exception as e:
            logger.error(f"Failed to create query history: {e}")
            return None

    def create_source_document_history(
        self,
        query_id: UUID,
        content_preview: str,
        similarity_score: float,
        document_metadata: None | DocumentMetadata = None,
    ) -> None | SourceDocumentHistoryResponse:
        """Create a source document history record.

        Args:
            query_id: Reference to the query
            content_preview: Preview of the source document content
            similarity_score: Similarity score of the document to the query
            document_metadata: Document metadata as dictionary

        Returns:
            SourceDocumentHistoryResponse: The created record, or None if failed
        """
        try:
            with Session(self.engine) as session:
                metadata_json = None
                parsed_metadata = None
                if document_metadata is not None:
                    parsed_metadata = self._parse_document_metadata(document_metadata)
                    if parsed_metadata is not None:
                        metadata_json = json.dumps(
                            parsed_metadata.model_dump(mode="json")
                        )

                source_doc = SourceDocumentHistory(
                    query_id=query_id,
                    content_preview=content_preview,
                    similarity_score=similarity_score,
                    document_metadata=metadata_json,
                )

                session.add(source_doc)
                session.commit()
                session.refresh(source_doc)

                if source_doc.id is None:
                    raise ValueError("Source document history ID not generated")

                return SourceDocumentHistoryResponse(
                    id=source_doc.id,
                    content_preview=source_doc.content_preview,
                    similarity_score=source_doc.similarity_score,
                    document_metadata=parsed_metadata,
                    created_at=source_doc.created_at,
                )

        except Exception as e:
            logger.error(f"Failed to create source document history: {e}")
            return None

    def get_query_history_paginated(
        self, limit: int = 10, offset: int = 0
    ) -> QueryHistoryListResponse:
        """Get paginated query history records.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            list[QueryHistory]: List of query history records
        """
        try:
            with Session(self.engine) as session:
                statement = (
                    select(QueryHistory)
                    .order_by(desc(QueryHistory.created_at))
                    .limit(limit)
                    .offset(offset)
                )
                results = session.exec(statement).all()
                return QueryHistoryListResponse(
                    items=[
                        QueryHistoryResponse.model_validate(item) for item in results
                    ],
                    total_count=self.get_total_query_count(),
                    limit=limit,
                    offset=offset,
                )

        except Exception as e:
            logger.error(f"Failed to get paginated query history: {e}")
            return QueryHistoryListResponse(
                items=[],
                total_count=0,
                limit=limit,
                offset=offset,
            )

    def get_query_history_by_id(self, query_id: UUID) -> None | QueryHistoryResponse:
        """Get a specific query history record by ID.

        Args:
            query_id: The UUID of the query

        Returns:
            QueryHistory: The query history record, or None if not found
        """
        try:
            with Session(self.engine) as session:
                statement = select(QueryHistory).where(QueryHistory.id == query_id)
                result = session.exec(statement).first()
                return QueryHistoryResponse.model_validate(result) if result else None

        except Exception as e:
            logger.error(f"Failed to get query by ID {query_id}: {e}")
            return None

    def get_source_documents_by_query_id(
        self, query_id: UUID
    ) -> list[SourceDocumentHistoryResponse]:
        """Get source documents for a specific query.

        Args:
            query_id: The UUID of the query

        Returns:
            list[SourceDocumentHistoryResponse]: List of source documents
        """
        try:
            with Session(self.engine) as session:
                statement = select(SourceDocumentHistory).where(
                    SourceDocumentHistory.query_id == query_id
                )
                results = session.exec(statement).all()

                response_list = []
                for item in results:
                    if not item.id:
                        continue

                    parsed_metadata = None
                    if item.document_metadata:
                        try:
                            parsed_metadata = self._parse_document_metadata(
                                item.document_metadata
                            )
                        except (ValueError, SyntaxError, json.JSONDecodeError) as e:
                            logger.warning(
                                f"Failed to parse metadata for document {item.id}: {e}\n{item.document_metadata}"
                            )

                    response = SourceDocumentHistoryResponse(
                        id=item.id,
                        content_preview=item.content_preview,
                        similarity_score=item.similarity_score,
                        document_metadata=parsed_metadata,
                        created_at=item.created_at,
                    )
                    response_list.append(response)

                return response_list

        except Exception as e:
            logger.error(f"Failed to get source documents for query {query_id}: {e}")
            return []

    def get_total_query_count(self) -> int:
        """Get total number of queries.

        Returns:
            int: Total number of query records
        """
        try:
            with Session(self.engine) as session:
                statement = select(QueryHistory)
                results = session.exec(statement).all()
                return len(results)

        except Exception as e:
            logger.error(f"Failed to get total query count: {e}")
            return 0

    def get_successful_query_count(self) -> int:
        """Get number of successful queries.

        Returns:
            int: Number of successful query records
        """
        try:
            with Session(self.engine) as session:
                statement = select(QueryHistory).where(QueryHistory.success == True)  # noqa: E712
                results = session.exec(statement).all()
                return len(results)

        except Exception as e:
            logger.error(f"Failed to get successful query count: {e}")
            return 0

    def get_queries_with_response_time(self) -> list[QueryHistoryResponse]:
        """Get all queries that have response time recorded.

        Returns:
            list[QueryHistory]: List of queries with response time
        """
        try:
            with Session(self.engine) as session:
                statement = select(QueryHistory).where(
                    QueryHistory.response_time_ms != None  # noqa: E711
                )
                results = session.exec(statement).all()
                return [QueryHistoryResponse.model_validate(item) for item in results]

        except Exception as e:
            logger.error(f"Failed to get queries with response time: {e}")
            return []
