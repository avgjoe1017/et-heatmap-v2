"""
Data access object for documents table.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from .base import BaseDAO


class DocumentDAO(BaseDAO):
    """DAO for documents table."""
    
    def create_document(self, doc_data: dict) -> str:
        """
        Create a new document.
        Returns doc_id.
        """
        data = {
            "doc_id": doc_data["doc_id"],
            "item_id": doc_data["item_id"],
            "doc_timestamp": doc_data.get("doc_timestamp", datetime.now(timezone.utc)),
            "lang": doc_data.get("lang", "en"),
            "text_title": doc_data.get("text_title"),
            "text_caption": doc_data.get("text_caption"),
            "text_body": doc_data.get("text_body"),
            "text_all": doc_data.get("text_all", ""),
            "quality_flags": json.dumps(doc_data.get("quality_flags", {})),
            "hash_sim": doc_data.get("hash_sim"),
        }
        
        # Handle datetime serialization
        if isinstance(data["doc_timestamp"], datetime):
            data["doc_timestamp"] = data["doc_timestamp"].isoformat()
        
        self.execute_insert("documents", data)
        return data["doc_id"]
    
    def get_document(self, doc_id: str) -> Optional[dict]:
        """Get document by ID."""
        results = self.execute_select("documents", {"doc_id": doc_id}, limit=1)
        if not results:
            return None
        
        doc = results[0]
        # Parse JSON fields
        doc["quality_flags"] = json.loads(doc.get("quality_flags", "{}"))
        return doc
    
    def get_documents_by_item(self, item_id: str) -> List[dict]:
        """
        Get documents for a source_item.
        """
        results = self.execute_select("documents", {"item_id": item_id})
        for doc in results:
            doc["quality_flags"] = json.loads(doc.get("quality_flags", "{}"))
        return results
    
    def get_documents_by_window(self, window_start: datetime, window_end: datetime) -> List[dict]:
        """Get documents in window."""
        if isinstance(window_start, datetime):
            window_start = window_start.isoformat()
        if isinstance(window_end, datetime):
            window_end = window_end.isoformat()
        
        query = """
            SELECT * FROM documents 
            WHERE doc_timestamp >= :window_start 
            AND doc_timestamp < :window_end
            ORDER BY doc_timestamp DESC
        """
        params = {"window_start": window_start, "window_end": window_end}
        result = self.execute_raw(query, params)
        
        docs = []
        for row in result:
            doc = dict(row._mapping)
            doc["quality_flags"] = json.loads(doc.get("quality_flags", "{}"))
            docs.append(doc)
        
        return docs


# Convenience functions
def create_document(doc_data: dict) -> str:
    """Create a new document."""
    with DocumentDAO() as dao:
        return dao.create_document(doc_data)

def get_documents_by_item(item_id: str) -> List[dict]:
    """Get documents for a source_item."""
    with DocumentDAO() as dao:
        return dao.get_documents_by_item(item_id)
