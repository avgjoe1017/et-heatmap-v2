"""
Service layer for pipeline run status and metrics.
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime
from src.storage.dao.runs import RunDAO


def get_latest_run() -> Optional[dict]:
    """
    Get the latest pipeline run with metrics.
    """
    with RunDAO() as run_dao:
        run = run_dao.get_latest_run()
        if not run:
            return None
        
        # Load run metrics
        run_id = run["run_id"]
        run_metrics = _get_run_metrics(run_id)
        
        return {
            **run,
            "metrics": run_metrics
        }


def get_run(run_id: str) -> Optional[dict]:
    """
    Get a specific pipeline run by ID.
    """
    with RunDAO() as run_dao:
        run = run_dao.get_run(run_id)
        if not run:
            return None
        
        # Load run metrics
        run_metrics = _get_run_metrics(run_id)
        
        return {
            **run,
            "metrics": run_metrics
        }


def _get_run_metrics(run_id: str) -> Optional[dict]:
    """Get run_metrics for a run."""
    query = "SELECT * FROM run_metrics WHERE run_id = :run_id"
    
    with RunDAO() as run_dao:
        result = run_dao.execute_raw(query, {"run_id": run_id})
        rows = [dict(row._mapping) for row in result]
        
        if not rows:
            return None
        
        metrics = rows[0]
        
        # Parse JSON fields
        metrics["source_counts"] = json.loads(metrics.get("source_counts", "{}"))
        metrics["mention_counts"] = json.loads(metrics.get("mention_counts", "{}"))
        metrics["unresolved_top"] = json.loads(metrics.get("unresolved_top", "[]"))
        metrics["timings_ms"] = json.loads(metrics.get("timings_ms", "{}"))
        
        return metrics
