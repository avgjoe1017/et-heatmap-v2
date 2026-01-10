"""
Service layer for pipeline run status and metrics.
"""

from typing import Optional, List, Dict, Any
from src.storage.dao.runs import RunDAO
from src.storage.dao.snapshots import SnapshotDAO
import json


def get_latest_run() -> Optional[dict]:
    """
    Get the latest pipeline run with metrics.
    """
    with RunDAO() as run_dao:
        run = run_dao.get_latest_run()
        if not run:
            return None
        
        # Add run metrics
        run["metrics"] = _get_run_metrics(run["run_id"])
        return run


def get_run(run_id: str) -> Optional[dict]:
    """
    Get a specific pipeline run by ID with metrics.
    """
    with RunDAO() as run_dao:
        run = run_dao.get_run(run_id)
        if not run:
            return None
        
        # Add run metrics
        run["metrics"] = _get_run_metrics(run_id)
        return run


def list_runs(limit: int = 100, status: Optional[str] = None) -> List[dict]:
    """
    List pipeline runs, optionally filtered by status.
    Returns most recent runs first.
    """
    with RunDAO() as run_dao:
        runs = run_dao.list_runs(limit=limit, status=status)
        return runs


def _get_run_metrics(run_id: str) -> Optional[dict]:
    """
    Get run metrics for a specific run.
    """
    with SnapshotDAO() as snapshot_dao:
        query = """
            SELECT * FROM run_metrics 
            WHERE run_id = :run_id
            LIMIT 1
        """
        result = snapshot_dao.execute_raw(query, {"run_id": run_id})
        rows = [dict(row._mapping) for row in result]
        
        if not rows:
            return None
        
        metrics = rows[0]
        
        # Parse JSONB fields
        if isinstance(metrics.get("source_counts"), str):
            metrics["source_counts"] = json.loads(metrics["source_counts"])
        if isinstance(metrics.get("mention_counts"), str):
            metrics["mention_counts"] = json.loads(metrics["mention_counts"])
        if isinstance(metrics.get("unresolved_top"), str):
            metrics["unresolved_top"] = json.loads(metrics["unresolved_top"])
        if isinstance(metrics.get("timings_ms"), str):
            metrics["timings_ms"] = json.loads(metrics["timings_ms"])
        
        return metrics
