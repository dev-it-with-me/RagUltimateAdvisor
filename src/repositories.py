"""Repositories module for RAG database operations.

This module provides a communication layer for database operations in the RAG system,
including vector storage, document indexing, and query operations.
"""

import logging
from contextlib import suppress
from pathlib import Path
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
)
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
        self.storage_context: None | StorageContext = None
        self.index: None | VectorStoreIndex = None
        # Track the actual embedding dimension detected from the model
        self._actual_embed_dim: int | None = None
        self._setup_models()
        self._setup_database()

    def _setup_models(self) -> None:
        """Setup the LLM and embedding models and validate embedding dimension."""
        try:
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
                "Models configured: LLM=%s, Embedding=%s",
                settings.CHAT_MODEL,
                settings.EMBEDDING_MODEL,
            )

            # Detect actual embedding dimension - this is critical for vector store setup
            try:
                test_vector = Settings.embed_model.get_text_embedding("__dim_probe__")
                self._actual_embed_dim = len(test_vector)
                if self._actual_embed_dim != settings.EMBED_DIM:
                    logger.warning(
                        "Configured EMBED_DIM (%s) does not match model output dimension (%s). Using model output dimension.",
                        settings.EMBED_DIM,
                        self._actual_embed_dim,
                    )
                else:
                    logger.info(
                        "Embedding dimension confirmed: %s", self._actual_embed_dim
                    )
            except Exception as e:
                logger.error("Failed to probe embedding dimension: %s", e)
                logger.warning(
                    "Could not determine embedding dimension during setup; proceeding with configured EMBED_DIM=%s",
                    settings.EMBED_DIM,
                )
                self._actual_embed_dim = None

        except Exception as e:
            logger.error("Failed to setup models: %s", e)
            raise

    def _setup_database(self) -> None:
        """Setup the database connection, extension and vector store."""
        try:
            db_url = (
                f"postgresql://{settings.PG_USER}:{settings.PG_PASSWORD}"
                f"@{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DATABASE}"
            )
            self.engine = create_engine(db_url)
            if self.engine:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    logger.info("Database connection established")
                    # Ensure pgvector extension exists (idempotent)
                    with suppress(Exception):
                        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                        conn.commit()
                        logger.info("pgvector extension ensured")

            embed_dim = self._actual_embed_dim or settings.EMBED_DIM
            if self._actual_embed_dim is None:
                logger.warning(
                    "Using configured EMBED_DIM=%s (model dimension probe failed earlier)",
                    settings.EMBED_DIM,
                )

            # Initialize vector store but let it handle table creation
            self.vector_store = PGVectorStore.from_params(
                database=settings.PG_DATABASE,
                host=settings.PG_HOST,
                password=settings.PG_PASSWORD,
                port=str(settings.PG_PORT),
                user=settings.PG_USER,
                table_name=settings.VECTOR_TABLE_NAME,
                embed_dim=embed_dim,
            )
            logger.info(
                "Vector store configured with table '%s' (embed_dim=%s)",
                settings.VECTOR_TABLE_NAME,
                embed_dim,
            )
        except Exception as e:
            logger.error("Failed to setup database: %s", e)
            raise

    def index_documents(self, documents: list) -> bool:
        """Index documents into the vector store."""
        try:
            if not documents:
                logger.warning("No documents to index")
                return False
            logger.info(f"Indexing {len(documents)} documents")

            logger.info("Creating index from documents...")
            self.storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            self.index = VectorStoreIndex.from_documents(
                documents,
                storage_context=self.storage_context,
                embed_model=Settings.embed_model,
                show_progress=True,
            )
            logger.info("Documents indexed successfully")
            return True

        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            import traceback

            traceback.print_exc()
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
            # First check basic health (database, vector_store, models)
            health = self.health_check(require_index=False)
            basic_health = {k: v for k, v in health.items() if k != "index"}
            if not all(basic_health.values()):
                logger.error("System not ready for queries - basic components failed")
                logger.error(f"Health status: {health}")
                return None

            # Check if we have documents in the vector store
            doc_count = self.get_document_count()
            if doc_count == 0:
                logger.error("No documents in vector store - cannot perform queries")
                return None

            logger.info(f"Vector store contains {doc_count} documents")

            # Ensure index is initialized from vector store
            if not self.index:
                logger.info("Index not initialized, creating from vector store...")
                if self.vector_store:
                    self.index = VectorStoreIndex.from_vector_store(self.vector_store)
                    logger.info("✓ Index successfully created from vector store")
                else:
                    logger.error("Vector store not initialized")
                    return None

            # Perform the query
            logger.info(f"Executing query: '{query_text[:50]}...'")
            query_engine = self.index.as_query_engine(similarity_top_k=similarity_top_k)
            response = query_engine.query(query_text)

            logger.info("Query executed successfully")
            return str(response)

        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def get_document_count(self) -> int:
        """Get the total number of documents in the vector store.

        Returns:
            int: Number of documents
        """
        if not self.engine:
            logger.warning("get_document_count called before engine initialization")
            return 0
        try:
            with self.engine.connect() as conn:
                exists_result = conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.tables WHERE table_name = :tbl"
                    ),
                    {"tbl": f"data_{settings.VECTOR_TABLE_NAME}"},
                ).fetchone()
                if not exists_result:
                    logger.info(
                        "Vector table '%s' not found (no rows to count yet)",
                        settings.VECTOR_TABLE_NAME,
                    )
                    return 0
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM data_{settings.VECTOR_TABLE_NAME}")
                )
                row = result.fetchone()
                count = int(row[0]) if row and row[0] is not None else 0
                return count
        except Exception as e:
            logger.error(
                "Failed to get document count from table '%s': %s",
                settings.VECTOR_TABLE_NAME,
                e,
            )
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
                conn.execute(
                    text(f"DROP TABLE IF EXISTS data_{settings.VECTOR_TABLE_NAME}")
                )
                conn.commit()

            # Reinitialize vector store
            self._setup_database()
            self.index = None

            logger.info("Index cleared successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to clear index: {e}")
            return False

    def force_recreate_index(self) -> bool:
        """Force drop and recreate the vector table (dimension mismatch recovery)."""
        if not self.engine:
            logger.error("Cannot recreate index: engine not initialized")
            return False
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text(f"DROP TABLE IF EXISTS data_{settings.VECTOR_TABLE_NAME}")
                )
                conn.commit()
            logger.info(
                "Dropped existing vector table '%s'", settings.VECTOR_TABLE_NAME
            )
            # Re-create store with actual dim if available
            self.vector_store = None
            self.index = None
            self._setup_database()
            return True
        except Exception as e:
            logger.error("Failed to force recreate index: %s", e)
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
