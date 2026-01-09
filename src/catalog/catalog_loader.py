"""
Load and merge entity catalog (pinned + discovered + resolved).
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone

from src.storage.dao.entities import EntityDAO
from src.storage.dao.base import BaseDAO


def load_catalog() -> List[dict]:
    """
    Load entity catalog from:
    - config/pinned_entities.json (pinned entities)
    - entities table (discovered entities)
    - entity_aliases table (aliases)
    
    Returns list of entity dicts ready for resolution.
    """
    catalog = []
    
    # Load pinned entities from config
    config_file = Path(__file__).parent.parent.parent / "config" / "pinned_entities.json"
    if config_file.exists():
        with open(config_file, "r") as f:
            pinned_data = json.load(f)
        
        for entity_data in pinned_data:
            # Normalize structure
            catalog.append({
                "entity_id": entity_data["entity_id"],
                "entity_key": entity_data.get("entity_key", entity_data["entity_id"]),
                "canonical_name": entity_data["canonical_name"],
                "entity_type": entity_data["type"],
                "aliases": entity_data.get("aliases", []),
                "context_hints": entity_data.get("context_hints", []),
                "external_ids": entity_data.get("external_ids", {}),
                "metadata": {},
                "is_pinned": True,
                "prior_weight": 1.0,  # Pinned entities get max weight
            })
    
    # Load entities from database
    with EntityDAO() as dao:
        db_entities = dao.execute_select("entities", {"is_active": True})
        
        for entity in db_entities:
            # Parse JSON fields
            external_ids = json.loads(entity.get("external_ids", "{}"))
            context_hints = json.loads(entity.get("context_hints", "[]"))
            metadata = json.loads(entity.get("metadata", "{}"))
            
            # Load aliases
            aliases_query = "SELECT alias FROM entity_aliases WHERE entity_id = :entity_id"
            alias_results = dao.execute_raw(aliases_query, {"entity_id": entity["entity_id"]})
            aliases = [row[0] for row in alias_results]
            
            # Skip if already in catalog (from pinned)
            if any(e["entity_id"] == entity["entity_id"] for e in catalog):
                continue
            
            catalog.append({
                "entity_id": entity["entity_id"],
                "entity_key": entity["entity_key"],
                "canonical_name": entity["canonical_name"],
                "entity_type": entity["entity_type"],
                "aliases": aliases,
                "context_hints": context_hints,
                "external_ids": external_ids,
                "metadata": metadata,
                "is_pinned": entity.get("is_pinned", False),
                "prior_weight": 0.5,  # Default weight for discovered entities
            })
    
    return catalog


def sync_pinned_to_db():
    """
    Sync pinned entities from config/pinned_entities.json to database.
    Creates entities if they don't exist, updates if they do.
    """
    config_file = Path(__file__).parent.parent.parent / "config" / "pinned_entities.json"
    if not config_file.exists():
        return
    
    with open(config_file, "r") as f:
        pinned_data = json.load(f)
    
    with EntityDAO() as dao:
        for entity_data in pinned_data:
            entity_id = entity_data["entity_id"]
            
            # Check if entity exists
            existing = dao.get_entity(entity_id)
            
            if existing:
                # Update to ensure it's pinned and active
                dao.update_entity(entity_id, {
                    "is_pinned": True,
                    "is_active": True,
                    "canonical_name": entity_data["canonical_name"],
                    "entity_type": entity_data["type"],
                    "external_ids": entity_data.get("external_ids", {}),
                    "context_hints": entity_data.get("context_hints", []),
                })
            else:
                # Create new entity
                dao.create_entity({
                    "entity_id": entity_id,
                    "entity_key": entity_data.get("entity_key", entity_id),
                    "canonical_name": entity_data["canonical_name"],
                    "entity_type": entity_data["type"],
                    "is_pinned": True,
                    "is_active": True,
                    "external_ids": entity_data.get("external_ids", {}),
                    "context_hints": entity_data.get("context_hints", []),
                    "first_seen_at": datetime.now(timezone.utc),
                })
            
            # Sync aliases
            aliases = entity_data.get("aliases", [])
            for alias in aliases:
                # Normalize alias for matching
                alias_norm = alias.lower().strip()
                try:
                    dao.create_alias(entity_id, alias, alias_norm)
                except Exception as e:
                    # Alias may already exist, skip silently
                    pass


if __name__ == "__main__":
    # Sync pinned entities to database
    sync_pinned_to_db()
    print("Pinned entities synced to database")
    
    # Load and display catalog
    catalog = load_catalog()
    print(f"Loaded {len(catalog)} entities from catalog")
    for entity in catalog[:5]:
        print(f"  - {entity['canonical_name']} ({entity['entity_type']})")
