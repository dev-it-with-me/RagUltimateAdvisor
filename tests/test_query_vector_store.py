"""Test script for querying the RAG vector store.

If the vector store is empty, the test is skipped with instructions to run the
embedding load script first (no automatic indexing here to keep behavior explicit).
"""

import logging
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import settings, get_rag_service, RAGService, QueryRequest, QueryResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_query_vector_store() -> None:
    """Test querying the vector store (skips if empty)."""
    print("=== Testing Vector Store Query ===\n")

    # 1. Configuration
    print("1. Configuration:")
    print(f"   Vector table: {settings.VECTOR_TABLE_NAME}")
    print(f"   Chat model: {settings.CHAT_MODEL}")
    print(f"   Embedding model: {settings.EMBEDDING_MODEL}\n")

    # 2. Health check (pre)
    print("2. Pre-Query Health Check:")
    rag_service: RAGService = get_rag_service()
    health = rag_service.get_health_status()
    for k, v in health.items():
        print(f"   {k}: {'✓' if v else '✗'}")
    print()

    # 3. Ensure data present (no auto-index)
    print("3. Data Presence:")
    count = rag_service.get_document_count()
    if count == 0:
        msg = "Vector store empty. Run 'python src/scripts/run_load_embeddings.py' first to load embeddings."
        print(f"   {msg}\n")
        pytest.skip(msg)
    else:
        print(f"   Existing document count: {count}\n")

    # 4. Perform sample query
    print("4. Sample Query:")
    sample_query = "Summarize the dimensions of an ultimate frisbee field according to the WFDF rules."
    query_request = QueryRequest(query=sample_query, top_k=3)
    response: QueryResponse = rag_service.query(query_request)
    if response and response.chat_response:
        print("   Query success: ✓")
        print(f"   Retrieved {len(response.source_documents)} source documents:")
        for idx, doc in enumerate(response.source_documents, start=1):
            print(f"     {idx}. Score: {doc.score:.3f}")
            print(f"        Content: {doc.content[:100]}{'...' if len(doc.content) > 100 else ''}")
            if doc.metadata:
                print(f"        Metadata: {doc.metadata}")
        print(f"   Chat Response: {response.chat_response}")
    else:
        print("   Query returned no response (None)")
    print()

    # 5. Post-query health (require index)
    print("5. Post-Query Health (require index):")
    post_health = rag_service.get_health_status(include_index=True)
    for k, v in post_health.items():
        print(f"   {k}: {'✓' if v else '✗'}")
    print()

    print("=== Query Test Complete ===")
    print("\nTo manually run only this test:")
    print("pytest -k test_query_vector_store -s")


if __name__ == "__main__":  # Manual invocation
    test_query_vector_store()
