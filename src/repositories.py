"""Repositories module for RAG database operations.

This module provides a communication layer for database operations in the RAG system,
including vector storage, document indexing, and query operations.
"""

import logging
from contextlib import suppress
import uuid
import json

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

            # Detect actual embedding dimension once to avoid mismatches with configured EMBED_DIM
            with suppress(Exception):  # Non fatal; we'll log if it fails below
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

            if self._actual_embed_dim is None:
                logger.warning(
                    "Could not determine embedding dimension during setup; proceeding with configured EMBED_DIM=%s",
                    settings.EMBED_DIM,
                )
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

            # Proactively create underlying table if private helper exists (future-proof)
            with suppress(Exception):
                create_fn = getattr(
                    self.vector_store, "_create_tables", None
                ) or getattr(self.vector_store, "_create_table", None)
                if callable(create_fn):
                    create_fn()
                    logger.info(
                        "Proactively ensured vector table '%s' exists",
                        settings.VECTOR_TABLE_NAME,
                    )

            # List current tables for diagnostics
            self._log_existing_tables()
            # After initialization, if mismatch persists with an existing table, offer to recreate automatically.
            self._maybe_recreate_on_dim_mismatch()
        except Exception as e:
            logger.error("Failed to setup database: %s", e)
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
            logger.info("Indexed %s documents successfully", len(documents))
            # Post-index: verify table exists & log row count immediately
            with suppress(Exception):
                # Retry a few times in case table creation/commit is slightly delayed
                import time

                for attempt in range(5):
                    count = self.get_document_count()
                    if count > 0:
                        logger.info(
                            "Post-index document count observed (attempt %s): %s",
                            attempt + 1,
                            count,
                        )
                        break
                    if attempt < 4:
                        time.sleep(0.5 * (attempt + 1))
                else:
                    logger.warning(
                        "Post-index document count still 0 after retries; check table name, permissions, or embedding dimension."
                    )
                    # Fallback: attempt manual persistence if table truly absent
                    if self.engine:
                        self._fallback_persist(documents)
                self._log_existing_tables()
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
        if not self.engine:
            logger.warning("get_document_count called before engine initialization")
            return 0
        try:
            with self.engine.connect() as conn:
                # Determine if table exists
                exists_result = conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.tables WHERE table_name = :tbl"
                    ),
                    {"tbl": settings.VECTOR_TABLE_NAME},
                ).fetchone()
                if not exists_result:
                    logger.info(
                        "Vector table '%s' not found (no rows to count yet)",
                        settings.VECTOR_TABLE_NAME,
                    )
                    return 0
                # If we know actual embed dim, ensure column type matches expected length
                if self._actual_embed_dim is not None:
                    with suppress(Exception):
                        dim_row = conn.execute(
                            text(
                                "SELECT atttypmod FROM pg_attribute a JOIN pg_class c ON a.attrelid=c.oid JOIN pg_namespace n ON c.relnamespace=n.oid "
                                "WHERE c.relname=:tbl AND a.attname='embedding' AND a.attnum>0 AND NOT a.attisdropped"
                            ),
                            {"tbl": settings.VECTOR_TABLE_NAME},
                        ).fetchone()
                        # pgvector stores dimension in atttypmod -4 (vector(dim)) => atttypmod = dim + 4
                        if dim_row and dim_row[0] is not None:
                            stored_dim = dim_row[0] - 4
                            if stored_dim != self._actual_embed_dim:
                                logger.warning(
                                    "Existing table '%s' embedding dim %s != model dim %s; recreate advised.",
                                    settings.VECTOR_TABLE_NAME,
                                    stored_dim,
                                    self._actual_embed_dim,
                                )
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM {settings.VECTOR_TABLE_NAME}")
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

    def _log_existing_tables(self) -> None:
        """Log current user tables (diagnostic)."""
        if not self.engine:
            return
        with suppress(Exception):
            with self.engine.connect() as conn:
                rows = conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
                    )
                ).fetchall()
                names = [r[0] for r in rows]
                logger.info("Public schema tables: %s", names)
                # If expected table missing but others exist, highlight
                if (
                    settings.VECTOR_TABLE_NAME not in names
                    and len(names) > 0
                    and self._actual_embed_dim is not None
                ):
                    logger.warning(
                        "Expected vector table '%s' missing while other tables exist",  # noqa: E501
                        settings.VECTOR_TABLE_NAME,
                    )

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

    def force_recreate_index(self) -> bool:
        """Force drop and recreate the vector table (dimension mismatch recovery)."""
        if not self.engine:
            logger.error("Cannot recreate index: engine not initialized")
            return False
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {settings.VECTOR_TABLE_NAME}"))
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

    def _maybe_recreate_on_dim_mismatch(self) -> None:
        """Detect dimension mismatch and auto-recreate table if empty or unusable."""
        if self._actual_embed_dim is None or not self.engine:
            return
        try:
            with self.engine.connect() as conn:
                # Check if table exists
                exists = conn.execute(
                    text("SELECT 1 FROM information_schema.tables WHERE table_name=:t"),
                    {"t": settings.VECTOR_TABLE_NAME},
                ).fetchone()
                if not exists:
                    return  # nothing to do
                # Fetch stored dim
                dim_row = conn.execute(
                    text(
                        "SELECT atttypmod FROM pg_attribute a JOIN pg_class c ON a.attrelid=c.oid JOIN pg_namespace n ON c.relnamespace=n.oid "
                        "WHERE c.relname=:tbl AND a.attname='embedding' AND a.attnum>0 AND NOT a.attisdropped"
                    ),
                    {"tbl": settings.VECTOR_TABLE_NAME},
                ).fetchone()
                if not dim_row or dim_row[0] is None:
                    return
                stored_dim = dim_row[0] - 4
                if stored_dim != self._actual_embed_dim:
                    # Check if table is empty; if so, auto drop & recreate
                    row = conn.execute(
                        text(f"SELECT COUNT(*) FROM {settings.VECTOR_TABLE_NAME}")
                    ).fetchone()
                    count = int(row[0]) if row and row[0] is not None else 0
                    if count == 0:
                        logger.warning(
                            "Auto-recreating empty vector table '%s' due to dimension mismatch (stored=%s, model=%s)",
                            settings.VECTOR_TABLE_NAME,
                            stored_dim,
                            self._actual_embed_dim,
                        )
                        conn.execute(
                            text(f"DROP TABLE IF EXISTS {settings.VECTOR_TABLE_NAME}")
                        )
                        conn.commit()
                        # Recreate via vector_store re-init
                        self.vector_store = PGVectorStore.from_params(
                            database=settings.PG_DATABASE,
                            host=settings.PG_HOST,
                            password=settings.PG_PASSWORD,
                            port=str(settings.PG_PORT),
                            user=settings.PG_USER,
                            table_name=settings.VECTOR_TABLE_NAME,
                            embed_dim=self._actual_embed_dim,
                        )
                        logger.info(
                            "Recreated vector table '%s' with embed_dim=%s",
                            settings.VECTOR_TABLE_NAME,
                            self._actual_embed_dim,
                        )
        except Exception as e:
            logger.error("Dimension mismatch recreation check failed: %s", e)

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

    # ---------------- Fallback Logic -----------------
    def _fallback_persist(self, documents: list[Document]) -> None:
        """Fallback path: create table manually and insert embeddings if vector store failed.

        This should rarely run; only when PGVectorStore didn't create a table.
        """
        if not self.engine:
            return
        if self._actual_embed_dim is None:
            logger.error(
                "Cannot fallback persist: unknown embedding dimension (model probe failed)"
            )
            return
        try:
            with self.engine.begin() as conn:  # transaction
                # Create table manually if absent
                conn.execute(
                    text(
                        f"CREATE TABLE IF NOT EXISTS {settings.VECTOR_TABLE_NAME} ("
                        "id UUID PRIMARY KEY, "
                        "content TEXT NOT NULL, "
                        f"embedding vector({self._actual_embed_dim}) NOT NULL, "
                        "metadata JSONB)"
                    )
                )
            # Insert rows (batch) with embeddings
            rows_inserted = 0
            with self.engine.begin() as conn:
                for doc in documents:
                    text_content = (
                        getattr(doc, "text", None)
                        or getattr(doc, "get_content", lambda: "")()
                    )
                    if not text_content:
                        continue
                    embedding = Settings.embed_model.get_text_embedding(
                        text_content[:5000]
                    )  # truncate to avoid huge tokens
                    # Prepare metadata
                    meta = {}
                    for attr in ("metadata", "extra_info"):
                        with suppress(Exception):
                            data = getattr(doc, attr, None)
                            if isinstance(data, dict):
                                meta.update(data)
                    conn.execute(
                        text(
                            f"INSERT INTO {settings.VECTOR_TABLE_NAME} (id, content, embedding, metadata) VALUES (:id, :content, :embedding, :metadata)"
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "content": text_content,
                            "embedding": embedding,
                            "metadata": json.dumps(meta),
                        },
                    )
                    rows_inserted += 1
            logger.warning(
                "Fallback persistence inserted %s rows into manually created table '%s'",
                rows_inserted,
                settings.VECTOR_TABLE_NAME,
            )
            logger.warning(
                "You should investigate why PGVectorStore did not create/manage the table; continuing with manual table."  # noqa: E501
            )
        except Exception as e:
            logger.error("Fallback persistence failed: %s", e)


# Global repository instance
rag_repository = RAGRepository()
