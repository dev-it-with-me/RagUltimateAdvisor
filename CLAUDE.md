# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ultimate Advisor is a production-ready **Retrieval-Augmented Generation (RAG)** application built with FastAPI, LlamaIndex, and PostgreSQL+pgvector. It provides an AI-powered Q&A system for Ultimate Frisbee rules using state-of-the-art AI models.

## Technology Stack

- **Backend**: FastAPI, SQLModel, LlamaIndex
- **Database**: PostgreSQL 17 with pgvector extension
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
# With Docker (recommended)
docker-compose up -d             # Start all services (PostgreSQL + Backend)
docker-compose logs -f           # Monitor logs
docker-compose down              # Stop all services

# Local development (requires PostgreSQL running)
uv run fastapi dev src/main.py --host 0.0.0.0 --port 8000
```

### Database Operations

```bash
# Initialize database tables (interactive prompts)
uv run python src/scripts/run_init_db.py

# Load embeddings from data/ folder into vector store
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
│   ├── repositories.py        # Data access (vector store, LLM setup)
│   └── routes.py              # API endpoints
└── history/                    # Query history tracking module
    ├── services.py            # History business logic
    ├── repositories.py        # Database operations
    ├── models.py              # SQLModel tables
    ├── schemas.py             # Pydantic response models
    └── routes.py              # API endpoints
```

### Key Components

#### RAGRepository (src/rag/repositories.py)
- **Initialization**: Sets up Anthropic Claude + VoyageAI embeddings, PostgreSQL+pgvector connection
- **Embedding Dimension**: Auto-detects embedding model output dimension (VoyageAI: 1024 dims)
- **Document Indexing**: Uses `SentenceSplitter` (chunk_size=256, overlap=20) optimized for small document collections
- **Query Processing**: Creates `VectorStoreIndex` from vector store, retrieves top-K similar documents, generates responses via Claude

#### RAGService (src/rag/services.py)
- Orchestrates RAG operations between repository and history service
- Tracks query performance metrics (response time, success/failure)
- Handles document indexing from directories or document lists

#### HistoryService (src/history/services.py)
- Persists query history, responses, source documents, and metadata
- Provides query statistics (total queries, success rate, avg response time)

### Configuration (src/config.py)

Environment variables use `APP_` prefix:
- `APP_PG_HOST`, `APP_PG_PORT`, `APP_PG_USER`, `APP_PG_PASSWORD`, `APP_PG_DATABASE`
- `APP_ANTHROPIC_API_KEY` - Anthropic API key from console.anthropic.com
- `APP_ANTHROPIC_MODEL` (default: claude-sonnet-4-0)
- `APP_VOYAGE_API_KEY` - VoyageAI API key from voyageai.com
- `APP_VOYAGE_MODEL` (default: voyage-3.5, includes 200M free tokens)
- `APP_VECTOR_TABLE_NAME` (default: documents)
- `APP_EMBED_DIM` (default: 1024, VoyageAI dimension)

### API Routes

**RAG Endpoints** (`/api/rag`):
- `POST /api/rag/query` - Submit query, returns chat response + source documents
- `GET /api/rag/health` - Check RAG system health (DB, vector store, models, index)
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

### Vector Store Operations

1. **First-time Setup**: Always run `run_init_db.py` before `run_load_embeddings.py`
2. **Document Loading**: Place PDF files in `data/` folder before running embedding script
3. **Embedding Dimension Mismatch**: If you change embedding models, the repository will auto-detect dimension. If table already exists with wrong dimension, use `force_recreate_index()` to drop and recreate the vector table.

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

### Docker Compose Services

1. **db**: PostgreSQL 17 with pgvector extension
2. **backend**: FastAPI app with UV package manager

The backend connects to Anthropic and VoyageAI APIs - no local model serving required.

## Common Tasks

### Changing AI Models

**To change the chat model:**
1. Update `APP_ANTHROPIC_MODEL` in `.env` (e.g., to `claude-opus-4-0` for maximum quality)
2. Restart backend: `docker-compose restart backend`

**To change the embedding model:**
1. Update `APP_VOYAGE_MODEL` in `.env` (options: `voyage-3.5`, `voyage-3.5-lite`, `voyage-3-large`)
2. If embedding dimensions change, you must recreate the vector table
3. Re-run `run_load_embeddings.py` to re-index all documents

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
