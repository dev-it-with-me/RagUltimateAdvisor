import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.history.routes import history_router
from src.rag.routes import rag_router
from src.schemas import APIInfoResponse, HealthCheckResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ultimate Advisor API",
    description="A RAG-based chat system for Ultimate Frisbee rules and guidance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include routers
app.include_router(history_router)
app.include_router(rag_router)

# Static files serving (if files directory exists)
static_path = Path("files")
if static_path.exists() and static_path.is_dir():
    app.mount("/files", StaticFiles(directory="files"), name="files")
    logger.info("Static files mounted at /files")


@app.exception_handler(500)
async def internal_server_error_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle internal server errors with custom response."""
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "detail": str(exc) if app.debug else None,
        },
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle 404 errors with custom response."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found.",
            "path": str(request.url.path),
        },
    )


@app.get("/", response_model=APIInfoResponse)
async def root() -> APIInfoResponse:
    """Root endpoint providing API information."""
    return APIInfoResponse(
        message="Welcome to Ultimate Advisor API",
        description="A RAG-based chat system for Ultimate Frisbee rules and guidance",
        version="1.0.0",
        endpoints={
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "rag": "/rag",
            "history": "/history",
        },
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint for monitoring."""
    return HealthCheckResponse(
        status="healthy", service="Ultimate Advisor API", version="1.0.0"
    )
