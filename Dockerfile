# Multi-stage Dockerfile for Ultimate Advisor with integrated frontend

# Frontend build stage
FROM node:20-slim as frontend-builder

# Install pnpm
RUN npm install -g pnpm

# Set working directory
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install frontend dependencies
RUN pnpm install --frozen-lockfile

# Copy frontend source code
COPY frontend/ ./

# Build the frontend
RUN pnpm run build

# Backend stage
FROM python:3.12-slim as backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy uv files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv sync --frozen

# Copy source code
COPY src/ ./src/

# Copy frontend build from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Command to run the application
CMD ["uv", "run", "fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]