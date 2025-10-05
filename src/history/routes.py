from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from .dependencies import get_history_service
from .schemas import (
    QueryDetailResponse,
    QueryHistoryListResponse,
    QueryStatisticsResponse,
    SourceDocumentHistoryResponse,
)
from .services import HistoryService

history_router = APIRouter(prefix="/history", tags=["History"])


@history_router.get("/queries", response_model=QueryHistoryListResponse)
async def get_query_history(
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    history_service: HistoryService = Depends(get_history_service),
) -> QueryHistoryListResponse:
    """
    Get paginated query history.

    Args:
        limit: Maximum number of queries to return (1-100)
        offset: Number of queries to skip for pagination
        history_service: The history service dependency

    Returns:
        QueryHistoryListResponse: Paginated list of query history
    """
    return history_service.get_query_history(limit=limit, offset=offset)


@history_router.get("/queries/{query_id}", response_model=QueryDetailResponse)
async def get_query_by_id(
    query_id: UUID,
    history_service: HistoryService = Depends(get_history_service),
) -> QueryDetailResponse:
    """
    Get a specific query by its ID along with source documents.

    Args:
        query_id: The UUID of the query to retrieve
        history_service: The history service dependency

    Returns:
        QueryDetailResponse: Detailed query information with source documents
    """
    query_history = history_service.get_query_by_id(query_id)
    if not query_history:
        raise HTTPException(status_code=404, detail=f"Query not found: {query_id}")

    source_documents = history_service.get_source_documents_for_query(query_id)

    return QueryDetailResponse(
        query_history=query_history, source_documents=source_documents
    )


@history_router.get(
    "/queries/{query_id}/sources", response_model=list[SourceDocumentHistoryResponse]
)
async def get_source_documents_for_query(
    query_id: UUID,
    history_service: HistoryService = Depends(get_history_service),
) -> list[SourceDocumentHistoryResponse]:
    """
    Get source documents used for a specific query.

    Args:
        query_id: The UUID of the query
        history_service: The history service dependency

    Returns:
        list[SourceDocumentHistoryResponse]: List of source documents used in the query
    """
    query_history = history_service.get_query_by_id(query_id)
    if not query_history:
        raise HTTPException(status_code=404, detail=f"Query not found: {query_id}")

    return history_service.get_source_documents_for_query(query_id)


@history_router.get("/statistics", response_model=QueryStatisticsResponse)
async def get_query_statistics(
    history_service: HistoryService = Depends(get_history_service),
) -> QueryStatisticsResponse:
    """
    Get statistics about query history.

    Args:
        history_service: The history service dependency

    Returns:
        QueryStatisticsResponse: Statistics including total queries, success rate, and avg response time
    """
    return history_service.get_query_statistics()
