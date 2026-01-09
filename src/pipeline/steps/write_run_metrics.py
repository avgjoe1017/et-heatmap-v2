"""
Write run instrumentation metrics.
"""

from typing import Dict, Any
import json
import logging

from src.storage.dao.runs import RunDAO

logger = logging.getLogger(__name__)


def write_run_metrics(run_id: str, metrics: dict, source_items: list = None, mentions: list = None, unresolved: list = None) -> None:
    """
    Write run_metrics for instrumentation and monitoring.
    """
    source_items = source_items or []
    mentions = mentions or []
    unresolved = unresolved or []
    
    # Build source counts
    source_counts = {}
    for item in source_items:
        source = item.get("source", "UNKNOWN")
        source_counts[source] = source_counts.get(source, 0) + 1
    
    # Build mention counts
    mention_counts = {
        "total": len(mentions) + len(unresolved),
        "resolved": len(mentions),
        "unresolved": len(unresolved),
        "implicit": sum(1 for m in mentions if m.get("is_implicit", False)),
    }
    
    # Get top unresolved strings
    unresolved_strings = {}
    for u in unresolved[:20]:  # Top 20
        surface = u.get("surface", "") or u.get("surface_norm", "")
        if surface:
            unresolved_strings[surface] = unresolved_strings.get(surface, 0) + 1
    
    unresolved_top = sorted(unresolved_strings.items(), key=lambda x: x[1], reverse=True)[:20]
    
    # Build metrics dict - run_metrics table has specific columns
    from datetime import datetime, timezone
    from src.storage.dao.base import BaseDAO
    
    class RunMetricsDAO(BaseDAO):
        """DAO for run_metrics table."""
        pass
    
    unresolved_top_list = [{"surface": s, "count": c} for s, c in unresolved_top]
    timings_dict = metrics.get("timings_ms", {})
    
    with RunMetricsDAO() as dao:
        # Insert or update run_metrics (table has columns: source_counts, mention_counts, unresolved_top, timings_ms)
        metrics_data = {
            "run_id": run_id,
            "source_counts": json.dumps(source_counts),
            "mention_counts": json.dumps(mention_counts),
            "unresolved_top": json.dumps(unresolved_top_list),
            "timings_ms": json.dumps(timings_dict),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        try:
            dao.execute_insert("run_metrics", metrics_data)
        except Exception as e:
            # If exists, update
            error_msg = str(e)
            if "UNIQUE constraint" in error_msg or "already exists" in error_msg.lower():
                updates = {k: v for k, v in metrics_data.items() if k != "run_id"}
                dao.execute_update("run_metrics", updates, {"run_id": run_id})
            else:
                logger.warning(f"Failed to store run metrics: {e}")
    
    logger.info(f"Wrote run metrics for run {run_id}")
