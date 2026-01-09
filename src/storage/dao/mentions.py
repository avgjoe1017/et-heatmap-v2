"""
Data access object for mentions table.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from .base import BaseDAO


class MentionDAO(BaseDAO):
    """DAO for mentions table."""
    
    def create_mention(self, mention_data: dict) -> str:
        """
        Create a new mention.
        Returns mention_id.
        """
        # Handle JSON serialization for features
        features = mention_data.get("features", {})
        if isinstance(features, dict):
            features = json.dumps(features)
        elif isinstance(features, str):
            # Already serialized
            pass
        else:
            features = "{}"
        
        data = {
            "mention_id": mention_data["mention_id"],
            "doc_id": mention_data["doc_id"],
            "entity_id": mention_data["entity_id"],
            "sent_idx": mention_data.get("sent_idx"),
            "span_start": mention_data.get("span_start"),
            "span_end": mention_data.get("span_end"),
            "surface": mention_data.get("surface"),
            "is_implicit": mention_data.get("is_implicit", False),
            "weight": mention_data.get("weight", 1.0),
            "resolve_confidence": mention_data.get("resolve_confidence", 1.0),
            "features": features,
        }
        
        self.execute_insert("mentions", data)
        return data["mention_id"]
    
    def get_mention(self, mention_id: str) -> Optional[dict]:
        """Get mention by ID."""
        results = self.execute_select("mentions", {"mention_id": mention_id}, limit=1)
        if not results:
            return None
        
        mention = results[0]
        # Parse JSON fields
        mention["features"] = json.loads(mention.get("features", "{}"))
        return mention
    
    def get_mentions_by_entity(self, entity_id: str, window_start: Optional[datetime] = None, window_end: Optional[datetime] = None) -> List[dict]:
        """
        Get mentions for an entity in window.
        """
        if window_start and window_end:
            # Join with documents to filter by timestamp
            if isinstance(window_start, datetime):
                window_start = window_start.isoformat()
            if isinstance(window_end, datetime):
                window_end = window_end.isoformat()
            
            query = """
                SELECT m.* FROM mentions m
                JOIN documents d ON m.doc_id = d.doc_id
                WHERE m.entity_id = :entity_id
                AND d.doc_timestamp >= :window_start
                AND d.doc_timestamp < :window_end
                ORDER BY d.doc_timestamp DESC
            """
            params = {
                "entity_id": entity_id,
                "window_start": window_start,
                "window_end": window_end
            }
            result = self.execute_raw(query, params)
        else:
            # No window filter
            result = self.execute_select("mentions", {"entity_id": entity_id})
            result = [{"mention_id": r["mention_id"], **r} for r in result]
        
        mentions = []
        for row in result:
            if isinstance(row, dict):
                mention = row
            else:
                mention = dict(row._mapping)
            mention["features"] = json.loads(mention.get("features", "{}"))
            mentions.append(mention)
        
        return mentions
    
    def get_mentions_by_doc(self, doc_id: str) -> List[dict]:
        """Get mentions for a document."""
        results = self.execute_select("mentions", {"doc_id": doc_id})
        for mention in results:
            mention["features"] = json.loads(mention.get("features", "{}"))
        return results
    
    def get_mentions_count_by_entity(self, window_start: datetime, window_end: datetime) -> Dict[str, int]:
        """Get mention counts per entity in window."""
        if isinstance(window_start, datetime):
            window_start = window_start.isoformat()
        if isinstance(window_end, datetime):
            window_end = window_end.isoformat()
        
        query = """
            SELECT m.entity_id, COUNT(*) as count
            FROM mentions m
            JOIN documents d ON m.doc_id = d.doc_id
            WHERE d.doc_timestamp >= :window_start
            AND d.doc_timestamp < :window_end
            GROUP BY m.entity_id
        """
        params = {"window_start": window_start, "window_end": window_end}
        result = self.execute_raw(query, params)
        
        return {row[0]: row[1] for row in result}


# Convenience functions
def create_mention(mention_data: dict) -> str:
    """Create a new mention."""
    with MentionDAO() as dao:
        return dao.create_mention(mention_data)

def get_mentions_by_entity(entity_id: str, window_start: datetime, window_end: datetime) -> List[dict]:
    """Get mentions for an entity in window."""
    with MentionDAO() as dao:
        return dao.get_mentions_by_entity(entity_id, window_start, window_end)
