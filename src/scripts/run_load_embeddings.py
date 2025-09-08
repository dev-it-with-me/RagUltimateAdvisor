"""Script to load and index documents into the RAG vector database.

This script processes all documents in the data folder and indexes them
into the vector store for RAG operations.
"""

import logging
import sys
from pathlib import Path
from typing import List

from llama_index.core.schema import Document

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings  # type: ignore
from repositories import rag_repository  # type: ignore

# Configure logging
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
            ".txt",
            ".md",
            ".docx",
            ".html",
            ".json",
            ".csv",
        }

    def get_document_files(self, directory_path: str) -> List[Path]:
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

    def load_specific_document(self, file_path: str) -> List[Document]:
        """Load a specific document file.

        Args:
            file_path: Path to the document file

        Returns:
            List of Document objects
        """
        try:
            from llama_index.core import SimpleDirectoryReader

            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"File {file_path} does not exist")
                return []

            # Use SimpleDirectoryReader with specific file
            reader = SimpleDirectoryReader(
                input_files=[str(file_path_obj)], recursive=False
            )

            documents = reader.load_data()
            logger.info(f"Loaded {len(documents)} documents from {file_path}")
            return documents

        except Exception as e:
            logger.error(f"Failed to load document {file_path}: {e}")
            return []


def load_and_index_documents() -> bool:
    """Main function to load and index documents.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting document loading and indexing process")

        # Initialize document loader
        loader = DocumentLoader()

        # Check repository health (don't require existing index for loading)
        health = rag_repository.health_check(require_index=False)
        logger.info(f"Repository health: {health}")

        if not all(health.values()):
            logger.error("Repository health check failed")
            return False

        # Get documents from data folder
        data_path = Path(settings.DATA_FOLDER)
        document_files = loader.get_document_files(str(data_path))

        if not document_files:
            logger.warning(f"No supported documents found in {data_path}")
            # Try to load the specific PDF file mentioned
            pdf_path = "/home/dev_it/dev/UltimateAdvisor/files/WFDF-Rules-of-Ultimate-2025-2028.pdf"
            logger.info(f"Attempting to load specific PDF: {pdf_path}")
            documents = loader.load_specific_document(pdf_path)

            if not documents:
                logger.error("No documents could be loaded")
                return False
        else:
            # Load all documents from data folder
            all_documents = []
            for file_path in document_files:
                logger.info(f"Loading document: {file_path}")
                docs = loader.load_specific_document(str(file_path))
                all_documents.extend(docs)

            documents = all_documents

        if not documents:
            logger.error("No documents were loaded")
            return False

        # Index documents
        logger.info(f"Indexing {len(documents)} documents into vector store")
        success = rag_repository.index_documents(documents)

        if success:
            logger.info("Document indexing completed successfully")
            # Log some statistics
            doc_count = rag_repository.get_document_count()
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

        success = load_and_index_documents()

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
