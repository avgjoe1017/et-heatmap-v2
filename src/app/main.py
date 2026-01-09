"""
FastAPI application entrypoint for Entertainment Feelings Heatmap API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="ET Heatmap API",
    description="Entertainment Feelings Heatmap - Daily-updated scatter plot of fame vs love",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite/React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {"message": "ET Heatmap API", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
