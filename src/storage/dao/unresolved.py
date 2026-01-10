"""
Data access object for unresolved_mentions table.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from .base import BaseDAO


class UnresolvedDAO(BaseDAO):
    """DAO for unresolved_mentions table."""
    
    def create_unresolved_mention(self, unresolved_data: dict) -> str:
        """
        Create unresolved_mention record.
        Returns unresolved_id.
        """
        candidates = unresolved_data.get("candidates", [])
        if isinstance(candidates, list):
            candidates = json.dumps(candidates)
        elif isinstance(candidates, str):
            pass
        else:
            candidates = "[]"
        
        data = {
            "unresolved_id": unresolved_data["unresolved_id"],
            "doc_id": unresolved_data["doc_id"],
            "surface": unresolved_data["surface"],
            "surface_norm": unresolved_data.get("surface_norm", unresolved_data["surface"].lower()),
            "sent_idx": unresolved_data.get("sent_idx"),
            "context": unresolved_data.get("context"),
            "candidates": candidates,
            "top_score": unresolved_data.get("top_score"),
            "second_score": unresolved_data.get("second_score"),
            "created_at": unresolved_data.get("created_at", datetime.now(timezone.utc)),
        }
        
        # Handle datetime serialization
        if isinstance(data["created_at"], datetime):
            data["created_at"] = data["created_at"].isoformat()
        
        self.execute_insert("unresolved_mentions", data)
        return data["unresolved_id"]
    
    def get_unresolved_for_window(self, window_start: datetime, window_end: datetime) -> List[dict]:
        """
        Get unresolved_mentions for window.
        """
        if isinstance(window_start, datetime):
            window_start = window_start.isoformat()
        if isinstance(window_end, datetime):
            window_end = window_end.isoformat()
        
        query = """
            SELECT u.* FROM unresolved_mentions u
            JOIN documents d ON u.doc_id = d.doc_id
            WHERE d.doc_timestamp >= :window_start
            AND d.doc_timestamp < :window_end
            ORDER BY u.created_at DESC
        """
        params = {"window_start": window_start, "window_end": window_end}
        result = self.execute_raw(query, params)
        
        unresolved = []
        for row in result:
            u = dict(row._mapping)
            u["candidates"] = json.loads(u.get("candidates", "[]"))
            unresolved.append(u)
        
        return unresolved
    
    def get_unresolved_aggregated(self, window_start: datetime, window_end: datetime, limit: int = 100) -> List[dict]:
        """
        Get aggregated unresolved mentions by surface_norm, sorted by count/impact.
        """
        if isinstance(window_start, datetime):
            window_start = window_start.isoformat()
        if isinstance(window_end, datetime):
            window_end = window_end.isoformat()
        
        # SQLite doesn't support MAX on JSONB, so we'll fetch a sample row per group
        query = """
            SELECT 
                u.surface,
                u.surface_norm,
                COUNT(*) as count,
                MAX(u.top_score) as top_score,
                MAX(u.second_score) as second_score
            FROM unresolved_mentions u
            JOIN documents d ON u.doc_id = d.doc_id
            WHERE d.doc_timestamp >= :window_start
            AND d.doc_timestamp < :window_end
            GROUP BY u.surface_norm, u.surface
            ORDER BY count DESC
            LIMIT :limit
        """
        params = {"window_start": window_start, "window_end": window_end, "limit": limit}
        result = self.execute_raw(query, params)
        
        aggregated = []
        for row in result:
            surface_norm = row[1]
            
            # Get a sample unresolved mention for context and candidates
            sample_query = """
                SELECT context, candidates
                FROM unresolved_mentions
                WHERE surface_norm = :surface_norm
                LIMIT 1
            """
            sample_result = self.execute_raw(sample_query, {"surface_norm": surface_norm})
            sample_rows = [dict(r._mapping) for r in sample_result]
            
            example_context = sample_rows[0].get("context", "") if sample_rows else ""
            example_candidates_raw = sample_rows[0].get("candidates", "[]") if sample_rows else "[]"
            
            # Parse candidates (handle JSONB string or already parsed)
            if isinstance(example_candidates_raw, str):
                try:
                    example_candidates = json.loads(example_candidates_raw)
                except:
                    example_candidates = []
            else:
                example_candidates = example_candidates_raw if isinstance(example_candidates_raw, list) else []
            
            agg = {
                "surface": row[0],
                "surface_norm": surface_norm,
                "count": row[2],
                "top_score": row[3] if row[3] is not None else None,
                "second_score": row[4] if row[4] is not None else None,
                "example_context": example_context,
                "example_candidates": example_candidates
            }
            aggregated.append(agg)
        
        return aggregated


# Convenience functions
def create_unresolved_mention(unresolved_data: dict) -> str:
    """Create unresolved_mention record."""
    with UnresolvedDAO() as dao:
        return dao.create_unresolved_mention(unresolved_data)

def get_unresolved_for_window(window_start: datetime, window_end: datetime) -> List[dict]:
    """Get unresolved_mentions for window."""
    with UnresolvedDAO() as dao:
        return dao.get_unresolved_for_window(window_start, window_end)
