"""
Service layer for building heatmap snapshots.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import pytz

from src.storage.dao.snapshots import SnapshotDAO
from src.storage.dao.runs import RunDAO
from src.storage.dao.entities import EntityDAO
from src.pipeline.daily_run import get_daily_window


def build_snapshot(window_start: Optional[datetime] = None) -> dict:
    """
    Build heatmap snapshot from entity_daily_metrics for a window.
    Returns dict matching api.snapshot.schema.json
    """
    # Get window
    if window_start is None:
        # Get latest run
        with RunDAO() as run_dao:
            latest_run = run_dao.get_latest_run()
            if not latest_run:
                return _empty_snapshot()
            
            window_start_iso = latest_run.get("window_start")
            window_end_iso = latest_run.get("window_end")
            run_id = latest_run["run_id"]
    else:
        # Find run for this window
        window_start_utc, window_end_utc = get_daily_window(window_start)
        window_start_iso = window_start_utc.isoformat()
        window_end_iso = window_end_utc.isoformat()
        
        with RunDAO() as run_dao:
            # Try to find run for this window
            query = """
                SELECT run_id FROM runs 
                WHERE window_start = :window_start 
                AND window_end = :window_end
                LIMIT 1
            """
            result = run_dao.execute_raw(query, {
                "window_start": window_start_iso,
                "window_end": window_end_iso
            })
            rows = [dict(row._mapping) for row in result]
            if not rows:
                return _empty_snapshot(window_start_iso, window_end_iso)
            run_id = rows[0]["run_id"]
    
    # Load entity metrics for this run
    with SnapshotDAO() as snapshot_dao:
        metrics_list = snapshot_dao.get_entity_metrics_for_run(run_id)
    
    if not metrics_list:
        return _empty_snapshot(window_start_iso, window_end_iso)
    
    # Load entities for metadata
    entity_ids = [m["entity_id"] for m in metrics_list]
    with EntityDAO() as entity_dao:
        entities_map = {}
        for entity_id in entity_ids:
            entity = entity_dao.get_entity(entity_id)
            if entity:
                entities_map[entity_id] = entity
    
    # Build points
    points = []
    for metrics in metrics_list:
        entity_id = metrics["entity_id"]
        entity = entities_map.get(entity_id)
        
        if not entity:
            continue  # Skip if entity not found
        
        # Load aliases + relationships
        with EntityDAO() as entity_dao:
            aliases_query = "SELECT alias FROM entity_aliases WHERE entity_id = :entity_id"
            alias_results = entity_dao.execute_raw(aliases_query, {"entity_id": entity_id})
            aliases = [row[0] for row in alias_results]

            parents_query = """
                SELECT parent_entity_id FROM entity_relationships
                WHERE child_entity_id = :entity_id AND rel_type = 'PARENT_CHILD'
            """
            parent_results = entity_dao.execute_raw(parents_query, {"entity_id": entity_id})
            parent_ids = [row[0] for row in parent_results]

            children_query = """
                SELECT child_entity_id FROM entity_relationships
                WHERE parent_entity_id = :entity_id AND rel_type = 'PARENT_CHILD'
            """
            child_results = entity_dao.execute_raw(children_query, {"entity_id": entity_id})
            child_ids = [row[0] for row in child_results]

        metadata = entity.get("metadata", {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                metadata = {}
        tags = metadata.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        
        # Build entity point
        point = {
            "entity_id": entity_id,
            "entity_key": entity.get("entity_key", entity_id),
            "name": entity["canonical_name"],
            "type": entity["entity_type"],
            "x_fame": float(metrics["fame"]),
            "y_love": float(metrics["love"]),
            "momentum": float(metrics["momentum"]),
            "polarization": float(metrics["polarization"]),
            "confidence": float(metrics["confidence"]),
            "attention": float(metrics["attention"]),
            "baseline_fame": float(metrics["baseline_fame"]) if metrics.get("baseline_fame") else None,
            "mentions_explicit": int(metrics["mentions_explicit"]),
            "mentions_implicit": int(metrics["mentions_implicit"]),
            "sources_distinct": int(metrics["sources_distinct"]),
            "is_pinned": entity.get("is_pinned", False),
            "is_dormant": metrics.get("is_dormant", False),
            "tags": tags,
            "parent_ids": parent_ids,
            "child_ids": child_ids,
        }
        points.append(point)
    
    # Build response
    pacific = pytz.timezone("America/Los_Angeles")
    window_start_dt = datetime.fromisoformat(window_start_iso.replace('Z', '+00:00'))
    window_end_dt = datetime.fromisoformat(window_end_iso.replace('Z', '+00:00'))
    
    return {
        "window": {
            "start": window_start_iso,
            "end": window_end_iso,
            "timezone": "America/Los_Angeles"
        },
        "defaults": {
            "color_mode": "MOMENTUM",
            "trail_days": 7
        },
        "points": points
    }


def _empty_snapshot(window_start: Optional[str] = None, window_end: Optional[str] = None) -> dict:
    """Return empty snapshot structure."""
    if window_start is None:
        window_start = datetime.now(timezone.utc).isoformat()
    if window_end is None:
        window_end = datetime.now(timezone.utc).isoformat()
    
    return {
        "window": {
            "start": window_start,
            "end": window_end,
            "timezone": "America/Los_Angeles"
        },
        "defaults": {
            "color_mode": "MOMENTUM",
            "trail_days": 7
        },
        "points": []
    }
