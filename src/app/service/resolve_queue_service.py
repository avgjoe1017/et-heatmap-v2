"""
Service layer for resolve queue management.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import pytz
import json

from src.storage.dao.unresolved import UnresolvedDAO
from src.storage.dao.runs import RunDAO
from src.storage.dao.entities import EntityDAO
from src.storage.dao.source_items import SourceItemDAO
from src.storage.dao.documents import DocumentDAO
from src.pipeline.daily_run import get_daily_window


def get_resolve_queue(window_start: Optional[datetime] = None, limit: int = 100) -> dict:
    """
    Build resolve queue response.
    Returns dict matching api.resolve_queue.schema.json
    """
    # Get window
    if window_start is None:
        with RunDAO() as run_dao:
            latest_run = run_dao.get_latest_run()
            if not latest_run:
                return _empty_resolve_queue()
            
            window_start_iso = latest_run.get("window_start")
            window_end_iso = latest_run.get("window_end")
    else:
        window_start_utc, window_end_utc = get_daily_window(window_start)
        window_start_iso = window_start_utc.isoformat()
        window_end_iso = window_end_utc.isoformat()
    
    # Load aggregated unresolved mentions
    with UnresolvedDAO() as unresolved_dao:
        aggregated = unresolved_dao.get_unresolved_aggregated(
            datetime.fromisoformat(window_start_iso.replace('Z', '+00:00')),
            datetime.fromisoformat(window_end_iso.replace('Z', '+00:00')),
            limit=limit
        )
    
    # Build examples with source item details
    items = []
    with DocumentDAO() as doc_dao:
        with SourceItemDAO() as source_dao:
            for agg in aggregated:
                # Get example unresolved mention for this surface
                query = """
                    SELECT * FROM unresolved_mentions 
                    WHERE surface_norm = :surface_norm 
                    LIMIT 1
                """
                result = unresolved_dao.execute_raw(query, {"surface_norm": agg["surface_norm"]})
                rows = [dict(row._mapping) for row in result]
                
                if not rows:
                    continue
                
                example = rows[0]
                example["candidates"] = json.loads(example.get("candidates", "[]"))
                
                # Get document and source item for context
                doc = doc_dao.get_document(example["doc_id"])
                if doc:
                    item = source_dao.get_source_item(doc["item_id"])
                    if item:
                        items.append({
                            "surface": agg["surface"],
                            "count": agg["count"],
                            "impact": float(agg.get("top_score", 0) or 0) * agg["count"],  # Approximate impact
                            "examples": [{
                                "source": item["source"],
                                "context": example.get("context", "")[:280],
                                "candidates": example["candidates"]
                            }]
                        })
    
    # Sort by impact desc
    items.sort(key=lambda x: x["impact"], reverse=True)
    
    # Build response
    return {
        "window": {
            "start": window_start_iso,
            "end": window_end_iso,
            "timezone": "America/Los_Angeles"
        },
        "items": items
    }


def resolve_mention(unresolved_id: str, entity_id: str, alias: Optional[str] = None) -> bool:
    """
    Resolve an unresolved mention to an entity.
    Creates alias if needed and marks as resolved.
    """
    import json
    
    # Load unresolved mention
    with UnresolvedDAO() as unresolved_dao:
        query = "SELECT * FROM unresolved_mentions WHERE unresolved_id = :unresolved_id"
        result = unresolved_dao.execute_raw(query, {"unresolved_id": unresolved_id})
        rows = [dict(row._mapping) for row in result]
        
        if not rows:
            return False
        
        unresolved = rows[0]
        surface = unresolved["surface"]
    
    # Verify entity exists
    with EntityDAO() as entity_dao:
        entity = entity_dao.get_entity(entity_id)
        if not entity:
            return False
        
        # Create alias if provided or use surface as alias
        alias_to_add = alias if alias else surface
        
        # Check if alias already exists
        alias_query = """
            SELECT * FROM entity_aliases 
            WHERE entity_id = :entity_id AND alias_norm = :alias_norm
        """
        alias_result = entity_dao.execute_raw(alias_query, {
            "entity_id": entity_id,
            "alias_norm": alias_to_add.lower()
        })
        existing = [dict(row._mapping) for row in alias_result]
        
        if not existing:
            # Create new alias
            alias_data = {
                "entity_id": entity_id,
                "alias": alias_to_add,
                "alias_norm": alias_to_add.lower(),
                "is_primary": False,
                "confidence": 0.8  # Default confidence for manually resolved
            }
            entity_dao.execute_insert("entity_aliases", alias_data)
    
    # Delete or mark unresolved mention as resolved
    # For now, we'll delete it since it's been resolved
    with UnresolvedDAO() as unresolved_dao:
        unresolved_dao.execute_delete("unresolved_mentions", {"unresolved_id": unresolved_id})
    
    return True


def _empty_resolve_queue(window_start: Optional[str] = None, window_end: Optional[str] = None) -> dict:
    """Return empty resolve queue structure."""
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
        "items": []
    }


