"""
API routes for entity drilldown data.
"""

from fastapi import APIRouter, Path, Query, HTTPException
from typing import Optional
from datetime import datetime
from src.app.service.entity_service import get_entity_drilldown

router = APIRouter(prefix="/api/entities", tags=["entities"])

@router.get("/{entity_id}")
async def get_entity_drilldown(
    entity_id: str = Path(..., description="Entity ID"),
    window_start: Optional[str] = Query(None, description="ISO 8601 datetime for window start (default: latest)"),
):
    """
    Get detailed drilldown for a specific entity.
    Returns EntityDrilldownResponse matching api.drilldown.schema.json
    """
    try:
        # Parse window_start if provided
        window_dt = None
        if window_start:
            try:
                window_dt = datetime.fromisoformat(window_start.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid window_start format. Use ISO 8601 format.")
        
        # Get drilldown
        drilldown = get_entity_drilldown(entity_id, window_dt)
        
        # Check if entity exists
        if not drilldown.get("entity", {}).get("entity_id"):
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
        
        return drilldown
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity drilldown: {str(e)}")
