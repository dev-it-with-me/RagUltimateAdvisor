import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.history.routes import history_router
from src.rag.routes import rag_router
from src.schemas import APIInfoResponse, HealthCheckResponse


# Configure logging with file output
def setup_logging():
    """Configure logging to save to timestamped files."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs/server_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create timestamped log file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{timestamp}.log"

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # File handler for saving to file
            logging.FileHandler(log_file, encoding="utf-8"),
            # Console handler for terminal output
            logging.StreamHandler(),
        ],
    )

    # Log the startup information
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger


# Setup logging and get logger
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    logger.info("🚀 Ultimate Advisor API server started successfully")
    logger.info("📚 RAG-based chat system for Ultimate Frisbee rules and guidance")
    yield
    # Clean up the ML models and release the resources
    logger.info("🛑 Ultimate Advisor API server shutting down")


app = FastAPI(
    title="Ultimate Advisor API",
    description="A RAG-based chat system for Ultimate Frisbee rules and guidance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses."""
    start_time = datetime.now()

    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = (datetime.now() - start_time).total_seconds()

    # Log response
    logger.info(
        f"Response: {response.status_code} for {request.method} {request.url.path} "
        f"- {process_time:.3f}s"
    )

    return response


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
