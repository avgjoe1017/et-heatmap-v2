"""
Data access object for entities table.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from .base import BaseDAO


class EntityDAO(BaseDAO):
    """DAO for entities table."""
    
    def create_entity(self, entity_data: dict) -> str:
        """
        Create a new entity.
        Returns entity_id.
        """
        # Prepare data for insertion
        data = {
            "entity_id": entity_data["entity_id"],
            "entity_key": entity_data.get("entity_key", entity_data["entity_id"]),
            "canonical_name": entity_data["canonical_name"],
            "entity_type": entity_data["entity_type"],
            "is_pinned": entity_data.get("is_pinned", False),
            "is_active": entity_data.get("is_active", True),
            "first_seen_at": entity_data.get("first_seen_at", datetime.now(timezone.utc)),
            "external_ids": json.dumps(entity_data.get("external_ids", {})),
            "context_hints": json.dumps(entity_data.get("context_hints", [])),
            "metadata": json.dumps(entity_data.get("metadata", {})),
        }
        
        return self.execute_insert("entities", data)
    
    def get_entity(self, entity_id: str) -> Optional[dict]:
        """
        Get entity by ID.
        """
        results = self.execute_select("entities", {"entity_id": entity_id}, limit=1)
        if not results:
            return None
        
        entity = results[0]
        # Parse JSON fields
        entity["external_ids"] = json.loads(entity.get("external_ids", "{}"))
        entity["context_hints"] = json.loads(entity.get("context_hints", "[]"))
        entity["metadata"] = json.loads(entity.get("metadata", "{}"))
        return entity
    
    def get_entities_by_type(self, entity_type: str) -> List[dict]:
        """Get all entities of a specific type."""
        results = self.execute_select("entities", {"entity_type": entity_type})
        for entity in results:
            entity["external_ids"] = json.loads(entity.get("external_ids", "{}"))
            entity["context_hints"] = json.loads(entity.get("context_hints", "[]"))
            entity["metadata"] = json.loads(entity.get("metadata", "{}"))
        return results
    
    def get_pinned_entities(self) -> List[dict]:
        """Get all pinned entities."""
        results = self.execute_select("entities", {"is_pinned": True})
        for entity in results:
            entity["external_ids"] = json.loads(entity.get("external_ids", "{}"))
            entity["context_hints"] = json.loads(entity.get("context_hints", "[]"))
            entity["metadata"] = json.loads(entity.get("metadata", "{}"))
        return results
    
    def update_entity(self, entity_id: str, updates: dict) -> int:
        """
        Update entity.
        Returns number of rows updated.
        """
        # Convert JSON fields
        if "external_ids" in updates:
            updates["external_ids"] = json.dumps(updates["external_ids"])
        if "context_hints" in updates:
            updates["context_hints"] = json.dumps(updates["context_hints"])
        if "metadata" in updates:
            updates["metadata"] = json.dumps(updates["metadata"])
        
        return self.execute_update("entities", updates, {"entity_id": entity_id})
    
    def update_last_seen(self, entity_id: str, timestamp: datetime = None):
        """Update last_seen_at timestamp."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        self.execute_update("entities", {"last_seen_at": timestamp}, {"entity_id": entity_id})


# Convenience functions for backwards compatibility
def create_entity(entity_data: dict) -> str:
    """Create a new entity."""
    with EntityDAO() as dao:
        return dao.create_entity(entity_data)

def get_entity(entity_id: str) -> Optional[dict]:
    """Get entity by ID."""
    with EntityDAO() as dao:
        return dao.get_entity(entity_id)

def update_entity(entity_id: str, updates: dict) -> int:
    """Update entity."""
    with EntityDAO() as dao:
        return dao.update_entity(entity_id, updates)
