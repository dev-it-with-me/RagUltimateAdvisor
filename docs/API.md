# API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, implement appropriate authentication mechanisms.

## Endpoints

### RAG Endpoints

#### Query Documents

Submit a query to the RAG system and receive an AI-generated response with source documents.

```http
POST /api/rag/query
```

**Request Body:**

```json
{
  "query": "string",
  "top_k": 5  // Optional, default: 5
}
```

**Response:**

```json
{
  "query": "string",
  "response": "string",
  "source_documents": [
    {
      "content": "string",
      "metadata": {
        "file_name": "string",
        "page_label": "string"
      },
      "score": 0.85
    }
  ],
  "timestamp": "2025-10-21T10:00:00Z"
}
```

#### Health Check

Check the health status of the RAG system components.

```http
GET /api/rag/health
```

**Response:**

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

#### Document Count

Get the total number of documents in the vector store.

```http
GET /api/rag/documents/count
```

**Response:**

```json
{
  "count": 150,
  "collection_name": "ultimate_advisor_docs"
}
```

### History Endpoints

#### Get Query History

Retrieve paginated query history.

```http
GET /api/history?limit=10&offset=0
```

**Query Parameters:**
- `limit` (optional): Number of records to return (default: 10, max: 100)
- `offset` (optional): Number of records to skip (default: 0)

**Response:**

```json
{
  "queries": [
    {
      "id": "uuid",
      "query": "string",
      "response": "string",
      "response_time": 1.23,
      "success": true,
      "timestamp": "2025-10-21T10:00:00Z"
    }
  ],
  "total": 100,
  "limit": 10,
  "offset": 0
}
```

#### Get Query Details

Get detailed information about a specific query.

```http
GET /api/history/{query_id}
```

**Path Parameters:**
- `query_id`: UUID of the query

**Response:**

```json
{
  "id": "uuid",
  "query": "string",
  "response": "string",
  "response_time": 1.23,
  "success": true,
  "timestamp": "2025-10-21T10:00:00Z",
  "metadata": {
    "model": "claude-sonnet-4-0",
    "top_k": 5,
    "similarity_cutoff": 0.6
  }
}
```

#### Get Source Documents

Retrieve source documents used for a specific query.

```http
GET /api/history/{query_id}/sources
```

**Path Parameters:**
- `query_id`: UUID of the query

**Response:**

```json
{
  "query_id": "uuid",
  "sources": [
    {
      "content": "string",
      "metadata": {
        "file_name": "string",
        "page_label": "string"
      },
      "score": 0.85,
      "order": 1
    }
  ]
}
```

#### Get Statistics

Get overall query statistics.

```http
GET /api/history/statistics
```

**Response:**

```json
{
  "total_queries": 1000,
  "successful_queries": 950,
  "failed_queries": 50,
  "success_rate": 0.95,
  "average_response_time": 1.5,
  "queries_today": 25,
  "queries_this_week": 150,
  "queries_this_month": 500
}
```

### Utility Endpoints

#### API Information

Get basic API information.

```http
GET /
```

**Response:**

```json
{
  "name": "Ultimate Advisor RAG API",
  "version": "1.0.0",
  "description": "AI-powered Q&A system for Ultimate Frisbee rules"
}
```

#### General Health Check

Check if the API is running.

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-10-21T10:00:00Z"
}
```

#### Download Files

Download files from the data directory.

```http
GET /files/download/{filename}
```

**Path Parameters:**
- `filename`: Name of the file to download

**Response:**
- Binary file data with appropriate content-type header

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}  // Optional additional error details
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `NOT_FOUND` | 404 | Resource not found |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting based on:
- IP address
- API key (when authentication is added)
- Endpoint-specific limits

## WebSocket Support

The API supports WebSocket connections for real-time updates (planned feature):

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:3000` (development)
- `http://localhost:5173` (Vite dev server)

Update CORS settings in production to match your deployment domains.

## OpenAPI Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Response Headers

All API responses include standard headers:
- `Content-Type`: Usually `application/json`
- `X-Request-ID`: Unique request identifier for tracing
- `X-Response-Time`: Time taken to process the request (ms)