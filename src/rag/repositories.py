"""Repositories module for RAG database operations.

This module provides a communication layer for database operations in the RAG system,
including vector storage, document indexing, and query operations.
"""

import logging
import traceback
from contextlib import suppress

from llama_index.core import (
    Settings,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config import settings
from src.schemas import DocumentMetadata, QueryRequest, QueryResponse, SourceDocument

logger = logging.getLogger(__name__)


class RAGRepository:
    """Repository class for RAG database operations."""

    def __init__(self) -> None:
        """Initialize the RAG repository with database connection and models."""
        self.engine: None | Engine = None
        self.vector_store: None | PGVectorStore = None
        self.storage_context: None | StorageContext = None
        self.index: None | VectorStoreIndex = None
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
            self.engine = create_engine(settings.database_url, echo=False)
            if self.engine:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    logger.info("Database connection established")
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
        """Index documents into the vector store.

        Optimized for small document collections (single document with ~17 pages).
        Uses smaller chunk sizes and reduced overlap for better granularity.
        """
        try:
            logger.info("Creating index from documents...")
            logger.info(f"Number of documents to index: {len(documents)}")

            text_splitter = SentenceSplitter(
                chunk_size=256,
                chunk_overlap=20,
                separator=".\n",
                paragraph_separator="\n\n\n",
            )

            Settings.text_splitter = text_splitter

            self.storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )

            self.index = VectorStoreIndex.from_documents(
                documents,
                storage_context=self.storage_context,
                embed_model=Settings.embed_model,
                show_progress=True,
                transformations=[text_splitter],
            )

            if self.index:
                try:
                    docstore = self.index.docstore
                    node_count = (
                        len(docstore.docs) if hasattr(docstore, "docs") else "unknown"
                    )
                    logger.info(
                        f"Documents indexed successfully - Created {node_count} text chunks"
                    )
                except Exception as e:
                    logger.info("Documents indexed successfully")
                    logger.debug(f"Could not retrieve node count: {e}")

            return True

        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            traceback.print_exc()
            return False

    def query(self, query_request: QueryRequest) -> QueryResponse:
        """Query the RAG system.

        Args:
            query_text: The query text
            similarity_top_k: Number of similar documents to retrieve

        Returns:
            Optional[dict]: Dictionary containing 'response' and 'source_documents' or None if query failed
        """
        try:
            health = self.health_check(require_index=False)
            basic_health = {k: v for k, v in health.items() if k != "index"}
            if not all(basic_health.values()):
                logger.error("System not ready for queries - basic components failed")
                logger.error(f"Health status: {health}")
                raise ValueError("System not healthy for queries")

            doc_count = self.get_document_count()
            if doc_count == 0:
                logger.error("No documents in vector store - cannot perform queries")
                raise ValueError("No documents in vector store")

            logger.info(f"Vector store contains {doc_count} documents")

            if not self.index:
                logger.info("Index not initialized, creating from vector store...")
                if self.vector_store:
                    self.index = VectorStoreIndex.from_vector_store(self.vector_store)
                    logger.info("✓ Index successfully created from vector store")
                else:
                    logger.error("Vector store not initialized")
                    raise ValueError("Vector store not initialized")

            logger.info(f"Executing query: '{query_request.query[:50]}...'")

            optimized_top_k = min(query_request.top_k * 2, 15)

            query_engine = self.index.as_query_engine(
                similarity_top_k=optimized_top_k,
                response_mode="tree_summarize",
                similarity_cutoff=0.6,
            )
            response = query_engine.query(query_request.query)

            source_documents: list[SourceDocument] = []
            if hasattr(response, "source_nodes") and response.source_nodes:
                top_nodes = response.source_nodes[: query_request.top_k]
                for node in top_nodes:
                    node_metadata = node.metadata if hasattr(node, "metadata") else {}
                    file_name = (
                        node_metadata.get("file_name")
                        or node_metadata.get("filename")
                        or node_metadata.get("file_path", "").split("/")[-1]
                        or "Unknown Document"
                    )
                    page = (
                        node_metadata.get("page")
                        or node_metadata.get("page_number")
                        or node_metadata.get("page_label")
                    )

                    if isinstance(page, str) and page.isdigit():
                        page = int(page)
                    elif not isinstance(page, int):
                        page = None

                    structured_metadata = DocumentMetadata(
                        file_name=file_name,
                        page=page,
                        source=node_metadata.get("file_path"),
                    )

                    source_doc = SourceDocument(
                        content=node.text,
                        score=getattr(node, "score", 0.0),
                        metadata=structured_metadata,
                    )
                    source_documents.append(source_doc)

            logger.info("Query executed successfully")
            return QueryResponse(
                chat_response=str(response), source_documents=source_documents
            )

        except Exception as e:
            logger.error(f"Failed to execute query: {e}")

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

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

            with self.engine.connect() as conn:
                conn.execute(
                    text(f"DROP TABLE IF EXISTS data_{settings.VECTOR_TABLE_NAME}")
                )
                conn.commit()

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
            if self.engine:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                health["database"] = True

            health["vector_store"] = self.vector_store is not None

            health["models"] = (
                Settings.llm is not None and Settings.embed_model is not None
            )

            if require_index:
                health["index"] = self.index is not None
            else:
                health["index"] = True

        except Exception as e:
            logger.error(f"Health check failed: {e}")

        return health


rag_repository = RAGRepository()
