"""FastAPI application: CORS, static files, API routes."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.routes import route_api

app = FastAPI(
    title="Route Map Web App",
    description="Natural-language driving route to map \
        with time and distance.",
    version="1.0.0",
)

# Allow frontend (same origin or separate dev server) to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(route_api.router, prefix="/api", tags=["route"])

# Serve static files (index.html, app.js) from project root / static
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(static_dir), html=True),
        name="static"
    )
