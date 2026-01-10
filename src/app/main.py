"""
FastAPI application entrypoint for Entertainment Feelings Heatmap API.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from datetime import datetime, timezone
import os
import logging
import traceback

# Setup logging
from src.common.logging import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ET Heatmap API",
    description="Entertainment Feelings Heatmap - Daily-updated scatter plot of fame vs love",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions gracefully."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "An unexpected error occurred",
            "path": str(request.url)
        }
    )

# Import routes
from src.app.api import routes_snapshot, routes_entity, routes_resolve_queue, routes_runs

# Register routes
app.include_router(routes_snapshot.router)
app.include_router(routes_entity.router)
app.include_router(routes_resolve_queue.router)
app.include_router(routes_runs.router)

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "ET Heatmap API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health():
    """
    Health check endpoint.
    Checks database connectivity and returns system status.
    """
    from src.storage.db import test_connection
    
    db_status = test_connection()
    health_status = "ok" if db_status else "degraded"
    
    return {
        "status": health_status,
        "database": "connected" if db_status else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0"
    }

@app.get("/info")
async def info():
    """
    API information endpoint.
    Returns API metadata and available endpoints.
    """
    return {
        "name": "ET Heatmap API",
        "version": "0.1.0",
        "description": "Entertainment Feelings Heatmap - Daily-updated scatter plot of fame vs love",
        "endpoints": {
            "snapshots": "/api/snapshots",
            "entities": "/api/entities/{entity_id}",
            "resolve_queue": "/api/resolve-queue",
            "runs": "/api/runs",
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json"
        },
        "features": {
            "data_sources": ["Reddit", "YouTube", "GDELT News"],
            "entity_types": ["PERSON", "SHOW", "FILM", "FRANCHISE", "BRAND", "STREAMER", "CHARACTER", "COUPLE"],
            "ml_features": ["Sentiment Analysis", "Theme Clustering", "Entity Resolution"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
