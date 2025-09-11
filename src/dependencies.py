"""
Dependency injection setup for RAG components.
"""

from src.history import HistoryService
from src.rag import RAGRepository, RAGService


def get_rag_repository() -> RAGRepository:
    return RAGRepository()


def get_history_service() -> HistoryService:
    return HistoryService()


def get_rag_service() -> RAGService:
    return RAGService(
        rag_repository=get_rag_repository(), history_service=get_history_service()
    )
