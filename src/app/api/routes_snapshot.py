"""
API routes for heatmap snapshot data.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
from src.app.service.snapshot_service import build_snapshot

router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])

@router.get("")
async def get_snapshot(
    window_start: Optional[str] = Query(None, description="ISO 8601 datetime for window start (default: latest)"),
):
    """
    Get heatmap snapshot for a specific window.
    Returns HeatmapSnapshotResponse matching api.snapshot.schema.json
    """
    try:
        # Parse window_start if provided
        window_dt = None
        if window_start:
            try:
                window_dt = datetime.fromisoformat(window_start.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid window_start format. Use ISO 8601 format.")
        
        # Build snapshot
        snapshot = build_snapshot(window_dt)
        return snapshot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build snapshot: {str(e)}")
