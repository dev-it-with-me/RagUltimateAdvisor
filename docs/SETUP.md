# Setup Guide

## Prerequisites

### System Requirements

- **Operating System**: Windows 11 (Native, no Docker required)
- **Python**: 3.12 or higher
- **Node.js**: 18.x or higher (for frontend development)
- **Storage**: ~500MB for dependencies + space for documents

### Required API Keys

You'll need accounts and API keys from:

1. **Anthropic Claude**
   - Sign up: https://console.anthropic.com/
   - Get API key from the console
   - Pricing: Pay-as-you-go

2. **VoyageAI**
   - Sign up: https://www.voyageai.com/
   - Get API key from dashboard
   - Free tier: 200M tokens included

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/RagUltimateAdvisor.git
cd RagUltimateAdvisor
```

### 2. Install UV Package Manager

UV is the recommended package manager for Python dependencies:

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip (fallback)
pip install uv
```

### 3. Set Up Python Environment

```bash
# Create virtual environment
uv venv

# Install dependencies
uv sync
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
copy .env.example .env

# Edit with your API keys
notepad .env
```

Add your API keys:

```env
APP_ANTHROPIC_API_KEY=your_anthropic_key_here
APP_VOYAGE_API_KEY=your_voyage_key_here
```

### 5. Initialize the Database

```bash
# Create SQLite database tables
uv run python src/scripts/run_init_db.py
```

### 6. Add Your Documents

Place PDF documents in the `data/` directory:

```bash
# Create data directory if it doesn't exist
mkdir data

# Copy your PDF files
copy "path\to\your\documents\*.pdf" data\
```

### 7. Index Documents

Generate embeddings for your documents:

```bash
uv run python src/scripts/run_load_embeddings.py
```

This will:
- Read all PDFs from `data/` directory
- Generate embeddings using VoyageAI
- Store vectors in ChromaDB (`.chroma/` directory)

### 8. Start the Application

```bash
# Development mode (with auto-reload)
uv run fastapi dev src/main.py --host 0.0.0.0 --port 8000

# Production mode
uv run fastapi run src/main.py --host 0.0.0.0 --port 8000
```

### 9. Access the Application

- **Web UI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## Frontend Development (Optional)

If you want to modify the frontend:

### 1. Install Node Dependencies

```bash
cd frontend
pnpm install  # or npm install
```

### 2. Start Development Server

```bash
pnpm dev  # or npm run dev
```

The frontend dev server runs on http://localhost:5173

### 3. Build for Production

```bash
pnpm build  # or npm run build
```

The build output goes to `frontend/dist/` and is served by the FastAPI backend.

## Verification Steps

### 1. Check API Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "..."}
```

### 2. Check RAG System

```bash
curl http://localhost:8000/api/rag/health
```

Expected response:
```json
{
  "status": "healthy",
  "components": {
    "chromadb": "connected",
    "llm": "available",
    "embeddings": "available",
    "index": "loaded"
  }
}
```

### 3. Check Document Count

```bash
curl http://localhost:8000/api/rag/documents/count
```

Should return the number of indexed documents.

### 4. Test a Query

```bash
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"What is Ultimate Frisbee?\"}"
```

## Common Issues

### Issue: "API key not found"

**Solution**: Ensure `.env` file exists with correct keys:
```bash
# Check if .env exists
dir .env

# Verify environment variables
echo %APP_ANTHROPIC_API_KEY%
```

### Issue: "ChromaDB collection not found"

**Solution**: Re-index your documents:
```bash
uv run python src/scripts/run_load_embeddings.py
```

### Issue: "Port 8000 already in use"

**Solution**: Use a different port:
```bash
uv run fastapi dev src/main.py --port 8001
```

### Issue: "Module not found" errors

**Solution**: Ensure dependencies are installed:
```bash
uv sync
```

### Issue: "SQLite database locked"

**Solution**:
1. Stop all running instances
2. Close any database browser tools
3. Restart the application

## Next Steps

1. **Add more documents**: Place additional PDFs in `data/` and re-run indexing
2. **Customize the UI**: Modify React components in `frontend/src/`
3. **Adjust chunking**: Edit parameters in `src/rag/repositories.py`
4. **Monitor performance**: Check logs in `logs/server_logs/`
5. **Run tests**: Execute `uv run pytest`

## Deployment Considerations

For production deployment:

1. **Use environment-specific configs**:
   ```bash
   APP_RELOAD=false
   APP_LOG_LEVEL=INFO
   ```

2. **Set up proper logging**:
   - Configure log rotation
   - Set up monitoring alerts

3. **Implement authentication**:
   - Add API key authentication
   - Implement user management

4. **Configure CORS properly**:
   - Update allowed origins in `src/main.py`

5. **Use a production server**:
   ```bash
   uv run gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

6. **Set up HTTPS**:
   - Use a reverse proxy (nginx, Caddy)
   - Configure SSL certificates

## Support

For issues or questions:
1. Check the [Architecture Documentation](ARCHITECTURE.md)
2. Review the [API Documentation](API.md)
3. Check the [Environment Configuration](ENVIRONMENT.md)
4. Open an issue on GitHub