import logging
import re
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.history.routes import history_router
from src.rag.routes import rag_router
from src.schemas import APIInfoResponse, HealthCheckResponse


def setup_logging():
    """Configure logging to save to timestamped files."""
    log_dir = Path("logs/server_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger


logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Ultimate Advisor API server started successfully")
    logger.info("📚 RAG-based chat system for Ultimate Frisbee rules and guidance")
    yield
    logger.info("🛑 Ultimate Advisor API server shutting down")


app = FastAPI(
    title="Ultimate Advisor API",
    description="A RAG-based chat system for Ultimate Frisbee rules and guidance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses."""
    start_time = datetime.now()

    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    response = await call_next(request)

    process_time = (datetime.now() - start_time).total_seconds()

    logger.info(
        f"Response: {response.status_code} for {request.method} {request.url.path} "
        f"- {process_time:.3f}s"
    )

    return response


app.include_router(history_router)
app.include_router(rag_router)


@app.get("/files/download/{filename}")
async def download_file(filename: str):
    """Download a file from the data directory.

    Args:
        filename: Name of the file to download

    Returns:
        FileResponse: The requested file

    Raises:
        HTTPException: If file not found or access denied
    """

    if not re.match(r"^[a-zA-Z0-9._-]+$", filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = Path("data") / filename

    try:
        file_path = file_path.resolve()
        data_dir = Path("data").resolve()
        file_path.relative_to(data_dir)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied") from None

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    logger.info(f"Serving file download: {filename}")
    return FileResponse(
        path=file_path, filename=filename, media_type="application/octet-stream"
    )


static_path = Path("files")
if static_path.exists() and static_path.is_dir():
    app.mount("/files", StaticFiles(directory="files"), name="files")
    logger.info("Static files mounted at /files")


frontend_dist_path = Path("frontend/dist")
if frontend_dist_path.exists() and frontend_dist_path.is_dir():
    app.mount(
        "/assets", StaticFiles(directory=frontend_dist_path / "assets"), name="assets"
    )
    logger.info("Frontend assets mounted at /assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA for all non-API routes."""
        if (
            full_path.startswith("api/")
            or full_path.startswith("docs")
            or full_path.startswith("redoc")
            or full_path.startswith("files/")
        ):
            raise HTTPException(status_code=404, detail="Not found")

        file_path = frontend_dist_path / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        index_file = frontend_dist_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

        raise HTTPException(status_code=404, detail="Frontend not found")

    logger.info("SPA routing configured for frontend")
else:
    logger.warning("Frontend dist directory not found - frontend will not be served")


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
