"""Repositories module for RAG database operations.

This module provides a communication layer for database operations in the RAG system,
including vector storage, document indexing, and query operations.
"""

import logging

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.schema import Document
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import settings

# Configure logging
logger = logging.getLogger(__name__)


class RAGRepository:
    """Repository class for RAG database operations."""

    def __init__(self) -> None:
        """Initialize the RAG repository with database connection and models."""
        self.engine: None | Engine = None
        self.vector_store: None | PGVectorStore = None
        self.index: None | VectorStoreIndex = None
        self._setup_models()
        self._setup_database()

    def _setup_models(self) -> None:
        """Setup the LLM and embedding models."""
        try:
            # Configure Ollama models
            Settings.llm = Ollama(
                model=settings.CHAT_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                request_timeout=120.0,
            )
            Settings.embed_model = OllamaEmbedding(
                model_name=settings.EMBEDDING_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
            )
            logger.info(
                f"Models configured: LLM={settings.CHAT_MODEL}, Embedding={settings.EMBEDDING_MODEL}"
            )
        except Exception as e:
            logger.error(f"Failed to setup models: {e}")
            raise

    def _setup_database(self) -> None:
        """Setup the database connection and vector store."""
        try:
            # Create SQLAlchemy engine
            db_url = f"postgresql://{settings.PG_USER}:{settings.PG_PASSWORD}@{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DATABASE}"
            self.engine = create_engine(db_url)

            # Test connection
            if self.engine:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    logger.info("Database connection established")

            # Setup vector store
            self.vector_store = PGVectorStore.from_params(
                database=settings.PG_DATABASE,
                host=settings.PG_HOST,
                password=settings.PG_PASSWORD,
                port=str(settings.PG_PORT),
                user=settings.PG_USER,
                table_name=settings.VECTOR_TABLE_NAME,
                embed_dim=settings.EMBED_DIM,
            )
            logger.info(
                f"Vector store configured with table: {settings.VECTOR_TABLE_NAME}"
            )

        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise

    def index_documents(self, documents: list[Document]) -> bool:
        """Index documents into the vector store.

        Args:
            documents: List of documents to index

        Returns:
            bool: True if indexing was successful
        """
        try:
            if not self.vector_store:
                raise ValueError("Vector store not initialized")

            self.index = VectorStoreIndex.from_documents(
                documents, vector_store=self.vector_store
            )
            logger.info(f"Indexed {len(documents)} documents successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            return False

    def index_documents_from_directory(self, directory_path: str) -> bool:
        """Index all documents from a directory.

        Args:
            directory_path: Path to the directory containing documents

        Returns:
            bool: True if indexing was successful
        """
        try:
            documents = SimpleDirectoryReader(directory_path).load_data()
            return self.index_documents(documents)

        except Exception as e:
            logger.error(
                f"Failed to index documents from directory {directory_path}: {e}"
            )
            return False

    def query(self, query_text: str, similarity_top_k: int = 5) -> None | str:
        """Query the RAG system.

        Args:
            query_text: The query text
            similarity_top_k: Number of similar documents to retrieve

        Returns:
            Optional[str]: The response text or None if query failed
        """
        try:
            # Check health requiring an index for queries
            health = self.health_check(require_index=True)
            if not all(health.values()):
                logger.error("System not ready for queries")
                return None

            if not self.index:
                logger.warning(
                    "Index not initialized, attempting to load from vector store"
                )
                if self.vector_store:
                    self.index = VectorStoreIndex.from_vector_store(self.vector_store)
                else:
                    raise ValueError("Vector store not initialized")

            query_engine = self.index.as_query_engine(similarity_top_k=similarity_top_k)
            response = query_engine.query(query_text)

            logger.info(f"Query executed successfully: '{query_text[:50]}...'")
            return str(response)

        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            return None

    def get_document_count(self) -> int:
        """Get the total number of documents in the vector store.

        Returns:
            int: Number of documents
        """
        try:
            if not self.engine:
                return 0

            # Query the actual table to count documents
            with self.engine.connect() as conn:
                # First check if table exists
                try:
                    result = conn.execute(
                        text(f"SELECT COUNT(*) FROM {settings.VECTOR_TABLE_NAME}")
                    )
                    row = result.fetchone()
                    if row is not None:
                        count = row[0]
                        return int(count)
                    else:
                        return 0
                except Exception:
                    # Table doesn't exist yet
                    logger.info(
                        f"Table {settings.VECTOR_TABLE_NAME} does not exist yet"
                    )
                    return 0

        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            return 0

    def clear_index(self) -> bool:
        """Clear all documents from the index.

        Returns:
            bool: True if clearing was successful
        """
        try:
            if not self.vector_store or not self.engine:
                return False

            # Drop and recreate the table
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {settings.VECTOR_TABLE_NAME}"))
                conn.commit()

            # Reinitialize vector store
            self._setup_database()
            self.index = None

            logger.info("Index cleared successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to clear index: {e}")
            return False

    def health_check(self, require_index: bool = False) -> dict:
        """Perform a health check on the repository.

        Args:
            require_index: Whether to require an existing index for the check

        Returns:
            dict: Health check results
        """
        health = {
            "database": False,
            "vector_store": False,
            "models": False,
            "index": False,
        }

        try:
            # Check database connection
            if self.engine:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                health["database"] = True

            # Check vector store
            health["vector_store"] = self.vector_store is not None

            # Check models
            health["models"] = (
                Settings.llm is not None and Settings.embed_model is not None
            )

            # Check index (only if required)
            if require_index:
                health["index"] = self.index is not None
            else:
                # For document loading, index can be None initially
                health["index"] = True  # We'll create it if needed

        except Exception as e:
            logger.error(f"Health check failed: {e}")

        return health


# Global repository instance
rag_repository = RAGRepository()
