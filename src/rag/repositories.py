"""Repositories module for RAG database operations.

This module provides a communication layer for database operations in the RAG system,
including vector storage, document indexing, and query operations.
"""

import logging
import traceback

import chromadb
from llama_index.core import (
    Settings,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.llms.anthropic import Anthropic
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.config import settings
from src.schemas import DocumentMetadata, QueryRequest, QueryResponse, SourceDocument

logger = logging.getLogger(__name__)


class RAGRepository:
    """Repository class for RAG database operations."""

    def __init__(self) -> None:
        """Initialize the RAG repository with ChromaDB and models."""
        self.chroma_client: chromadb.PersistentClient | None = None
        self.chroma_collection: chromadb.Collection | None = None
        self.vector_store: ChromaVectorStore | None = None
        self.storage_context: StorageContext | None = None
        self.index: VectorStoreIndex | None = None
        self._actual_embed_dim: int | None = None
        self._setup_models()
        self._setup_vector_store()

    def _setup_models(self) -> None:
        """Setup the LLM and embedding models and validate embedding dimension."""
        try:
            Settings.llm = Anthropic(
                model=settings.ANTHROPIC_MODEL,
                api_key=settings.ANTHROPIC_API_KEY,
                max_tokens=4096,
            )
            Settings.embed_model = VoyageEmbedding(
                model_name=settings.VOYAGE_MODEL,
                voyage_api_key=settings.VOYAGE_API_KEY,
                truncation=True,
            )
            logger.info(
                "Models configured: LLM=%s (Anthropic), Embedding=%s (VoyageAI)",
                settings.ANTHROPIC_MODEL,
                settings.VOYAGE_MODEL,
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

    def _setup_vector_store(self) -> None:
        """Setup ChromaDB persistent client and vector store."""
        try:
            # Create ChromaDB persistent client
            persist_dir = str(settings.CHROMA_PERSIST_DIRECTORY)
            self.chroma_client = chromadb.PersistentClient(path=persist_dir)
            logger.info(f"ChromaDB client initialized at: {persist_dir}")

            # Get or create collection with cosine similarity
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                f"ChromaDB collection '{settings.CHROMA_COLLECTION_NAME}' ready"
            )

            # Create LlamaIndex ChromaVectorStore wrapper
            self.vector_store = ChromaVectorStore(
                chroma_collection=self.chroma_collection
            )
            logger.info("ChromaVectorStore initialized successfully")

        except Exception as e:
            logger.error(f"Failed to setup ChromaDB vector store: {e}")
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
        if not self.chroma_collection:
            logger.warning(
                "get_document_count called before ChromaDB collection initialization"
            )
            return 0
        try:
            count = self.chroma_collection.count()
            logger.debug(f"ChromaDB collection contains {count} documents")
            return count
        except Exception as e:
            logger.error(f"Failed to get document count from ChromaDB: {e}")
            return 0

    def clear_index(self) -> bool:
        """Clear all documents from the index.

        Returns:
            bool: True if clearing was successful
        """
        try:
            if not self.chroma_client or not self.chroma_collection:
                logger.error("ChromaDB not initialized")
                return False

            # Delete the collection
            collection_name = settings.CHROMA_COLLECTION_NAME
            self.chroma_client.delete_collection(name=collection_name)
            logger.info(f"Deleted ChromaDB collection '{collection_name}'")

            # Recreate the collection
            self.chroma_collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Recreated ChromaDB collection '{collection_name}'")

            # Recreate vector store wrapper
            self.vector_store = ChromaVectorStore(
                chroma_collection=self.chroma_collection
            )
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
            "chroma_client": False,
            "chroma_collection": False,
            "vector_store": False,
            "models": False,
            "index": False,
        }

        try:
            # Check ChromaDB client
            if self.chroma_client:
                try:
                    self.chroma_client.heartbeat()
                    health["chroma_client"] = True
                except Exception:
                    pass

            # Check ChromaDB collection
            health["chroma_collection"] = self.chroma_collection is not None

            # Check vector store wrapper
            health["vector_store"] = self.vector_store is not None

            # Check models
            health["models"] = (
                Settings.llm is not None and Settings.embed_model is not None
            )

            # Check index
            if require_index:
                health["index"] = self.index is not None
            else:
                health["index"] = True

        except Exception as e:
            logger.error(f"Health check failed: {e}")

        return health


rag_repository = RAGRepository()
