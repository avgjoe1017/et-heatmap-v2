"""
Service layer for entity drilldown data.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import pytz

from src.storage.dao.snapshots import SnapshotDAO
from src.storage.dao.runs import RunDAO
from src.storage.dao.entities import EntityDAO
from src.storage.dao.source_items import SourceItemDAO
from src.pipeline.daily_run import get_daily_window


def get_entity_drilldown(entity_id: str, window_start: Optional[datetime] = None) -> dict:
    """
    Build entity drilldown response.
    Returns dict matching api.drilldown.schema.json
    """
    # Get window
    if window_start is None:
        with RunDAO() as run_dao:
            latest_run = run_dao.get_latest_run()
            if not latest_run:
                return _empty_drilldown(entity_id)
            
            window_start_iso = latest_run.get("window_start")
            window_end_iso = latest_run.get("window_end")
            run_id = latest_run["run_id"]
    else:
        window_start_utc, window_end_utc = get_daily_window(window_start)
        window_start_iso = window_start_utc.isoformat()
        window_end_iso = window_end_utc.isoformat()
        
        with RunDAO() as run_dao:
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
                return _empty_drilldown(entity_id, window_start_iso, window_end_iso)
            run_id = rows[0]["run_id"]
    
    # Load entity
    with EntityDAO() as entity_dao:
        entity = entity_dao.get_entity(entity_id)
        if not entity:
            return _empty_drilldown(entity_id, window_start_iso, window_end_iso)
        
        # Load aliases
        aliases_query = "SELECT alias FROM entity_aliases WHERE entity_id = :entity_id"
        alias_results = entity_dao.execute_raw(aliases_query, {"entity_id": entity_id})
        aliases = [row[0] for row in alias_results]
        
        # Load relationships
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
    
    # Load metrics for this run
    with SnapshotDAO() as snapshot_dao:
        metrics_list = snapshot_dao.get_entity_metrics_for_run(run_id)
        current_metrics = next((m for m in metrics_list if m["entity_id"] == entity_id), None)
        
        if not current_metrics:
            return _empty_drilldown(entity_id, window_start_iso, window_end_iso)
        
        # Get historical series (last 90 days)
        window_end_dt = datetime.fromisoformat(window_end_iso.replace('Z', '+00:00'))
        window_start_hist = window_end_dt - timedelta(days=90)
        historical = snapshot_dao.get_entity_metrics_for_window(
            entity_id, window_start_hist, window_end_dt
        )
        
        # Calculate deltas
        delta_1d = _calculate_delta(current_metrics, historical, days=1)
        delta_7d = _calculate_delta(current_metrics, historical, days=7)
        
        # Load drivers
        drivers = snapshot_dao.get_drivers_for_entity(run_id, entity_id)
        
        # Load themes
        themes = snapshot_dao.get_themes_for_entity(run_id, entity_id)
    
    # Build drivers with source item details
    drivers_list = []
    with SourceItemDAO() as source_dao:
        for driver in drivers:
            item = source_dao.get_source_item(driver["item_id"])
            if item:
                drivers_list.append({
                    "rank": driver["rank"],
                    "source": item["source"],
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "published_at": item.get("published_at"),
                    "impact_score": float(driver["impact_score"]),
                    "reason": driver.get("driver_reason"),
                })
    
    # Build narrative
    narrative = _build_narrative(current_metrics, delta_1d, delta_7d)
    
    # Build series
    series = []
    for hist_metrics in historical:
        # Get run to get window_start
        with RunDAO() as run_dao:
            run = run_dao.get_run(hist_metrics["run_id"])
            if run:
                series.append({
                    "window_start": run["window_start"],
                    "x_fame": float(hist_metrics["fame"]),
                    "y_love": float(hist_metrics["love"]),
                    "momentum": float(hist_metrics["momentum"]),
                    "polarization": float(hist_metrics["polarization"]),
                    "confidence": float(hist_metrics["confidence"]),
                })
    
    # Build response
    return {
        "window": {
            "start": window_start_iso,
            "end": window_end_iso,
            "timezone": "America/Los_Angeles"
        },
        "entity": {
            "entity_id": entity_id,
            "entity_key": entity.get("entity_key", entity_id),
            "name": entity["canonical_name"],
            "type": entity["entity_type"],
            "is_pinned": entity.get("is_pinned", False),
            "external_ids": entity.get("external_ids", {}),
            "aliases": aliases,
            "relationships": {
                "parents": parent_ids,
                "children": child_ids
            }
        },
        "metrics": {
            "x_fame": float(current_metrics["fame"]),
            "y_love": float(current_metrics["love"]),
            "momentum": float(current_metrics["momentum"]),
            "polarization": float(current_metrics["polarization"]),
            "confidence": float(current_metrics["confidence"]),
            "attention": float(current_metrics["attention"]),
            "baseline_fame": float(current_metrics["baseline_fame"]) if current_metrics.get("baseline_fame") else None,
            "mentions_explicit": int(current_metrics["mentions_explicit"]),
            "mentions_implicit": int(current_metrics["mentions_implicit"]),
            "sources_distinct": int(current_metrics["sources_distinct"]),
            "delta_1d": delta_1d,
            "delta_7d": delta_7d,
        },
        "narrative": narrative,
        "drivers": drivers_list,
        "themes": themes,
        "series": series
    }


def _calculate_delta(current: dict, historical: List[dict], days: int) -> dict:
    """Calculate delta from N days ago."""
    if not historical:
        return {}
    
    # Find metrics from N days ago (approximate)
    # For now, just use the oldest historical entry
    if days == 1 and len(historical) >= 2:
        prev = historical[-2]  # Second to last (1 day before)
    elif days == 7 and len(historical) >= 8:
        prev = historical[-8]  # 7 days before
    else:
        return {}
    
    return {
        "x_fame": float(current["fame"]) - float(prev["fame"]),
        "y_love": float(current["love"]) - float(prev["love"]),
        "momentum": float(current["momentum"]) - float(prev["momentum"]),
    }


def _build_narrative(metrics: dict, delta_1d: dict, delta_7d: dict) -> dict:
    """Build narrative explanation of movement."""
    bullets = []
    
    if delta_1d:
        if delta_1d.get("x_fame", 0) > 5:
            bullets.append(f"Fame increased by {delta_1d['x_fame']:.1f} points in the last day")
        elif delta_1d.get("x_fame", 0) < -5:
            bullets.append(f"Fame decreased by {abs(delta_1d['x_fame']):.1f} points in the last day")
        
        if delta_1d.get("y_love", 0) > 5:
            bullets.append(f"Love increased by {delta_1d['y_love']:.1f} points in the last day")
        elif delta_1d.get("y_love", 0) < -5:
            bullets.append(f"Love decreased by {abs(delta_1d['y_love']):.1f} points in the last day")
    
    moved_because = "Metrics remain stable" if not bullets else "Recent activity detected"
    
    return {
        "moved_because": moved_because,
        "bullets": bullets
    }


def _empty_drilldown(entity_id: str, window_start: Optional[str] = None, window_end: Optional[str] = None) -> dict:
    """Return empty drilldown structure."""
    if window_start is None:
        window_start = datetime.now(timezone.utc).isoformat()
    if window_end is None:
        window_end = datetime.now(timezone.utc).isoformat()
    
    # Try to load entity info even if no metrics
    entity_info = {
        "entity_id": entity_id,
        "entity_key": entity_id,
        "name": entity_id,
        "type": "PERSON",
        "is_pinned": False,
        "external_ids": {},
        "aliases": [],
        "relationships": {"parents": [], "children": []}
    }
    
    try:
        with EntityDAO() as entity_dao:
            entity = entity_dao.get_entity(entity_id)
            if entity:
                entity_info = {
                    "entity_id": entity_id,
                    "entity_key": entity.get("entity_key", entity_id),
                    "name": entity["canonical_name"],
                    "type": entity["entity_type"],
                    "is_pinned": entity.get("is_pinned", False),
                    "external_ids": json.loads(entity.get("external_ids", "{}")) if isinstance(entity.get("external_ids"), str) else entity.get("external_ids", {}),
                    "aliases": [],
                    "relationships": {"parents": [], "children": []}
                }
    except Exception:
        pass
    
    return {
        "window": {
            "start": window_start,
            "end": window_end,
            "timezone": "America/Los_Angeles"
        },
        "entity": entity_info,
        "metrics": {
            "x_fame": 0.0,
            "y_love": 50.0,
            "momentum": 0.0,
            "polarization": 0.0,
            "confidence": 0.0,
            "attention": 0.0,
            "baseline_fame": None,
            "mentions_explicit": 0,
            "mentions_implicit": 0,
            "sources_distinct": 0,
            "delta_1d": {},
            "delta_7d": {},
        },
        "narrative": {
            "moved_because": "No data available",
            "bullets": []
        },
        "drivers": [],
        "themes": [],
        "series": []
    }
