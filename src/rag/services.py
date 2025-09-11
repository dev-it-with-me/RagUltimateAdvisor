"""
Service layer for handling business logic related to RAG operations.
"""

import logging
import time
from pathlib import Path

from llama_index.core import (
    SimpleDirectoryReader,
)

from src.history import HistoryService
from src.schemas import QueryRequest, QueryResponse

from .repositories import RAGRepository

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, rag_repository: RAGRepository, history_service: HistoryService):
        self.rag_repository = rag_repository
        self.history_service = history_service

    def get_health_status(self, include_index: bool = False) -> dict:
        """Get the health status of the RAG repository.

        Returns:
            dict: Health status: 'vector_store', 'embedding_model', 'chat_model'
        """
        return self.rag_repository.health_check(require_index=include_index)

    def get_document_count(self) -> int:
        """Get the total number of documents in the vector store.

        Returns:
            int: Total document count
        """
        return self.rag_repository.get_document_count()

    def index_documents(self, documents: list) -> bool:
        """Index a list of documents.

        Args:
            documents: List of Document objects to index

        Returns:
            bool: True if indexing was successful
        """
        try:
            if not documents:
                logger.warning("No documents to index")
                return False
            logger.info(f"Indexing {len(documents)} documents")
            return self.rag_repository.index_documents(documents)
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            return False

    def index_documents_from_directory(self, directory_path: Path) -> bool:
        """Index all documents from a directory.

        Args:
            directory_path: Path to the directory containing documents

        Returns:
            bool: True if indexing was successful
        """
        try:
            documents = SimpleDirectoryReader(directory_path).load_data()
            return self.rag_repository.index_documents(documents)

        except Exception as e:
            logger.error(
                f"Failed to index documents from directory {directory_path}: {e}"
            )
            return False

    def query(self, query_request: QueryRequest) -> QueryResponse:
        """Query the vector store and get a response from the chat model.

        Args:
            query_request: The query request object containing query details

        Returns:
            QueryResponse: The response object containing query results
        """
        start_time = time.time()
        error_message = None
        success = True
        result = QueryResponse(
            chat_response="Error processing query.", source_documents=[]
        )
        try:
            result = self.rag_repository.query(query_request)
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Query failed for '{query_request}': {e}")
        finally:
            response_time_ms = int((time.time() - start_time) * 1000)
            try:
                self.history_service.save_query_history(
                    query_request=query_request,
                    query_response=result,
                    response_time_ms=response_time_ms,
                    success=success,
                    error_message=error_message,
                )

            except Exception as e:
                logger.error(f"Failed to save query history: {e}")
        return result
