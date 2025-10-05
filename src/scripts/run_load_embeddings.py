"""Script to load and index documents into the RAG vector database.

This script processes all documents in the data folder and indexes them
into the vector store for RAG operations.
"""

import logging
import sys
from pathlib import Path

from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config import settings
from src.dependencies import get_rag_service
from src.rag import RAGService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("load_embeddings.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class DocumentLoader:
    """Handles loading and processing of documents."""

    def __init__(self) -> None:
        """Initialize the document loader."""
        self.supported_extensions = {
            ".pdf",
        }

    def get_document_files(self, directory_path: str) -> list[Path]:
        """Get all supported document files from the directory.

        Args:
            directory_path: Path to the directory containing documents

        Returns:
            List of Path objects for supported document files
        """
        directory = Path(directory_path)

        if not directory.exists():
            logger.warning(f"Directory {directory_path} does not exist")
            return []

        if not directory.is_dir():
            logger.error(f"Path {directory_path} is not a directory")
            return []

        document_files = []
        for file_path in directory.rglob("*"):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in self.supported_extensions
            ):
                document_files.append(file_path)

        logger.info(f"Found {len(document_files)} document files in {directory_path}")
        return document_files

    def load_specific_document(self, file_path: Path) -> list[Document]:
        """Load a specific document file.

        Args:
            file_path: Path to the document file

        Returns:
            List of Document objects
        """
        try:
            if not file_path.exists():
                logger.error(f"File {file_path} does not exist")
                return []

            reader = SimpleDirectoryReader(
                input_files=[str(file_path)], recursive=False
            )

            documents = reader.load_data()
            logger.info(f"Loaded {len(documents)} documents from {file_path}")
            return documents

        except Exception as e:
            logger.error(f"Failed to load document {file_path}: {e}")
            return []


def load_and_index_documents(rag_service: RAGService) -> bool:
    """Main function to load and index documents.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting document loading and indexing process")

        loader = DocumentLoader()

        health = rag_service.get_health_status(include_index=False)
        logger.info(f"Repository health: {health}")

        if not all(health.values()):
            logger.error("Repository health check failed")
            return False

        data_path = Path(settings.DATA_FOLDER)
        document_files = loader.get_document_files(str(data_path))

        all_documents = []
        for file_path in document_files:
            logger.info(f"Loading document: {file_path}")
            docs = loader.load_specific_document(file_path)
            all_documents.extend(docs)

        if not all_documents:
            logger.error("No documents were loaded")
            return False

        logger.info(f"Indexing {len(all_documents)} documents into vector store")
        success = rag_service.index_documents(all_documents)

        if success:
            logger.info("Document indexing completed successfully")
            doc_count = rag_service.get_document_count()
            logger.info(f"Total documents in vector store: {doc_count}")
        else:
            logger.error("Document indexing failed")

        return success

    except Exception as e:
        logger.error(f"Document loading and indexing failed: {e}")
        return False


def main() -> None:
    """Main entry point."""
    try:
        logger.info("=" * 50)
        logger.info("Ultimate Advisor - Document Loading Script")
        logger.info("=" * 50)
        rag_service: RAGService = get_rag_service()

        success = load_and_index_documents(rag_service)

        if success:
            logger.info("✓ Document loading and indexing completed successfully")
            sys.exit(0)
        else:
            logger.error("✗ Document loading and indexing failed")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
