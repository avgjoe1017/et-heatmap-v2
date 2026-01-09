"""
Data access object for source_items table.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from .base import BaseDAO


class SourceItemDAO(BaseDAO):
    """DAO for source_items table."""
    
    def create_source_item(self, item_data: dict) -> str:
        """
        Create a new source_item.
        Returns item_id.
        """
        data = {
            "item_id": item_data["item_id"],
            "source": item_data["source"],
            "url": item_data.get("url"),
            "published_at": item_data.get("published_at"),
            "fetched_at": item_data.get("fetched_at", datetime.now(timezone.utc)),
            "title": item_data.get("title"),
            "description": item_data.get("description"),
            "author": item_data.get("author"),
            "engagement": json.dumps(item_data.get("engagement", {})),
            "raw_payload": json.dumps(item_data.get("raw_payload", {})),
        }
        
        # Handle datetime serialization
        for key in ["published_at", "fetched_at"]:
            if data.get(key) and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        
        self.execute_insert("source_items", data)
        return data["item_id"]
    
    def get_source_item(self, item_id: str) -> Optional[dict]:
        """Get source_item by ID."""
        results = self.execute_select("source_items", {"item_id": item_id}, limit=1)
        if not results:
            return None
        
        item = results[0]
        # Parse JSON fields
        item["engagement"] = json.loads(item.get("engagement", "{}"))
        item["raw_payload"] = json.loads(item.get("raw_payload", "{}"))
        return item
    
    def get_source_items_by_window(self, window_start: datetime, window_end: datetime) -> List[dict]:
        """
        Get source_items in window.
        """
        # Handle datetime serialization
        if isinstance(window_start, datetime):
            window_start = window_start.isoformat()
        if isinstance(window_end, datetime):
            window_end = window_end.isoformat()
        
        query = """
            SELECT * FROM source_items 
            WHERE published_at >= :window_start 
            AND published_at < :window_end
            ORDER BY published_at DESC
        """
        params = {"window_start": window_start, "window_end": window_end}
        result = self.execute_raw(query, params)
        
        items = []
        for row in result:
            item = dict(row._mapping)
            item["engagement"] = json.loads(item.get("engagement", "{}"))
            item["raw_payload"] = json.loads(item.get("raw_payload", "{}"))
            items.append(item)
        
        return items
    
    def get_source_items_by_source(self, source: str, limit: int = 100) -> List[dict]:
        """Get source_items by source type."""
        results = self.execute_select("source_items", {"source": source}, limit=limit)
        for item in results:
            item["engagement"] = json.loads(item.get("engagement", "{}"))
            item["raw_payload"] = json.loads(item.get("raw_payload", "{}"))
        return results


# Convenience functions
def create_source_item(item_data: dict) -> str:
    """Create a new source_item."""
    with SourceItemDAO() as dao:
        return dao.create_source_item(item_data)

def get_source_items_by_window(window_start: datetime, window_end: datetime) -> List[dict]:
    """Get source_items in window."""
    with SourceItemDAO() as dao:
        return dao.get_source_items_by_window(window_start, window_end)
