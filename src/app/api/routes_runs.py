"""
API routes for pipeline run status and metrics.
"""

from fastapi import APIRouter, Path, HTTPException
from typing import Optional
from src.app.service.run_service import get_latest_run as get_latest_run_service, get_run as get_run_service

router = APIRouter(prefix="/api/runs", tags=["runs"])

@router.get("/latest")
async def get_latest_run():
    """
    Get status and metrics for the latest pipeline run.
    """
    try:
        run = get_latest_run_service()
        if not run:
            raise HTTPException(status_code=404, detail="No runs found")
        return run
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get latest run: {str(e)}")

@router.get("/{run_id}")
async def get_run(run_id: str = Path(..., description="Run ID")):
    """
    Get status and metrics for a specific pipeline run.
    """
    try:
        run = get_run_service(run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        return run
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get run: {str(e)}")
