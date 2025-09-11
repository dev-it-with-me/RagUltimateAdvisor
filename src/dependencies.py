"""
Dependency injection setup for RAG components.
"""

from .repositories import RAGRepository
from .services import RAGService


def get_rag_repository() -> RAGRepository:
    return RAGRepository()


def get_rag_service() -> RAGService:
    return RAGService(rag_repository=get_rag_repository())
