# Environment Configuration

## Overview

This document describes all environment variables used by the Ultimate Advisor application. All environment variables use the `APP_` prefix for consistency.

## Configuration File

Create a `.env` file in the project root with the following variables:

```bash
# API Keys
APP_ANTHROPIC_API_KEY=your_anthropic_api_key_here
APP_VOYAGE_API_KEY=your_voyage_api_key_here

# Model Configuration
APP_ANTHROPIC_MODEL=claude-sonnet-4-0
APP_VOYAGE_MODEL=voyage-3.5
APP_EMBED_DIM=1024

# ChromaDB Configuration
APP_CHROMA_PERSIST_DIRECTORY=storage/vectors/chroma
APP_CHROMA_COLLECTION_NAME=ultimate_advisor_docs

# SQLite Configuration
APP_HISTORY_DB_PATH=storage/database/ultimate_advisor.db

# Server Configuration (Optional)
APP_HOST=0.0.0.0
APP_PORT=8000
APP_RELOAD=true
APP_LOG_LEVEL=INFO
```

## Environment Variables Reference

### Required Variables

#### `APP_ANTHROPIC_API_KEY`
- **Type**: String
- **Required**: Yes
- **Description**: API key for Anthropic Claude
- **How to get**: Sign up at https://console.anthropic.com/
- **Example**: `sk-ant-api03-...`

#### `APP_VOYAGE_API_KEY`
- **Type**: String
- **Required**: Yes
- **Description**: API key for VoyageAI embeddings
- **How to get**: Sign up at https://www.voyageai.com/
- **Note**: Includes 200M free tokens for voyage-3.5
- **Example**: `pa-...`

### Model Configuration

#### `APP_ANTHROPIC_MODEL`
- **Type**: String
- **Default**: `claude-sonnet-4-0`
- **Description**: Anthropic Claude model to use for chat
- **Options**:
  - `claude-sonnet-4-0` - Balanced performance and cost
  - `claude-opus-4-0` - Maximum quality
  - `claude-haiku-3-5` - Fast and economical

#### `APP_VOYAGE_MODEL`
- **Type**: String
- **Default**: `voyage-3.5`
- **Description**: VoyageAI embedding model
- **Options**:
  - `voyage-3.5` - Best balance (1024 dimensions)
  - `voyage-3.5-lite` - Faster, lighter (512 dimensions)
  - `voyage-3-large` - Maximum quality (1536 dimensions)

#### `APP_EMBED_DIM`
- **Type**: Integer
- **Default**: `1024`
- **Description**: Embedding vector dimensions
- **Note**: Must match the selected VoyageAI model output

### Storage Configuration

#### `APP_CHROMA_PERSIST_DIRECTORY`
- **Type**: String (Path)
- **Default**: `storage/vectors/chroma`
- **Description**: Directory for ChromaDB vector storage
- **Note**: Created automatically if it doesn't exist

#### `APP_CHROMA_COLLECTION_NAME`
- **Type**: String
- **Default**: `ultimate_advisor_docs`
- **Description**: ChromaDB collection name for document embeddings
- **Note**: Changing this requires re-indexing documents

#### `APP_HISTORY_DB_PATH`
- **Type**: String (Path)
- **Default**: `storage/database/ultimate_advisor.db`
- **Description**: SQLite database file path for query history
- **Note**: Created automatically on first use

### Server Configuration (Optional)

#### `APP_HOST`
- **Type**: String
- **Default**: `0.0.0.0`
- **Description**: Host to bind the server to
- **Options**:
  - `0.0.0.0` - Listen on all interfaces
  - `127.0.0.1` - Local only

#### `APP_PORT`
- **Type**: Integer
- **Default**: `8000`
- **Description**: Port number for the API server

#### `APP_RELOAD`
- **Type**: Boolean
- **Default**: `true` (development), `false` (production)
- **Description**: Enable auto-reload on code changes

#### `APP_LOG_LEVEL`
- **Type**: String
- **Default**: `INFO`
- **Description**: Logging verbosity level
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## Environment-Specific Configuration

### Development

```bash
# .env.development
APP_RELOAD=true
APP_LOG_LEVEL=DEBUG
APP_HOST=127.0.0.1
```

### Production

```bash
# .env.production
APP_RELOAD=false
APP_LOG_LEVEL=INFO
APP_HOST=0.0.0.0
```

### Testing

```bash
# .env.test
APP_CHROMA_PERSIST_DIRECTORY=storage/vectors/chroma_test
APP_HISTORY_DB_PATH=storage/database/test_advisor.db
APP_LOG_LEVEL=WARNING
```

## Loading Environment Variables

The application automatically loads environment variables from `.env` files using Pydantic's BaseSettings:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    voyage_api_key: str
    # ... other settings

    class Config:
        env_prefix = "APP_"
        env_file = ".env"
```

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use `.env.example`** as a template with dummy values
3. **Rotate API keys** regularly
4. **Use different keys** for development and production
5. **Store production secrets** in secure vaults (e.g., Azure Key Vault, AWS Secrets Manager)

## Troubleshooting

### API Key Errors

If you see errors like "Invalid API key", check:
1. API keys are correctly set in `.env`
2. No extra spaces or quotes in the values
3. The `.env` file is in the project root
4. Environment variables are loaded (check with `echo %APP_ANTHROPIC_API_KEY%`)

### Dimension Mismatch Errors

If you change `APP_VOYAGE_MODEL` to a model with different dimensions:
1. Update `APP_EMBED_DIM` to match
2. Delete `.chroma` directory
3. Re-run indexing: `uv run python src/scripts/run_load_embeddings.py`

### Database Lock Errors

If SQLite database is locked:
1. Ensure only one instance is running
2. Close any database browser tools
3. Check file permissions on `APP_HISTORY_DB_PATH`

## Migration Guide

### Changing Embedding Models

1. Stop the application
2. Update `.env`:
   ```bash
   APP_VOYAGE_MODEL=voyage-3-large
   APP_EMBED_DIM=1536
   ```
3. Delete the ChromaDB directory:
   ```bash
   rm -rf storage/vectors/chroma
   ```
4. Re-index documents:
   ```bash
   uv run python src/scripts/run_load_embeddings.py
   ```
5. Restart the application

### Changing Collection Name

1. Update `.env`:
   ```bash
   APP_CHROMA_COLLECTION_NAME=new_collection_name
   ```
2. Re-index documents (creates new collection)
3. Optionally delete old collection data