# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ultimate Advisor is a production-ready **Retrieval-Augmented Generation (RAG)** application built with FastAPI, LlamaIndex, ChromaDB, and SQLite. It provides an AI-powered Q&A system for Ultimate Frisbee rules using state-of-the-art AI models.

**✅ 100% Windows Native** - No Docker, no containers, runs directly on Windows 11.

## Technology Stack

- **Backend**: FastAPI, SQLModel, LlamaIndex
- **Vector Database**: ChromaDB (persistent local storage with HNSW indexing)
- **Query History**: SQLite (local relational database)
- **LLM**: Anthropic Claude (claude-sonnet-4-0)
- **Embeddings**: VoyageAI (voyage-3.5 - cost-effective, 1024 dimensions)
- **Package Management**: UV (not pip)
- **Frontend**: React 19 + Vite + TailwindCSS (in `frontend/` directory)

## Development Commands

### Environment Setup

```bash
# Virtual environment is managed by UV
uv sync                          # Install/sync all dependencies
uv venv                          # Create virtual environment if missing
```

### Running the Application

```bash
# Native Windows execution (no Docker)
uv run fastapi dev src/main.py --host 0.0.0.0 --port 8000

# Or for production
uv run fastapi run src/main.py --host 0.0.0.0 --port 8000
```

### Database Operations

```bash
# Initialize SQLite database tables (interactive prompts)
uv run python src/scripts/run_init_db.py

# Load embeddings from data/ folder into ChromaDB
uv run python src/scripts/run_load_embeddings.py
```

### Code Quality

```bash
# Linting with Ruff
uv run ruff check .              # Check for issues
uv run ruff check --fix .        # Auto-fix issues
uv run ruff format .             # Format code
```

### Testing

```bash
# Run tests with pytest
uv run pytest                    # Run all tests
uv run pytest tests/test_query_vector_store.py  # Run specific test
```

## Architecture

### Module Structure

The codebase follows a layered architecture pattern:

```
src/
├── main.py                     # FastAPI app entry point, SPA serving, logging
├── config.py                   # Settings (Pydantic BaseSettings with APP_ prefix)
├── dependencies.py             # Dependency injection for services
├── schemas.py                  # Shared Pydantic models
├── rag/                        # RAG module
│   ├── services.py            # Business logic (query, indexing)
│   ├── repositories.py        # Data access (ChromaDB, LLM setup)
│   └── routes.py              # API endpoints
└── history/                    # Query history tracking module
    ├── services.py            # History business logic
    ├── repositories.py        # SQLite database operations
    ├── models.py              # SQLModel tables
    ├── schemas.py             # Pydantic response models
    └── routes.py              # API endpoints
```

### Key Components

#### RAGRepository (src/rag/repositories.py)
- **Initialization**: Sets up Anthropic Claude + VoyageAI embeddings, ChromaDB persistent client
- **ChromaDB Client**: Uses `PersistentClient` to store vectors locally in `.chroma/` directory
- **Embedding Dimension**: Auto-detects embedding model output dimension (VoyageAI: 1024 dims)
- **Document Indexing**: Uses `SentenceSplitter` (chunk_size=256, overlap=20) optimized for small document collections
- **Query Processing**: Creates `VectorStoreIndex` from ChromaDB, retrieves top-K similar documents, generates responses via Claude
- **Collection**: Uses cosine similarity for vector search (HNSW algorithm)

#### RAGService (src/rag/services.py)
- Orchestrates RAG operations between repository and history service
- Tracks query performance metrics (response time, success/failure)
- Handles document indexing from directories or document lists

#### HistoryService (src/history/services.py)
- Persists query history, responses, source documents, and metadata to SQLite
- Provides query statistics (total queries, success rate, avg response time)

### Configuration (src/config.py)

Environment variables use `APP_` prefix:

**ChromaDB (Vector Store):**
- `APP_CHROMA_PERSIST_DIRECTORY` (default: `.chroma`) - Local directory for vector storage
- `APP_CHROMA_COLLECTION_NAME` (default: `ultimate_advisor_docs`) - Collection name

**SQLite (Query History):**
- `APP_HISTORY_DB_PATH` (default: `ultimate_advisor.db`) - SQLite database file path

**API Keys:**
- `APP_ANTHROPIC_API_KEY` - Anthropic API key from console.anthropic.com
- `APP_ANTHROPIC_MODEL` (default: claude-sonnet-4-0)
- `APP_VOYAGE_API_KEY` - VoyageAI API key from voyageai.com
- `APP_VOYAGE_MODEL` (default: voyage-3.5, includes 200M free tokens)
- `APP_EMBED_DIM` (default: 1024, VoyageAI dimension)

### API Routes

**RAG Endpoints** (`/api/rag`):
- `POST /api/rag/query` - Submit query, returns chat response + source documents
- `GET /api/rag/health` - Check RAG system health (ChromaDB, models, index)
- `GET /api/rag/documents/count` - Get total document count in vector store

**History Endpoints** (`/api/history`):
- `GET /api/history` - Paginated query history (limit, offset)
- `GET /api/history/{query_id}` - Get specific query details
- `GET /api/history/{query_id}/sources` - Get source documents for query
- `GET /api/history/statistics` - Query statistics

**Other Endpoints**:
- `GET /` - API info
- `GET /health` - General health check
- `GET /files/download/{filename}` - Download files from data/ directory

