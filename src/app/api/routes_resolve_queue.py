"""
API routes for resolve queue management.
"""

from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from src.app.service.resolve_queue_service import get_resolve_queue, resolve_mention as resolve_mention_service

router = APIRouter(prefix="/api/resolve-queue", tags=["resolve-queue"])


class ResolveRequest(BaseModel):
    unresolved_id: str
    entity_id: str
    alias: Optional[str] = None


@router.get("")
async def get_resolve_queue_route(
    window_start: Optional[str] = Query(None, description="ISO 8601 datetime for window start (default: latest)"),
    limit: int = Query(100, description="Maximum number of items to return"),
):
    """
    Get unresolved mentions resolve queue.
    Returns ResolveQueueResponse matching api.resolve_queue.schema.json
    """
    try:
        # Parse window_start if provided
        window_dt = None
        if window_start:
            try:
                window_dt = datetime.fromisoformat(window_start.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid window_start format. Use ISO 8601 format.")
        
        # Get resolve queue
        queue = get_resolve_queue(window_dt, limit)
        return queue
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resolve queue: {str(e)}")


@router.post("/resolve")
async def resolve_mention_route(
    request: ResolveRequest = Body(...)
):
    """
    Resolve an unresolved mention to an existing entity.
    Creates alias if needed and backfills future runs.
    """
    try:
        success = resolve_mention_service(
            request.unresolved_id,
            request.entity_id,
            request.alias
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Unresolved mention or entity not found")
        
        return {
            "success": True,
            "message": f"Resolved to entity {request.entity_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve mention: {str(e)}")
