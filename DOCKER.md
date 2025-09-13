# Docker Setup Guide for Ultimate Advisor

This guide will help you run the entire Ultimate Advisor application stack using Docker with an integrated frontend-backend setup.

## Prerequisites

1. Docker and Docker Compose installed
2. NVIDIA Docker runtime (if using GPU acceleration for Ollama)
3. At least 8GB of available RAM
4. Internet connection for downloading models

## Architecture

The application uses an integrated approach where:
- **Frontend**: React SPA built as static files and served by FastAPI
- **Backend**: FastAPI serves both API endpoints and frontend static files
- **Database**: PostgreSQL with pgvector extension
- **AI**: Ollama for LLM and embedding models

## Quick Start

1. **Copy environment variables:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file with your preferred values:**
   ```bash
   # Update these values in .env
   APP_PG_PASSWORD=your_secure_password_here
   APP_PG_USER=ultimateadvisor
   APP_PG_DATABASE=ultimateadvisor_db
   ```

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database:**
   ```bash
   docker-compose exec backend uv run python src/scripts/run_init_db.py
   ```

5. **Load document embeddings:**
   ```bash
   docker-compose exec backend uv run python src/scripts/run_load_embeddings.py
   ```

6. **Access the application:**
   - **Complete Application**: http://localhost:8000 (frontend + API)
   - **API Documentation**: http://localhost:8000/docs
   - **API Health Check**: http://localhost:8000/health

## Services Overview

- **Database (PostgreSQL + pgvector)**: Port 5432
- **Ollama (LLM server)**: Port 11434
- **Application (FastAPI + React)**: Port 8000

## Development Workflow

### Making Backend Changes
- Edit files in `src/` directory
- FastAPI will automatically reload the server
- Frontend static files are served from the built version

### Making Frontend Changes

**For quick frontend development:**
```bash
# Option 1: Standalone development (recommended for active frontend work)
cd frontend
pnpm install
pnpm dev
# Frontend runs on http://localhost:5173 with API proxy to localhost:8000
```

**For integrated testing:**
```bash
# Option 2: Rebuild and restart backend container
docker-compose exec backend bash
# Then rebuild frontend or restart container to see changes
```

### Rebuilding Frontend in Docker
```bash
# Rebuild the entire application including frontend
docker-compose build backend
docker-compose up -d
```

## Useful Commands

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f ollama
```

### Restart services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Execute commands in containers
```bash
# Backend shell
docker-compose exec backend bash

# Run backend scripts
docker-compose exec backend uv run python src/scripts/run_init_db.py

# Check frontend build
docker-compose exec backend ls -la frontend/dist/
```

### Stop services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (DANGER: deletes data)
docker-compose down -v
```

## Production Deployment

For production, the current setup is already optimized:

1. ✅ Frontend is built as static files and served by FastAPI
2. ✅ Single port exposure (8000)
3. ✅ Optimized Docker builds with multi-stage
4. ✅ No unnecessary services

Additional production considerations:
- Set appropriate environment variables
- Use proper secrets management
- Add reverse proxy (nginx) if needed for SSL/load balancing
- Configure proper logging and monitoring

## Troubleshooting

### Frontend not loading
```bash
# Check if frontend was built correctly
docker-compose exec backend ls -la frontend/dist/

# Check backend logs for SPA routing
docker-compose logs backend | grep "Frontend"

# Rebuild if needed
docker-compose build backend
```

### Models not downloading
```bash
# Check Ollama logs
docker-compose logs ollama

# Manually pull models
docker-compose exec ollama ollama pull gemma3:4b
docker-compose exec ollama ollama pull embeddinggemma
```

### Database connection issues
```bash
# Check database logs
docker-compose logs db

# Test database connection
docker-compose exec backend uv run python -c "from src.config import settings; print(settings.database_url)"
```

### API routes not working
```bash
# Check if FastAPI is serving both frontend and API
curl http://localhost:8000/health
curl http://localhost:8000/docs
curl http://localhost:8000/  # Should return frontend HTML
```

### Port conflicts
If port 8000 is already in use, update the port mapping in docker-compose.yaml:
```yaml
ports:
  - "8001:8000"  # Change host port
```

### Reset everything
```bash
# Stop and remove everything
docker-compose down -v
docker system prune -f

# Start fresh
docker-compose up -d
```

## Development vs Production

### Development Mode
- Use standalone frontend development: `cd frontend && pnpm dev`
- FastAPI backend in Docker: `docker-compose up db ollama backend`
- Hot reloading for both frontend and backend

### Production Mode
- Single integrated container with both frontend and backend
- All services in Docker: `docker-compose up -d`
- Frontend served as static files by FastAPI

## GPU Support

The Ollama service is configured to use GPU acceleration. If you don't have NVIDIA GPU support:

1. Remove the `deploy` section from the ollama service in docker-compose.yaml
2. Or install NVIDIA Container Toolkit

## Environment Variables Reference

See `.env.example` for all available configuration options.

Key variables:
- `APP_PG_*`: Database configuration
- `APP_OLLAMA_BASE_URL`: Ollama API URL
- `APP_CHAT_MODEL`: LLM model name
- `APP_EMBEDDING_MODEL`: Embedding model name
- `VITE_API_BASE_URL`: Frontend API URL (leave empty for integrated setup)