### Frontend Integration

The backend serves the React SPA:
- Production build: `frontend/dist/` mounted at root
- Assets: `/assets` serves `frontend/dist/assets`
- SPA routing: All non-API routes fall back to `index.html`
- CORS: Configured for localhost:3000 and localhost:5173

### Logging

- Logs saved to `logs/server_logs/{timestamp}.log`
- Request/response middleware logs all HTTP traffic
- Module-level loggers throughout codebase

## Important Notes

### Local Persistence

1. **ChromaDB Data**: All vector embeddings are stored locally in `.chroma/` directory
   - Automatically created on first run
   - Persists across application restarts
   - Can be deleted to start fresh (will need to re-index documents)

2. **SQLite Data**: Query history stored in `ultimate_advisor.db` file
   - Created automatically on first query
   - Single-file database (easy to backup/transfer)
   - Can be deleted to clear history

3. **First-time Setup**:
   - Run `uv sync` to install dependencies
   - Run `uv run python src/scripts/run_init_db.py` to create SQLite tables
   - Place PDF files in `data/` folder
   - Run `uv run python src/scripts/run_load_embeddings.py` to index documents

### ChromaDB Operations

- **Collection Management**: Collections are auto-created with `get_or_create_collection()`
- **Vector Search**: Uses HNSW algorithm with cosine similarity
- **Embedding Dimensions**: ChromaDB auto-detects dimensions from first insert
- **No Migration Needed**: If embedding model changes, ChromaDB will reject dimension mismatches (clear and re-index)

### Query Optimization

The query engine uses:
- `similarity_top_k` multiplied by 2 (capped at 15) for retrieval
- `response_mode="tree_summarize"` for better context synthesis
- `similarity_cutoff=0.6` to filter low-relevance documents
- Only returns the user-requested `top_k` documents in response

### Dependency Injection Pattern

Services are created via `dependencies.py`:
- `get_rag_repository()` - Singleton-like repository instance
- `get_rag_service()` - Creates service with dependencies injected
- `get_history_service()` - History service factory

This pattern allows for easy testing and swapping implementations.

## Common Tasks

### Changing AI Models

**To change the chat model:**
1. Update `APP_ANTHROPIC_MODEL` in `.env` (e.g., to `claude-opus-4-0` for maximum quality)
2. Restart backend: Stop and re-run `uv run fastapi dev src/main.py`

**To change the embedding model:**
1. Update `APP_VOYAGE_MODEL` in `.env` (options: `voyage-3.5`, `voyage-3.5-lite`, `voyage-3-large`)
2. If embedding dimensions change, delete `.chroma` directory
3. Re-run `uv run python src/scripts/run_load_embeddings.py` to re-index all documents

### Adding New API Endpoints

1. Define Pydantic request/response schemas in appropriate `schemas.py`
2. Add business logic in `services.py`
3. Add data access in `repositories.py` if needed
4. Create route handler in `routes.py`
5. Router is auto-included in `main.py` via `app.include_router()`

### Modifying Document Chunking

Edit `RAGRepository.index_documents()` in `src/rag/repositories.py`:
- `chunk_size`: Token limit per chunk (default 256)
- `chunk_overlap`: Overlap between chunks (default 20)
- `separator`: Sentence boundary (default ".\n")
- `paragraph_separator`: Document section boundary (default "\n\n\n")

### Running Tests

Tests are located in `tests/` directory:
- `test_query_vector_store.py`: Vector store query tests

Use `uv run pytest` with optional file/test path for specific tests.

### Clearing Data

**Clear vector embeddings:**
```python
# Via Python REPL
from src.rag.repositories import rag_repository
rag_repository.clear_index()
```

**Or manually:**
- Delete `.chroma/` directory
- Re-run embedding script to re-index

**Clear query history:**
- Delete `ultimate_advisor.db` file
- Re-run `uv run python src/scripts/run_init_db.py`

## API Keys and Costs

### Anthropic API
- Sign up: https://console.anthropic.com/
- Pricing: Pay-as-you-go (claude-sonnet-4-0 is cost-effective for most use cases)
- Rate limits: Check current limits in console

### VoyageAI API
- Sign up: https://www.voyageai.com/
- **Free tier**: 200 million tokens for `voyage-3.5`
- **After free tier**: $0.06 per million tokens
- Estimated cost for 100-page technical PDF: ~$0.003 (one-time indexing)

## Development Workflow

1. **Start backend**: `uv run fastapi dev src/main.py --host 0.0.0.0 --port 8000`
2. **Access UI**: http://localhost:8000
3. **API docs**: http://localhost:8000/docs
4. **Make changes**: Edit source files (auto-reload enabled in dev mode)
5. **Test**: `uv run pytest`
6. **Lint**: `uv run ruff check --fix .`

## Troubleshooting

**ChromaDB collection not found:**
- Collection is auto-created on first index operation
- Check `.chroma/` directory exists and is writable

**SQLite database locked:**
- Ensure only one application instance is running
- Close any DB browser tools accessing `ultimate_advisor.db`

**Dimension mismatch error:**
- Embedding model changed after initial indexing
- Delete `.chroma/` directory and re-index documents

**API key errors:**
- Verify `.env` file exists with correct API keys
- Check environment variables are loaded: `APP_ANTHROPIC_API_KEY` and `APP_VOYAGE_API_KEY`
