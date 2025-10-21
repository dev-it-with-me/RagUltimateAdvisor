# Embedding Models Guide

## Overview

This application uses VoyageAI for generating text embeddings. VoyageAI provides state-of-the-art embedding models optimized for semantic search and retrieval.

## Current Configuration

- **Default Model**: `voyage-3.5`
- **Dimensions**: 1024
- **Free Tier**: 200 million tokens included
- **Cost After Free Tier**: $0.06 per million tokens

## Available Models

### Recommended Models

| Model | Dimensions | Price/Million Tokens | Free Tokens | Use Case |
|-------|------------|---------------------|-------------|----------|
| **voyage-3.5** | 1024 | $0.06 | 200M | Best balance of performance and cost |
| voyage-3.5-lite | 512 | $0.02 | 200M | Faster, lower cost, good for simple queries |
| voyage-3-large | 1536 | $0.18 | 200M | Maximum quality for complex domains |

### Specialized Models

| Model | Price/Million Tokens | Free Tokens | Use Case |
|-------|---------------------|-------------|----------|
| voyage-code-3 | $0.18 | 200M | Code and technical documentation |
| voyage-context-3 | $0.18 | 200M | Long-context documents |
| voyage-finance-2 | $0.12 | 50M | Financial documents |
| voyage-law-2 | $0.12 | 50M | Legal documents |

## Cost Estimation

### Document Processing Costs

For a typical 100-page technical PDF:
- **Pages**: ~100 pages
- **Tokens**: ~50,000 tokens (assuming ~500 tokens per page)
- **Cost with voyage-3.5**: $0.003 (after free tier)
- **One-time cost**: Embeddings are generated once and stored

### Query Processing Costs

- **Average query**: ~20 tokens
- **Cost per query**: $0.0000012 (negligible)
- **10,000 queries**: ~$0.012

### Free Tier Coverage

With 200 million free tokens, you can process:
- **4,000 PDFs** of 100 pages each, OR
- **10 million queries** of average length

## Model Selection Guide

### Choose `voyage-3.5` (Default) when:
- Building general-purpose RAG applications
- Need good balance of quality and cost
- Working with diverse document types
- Want 1024-dimensional embeddings

### Choose `voyage-3.5-lite` when:
- Cost is a primary concern
- Documents are simple and well-structured
- Faster embedding generation is needed
- Storage space is limited (512 dimensions)

### Choose `voyage-3-large` when:
- Maximum retrieval accuracy is critical
- Working with complex, technical documents
- Cost is not a primary concern
- Have ample storage for 1536-dimensional vectors

## Changing the Embedding Model

### Step 1: Update Configuration

Edit your `.env` file:

```bash
# For voyage-3.5-lite (faster, cheaper)
APP_VOYAGE_MODEL=voyage-3.5-lite
APP_EMBED_DIM=512

# For voyage-3-large (highest quality)
APP_VOYAGE_MODEL=voyage-3-large
APP_EMBED_DIM=1536
```

### Step 2: Clear Existing Embeddings

```bash
# Windows
rmdir /S /Q .chroma

# Or manually delete the .chroma folder
```

### Step 3: Re-index Documents

```bash
uv run python src/scripts/run_load_embeddings.py
```

### Step 4: Restart Application

```bash
uv run fastapi dev src/main.py --host 0.0.0.0 --port 8000
```

## Performance Comparison

| Model | Embedding Time* | Storage Size** | Retrieval Quality |
|-------|----------------|----------------|-------------------|
| voyage-3.5-lite | ~2 seconds | 2 MB | Good |
| voyage-3.5 | ~3 seconds | 4 MB | Excellent |
| voyage-3-large | ~4 seconds | 6 MB | Best |

*Per 100-page PDF on standard hardware
**Approximate storage for 1000 document chunks

## API Rate Limits

VoyageAI enforces the following rate limits:
- **Requests per minute**: 300
- **Tokens per minute**: 1,000,000
- **Concurrent requests**: 50

The application handles rate limiting automatically with retries and exponential backoff.

## Monitoring Usage

### Check Current Usage

Visit your VoyageAI dashboard: https://www.voyageai.com/dashboard

### Estimate Remaining Free Tokens

```python
# Calculate approximate tokens used
documents_processed = 50  # Number of PDFs
pages_per_document = 100
tokens_per_page = 500

total_tokens = documents_processed * pages_per_document * tokens_per_page
remaining_free = 200_000_000 - total_tokens

print(f"Estimated tokens used: {total_tokens:,}")
print(f"Estimated free tokens remaining: {remaining_free:,}")
```

## Best Practices

1. **Start with the free tier**: 200M tokens is generous for most applications
2. **Use voyage-3.5**: Best balance for most use cases
3. **Monitor usage**: Check dashboard regularly if approaching limits
4. **Batch processing**: Index multiple documents at once to optimize API calls
5. **Cache embeddings**: ChromaDB persists embeddings locally - no need to regenerate

## Troubleshooting

### "Dimension mismatch" Error

This occurs when changing models with different dimensions. Solution:
1. Delete `.chroma` directory
2. Update `APP_EMBED_DIM` in `.env`
3. Re-index all documents

### "Rate limit exceeded" Error

The application automatically retries with backoff. If persistent:
1. Reduce batch size in indexing script
2. Add delays between batches
3. Check dashboard for usage limits

### "Invalid API key" Error

1. Verify `APP_VOYAGE_API_KEY` in `.env`
2. Check key validity at https://www.voyageai.com/dashboard
3. Ensure no extra spaces or quotes in the key

## Additional Resources

- [VoyageAI Documentation](https://docs.voyageai.com/)
- [Model Comparison Guide](https://www.voyageai.com/models)
- [API Reference](https://docs.voyageai.com/reference/api-reference)