# Route Map Web App - FastAPI + static frontend
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Prevent Python from writing pyc and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Use system Python so uv does not download another interpreter
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

# Sync environment from lockfile (copy first for layer caching)
COPY pyproject.toml uv.lock .
RUN uv sync --frozen --no-install-project

# Copy application and static assets
COPY app/ ./app/
COPY static/ ./static/

# Run as non-root user
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# GEMINI_API_KEY and optional GOOGLE_MAPS_API_KEY via env at runtime
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
