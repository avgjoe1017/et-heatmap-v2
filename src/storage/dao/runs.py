"""
Data access object for runs table.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging
from .base import BaseDAO


class RunDAO(BaseDAO):
    """DAO for runs table."""
    
    def create_run(self, run_data: dict) -> str:
        """
        Create a new run.
        Returns run_id.
        Checks for existing run for this window first.
        """
        # Handle datetime serialization for SQLite
        window_start = run_data["window_start"]
        window_end = run_data["window_end"]
        if isinstance(window_start, datetime):
            window_start = window_start.isoformat()
        if isinstance(window_end, datetime):
            window_end = window_end.isoformat()
        
        # Check if run already exists for this window
        existing = self.get_run_by_window(window_start, window_end)
        if existing:
            logger = logging.getLogger(__name__)
            logger.info(f"Run already exists for window {window_start} to {window_end}, using existing run_id: {existing['run_id']}")
            return existing["run_id"]
        
        data = {
            "run_id": run_data["run_id"],
            "window_start": window_start,
            "window_end": window_end,
            "started_at": run_data.get("started_at", datetime.now(timezone.utc)),
            "finished_at": run_data.get("finished_at"),
            "status": run_data.get("status", "RUNNING"),
            "config_hash": run_data.get("config_hash"),
            "notes": run_data.get("notes"),
        }
        
        # Handle datetime serialization for SQLite
        if isinstance(data["started_at"], datetime):
            data["started_at"] = data["started_at"].isoformat()
        if data.get("finished_at") and isinstance(data["finished_at"], datetime):
            data["finished_at"] = data["finished_at"].isoformat()
        
        self.execute_insert("runs", data)
        return data["run_id"]
    
    def get_run_by_window(self, window_start: str, window_end: str) -> Optional[dict]:
        """Get run by window."""
        query = """
            SELECT * FROM runs 
            WHERE window_start = :window_start 
            AND window_end = :window_end
            LIMIT 1
        """
        result = self.execute_raw(query, {"window_start": window_start, "window_end": window_end})
        rows = [dict(row._mapping) for row in result]
        return rows[0] if rows else None
    
    def get_run(self, run_id: str) -> Optional[dict]:
        """Get run by ID."""
        results = self.execute_select("runs", {"run_id": run_id}, limit=1)
        if not results:
            return None
        return results[0]
    
    def get_latest_run(self) -> Optional[dict]:
        """
        Get the latest run.
        """
        query = "SELECT * FROM runs ORDER BY started_at DESC LIMIT 1"
        result = self.execute_raw(query)
        rows = [dict(row._mapping) for row in result]
        return rows[0] if rows else None
    
    def get_runs_by_status(self, status: str) -> List[dict]:
        """Get runs by status."""
        return self.execute_select("runs", {"status": status})
    
    def update_run_status(self, run_id: str, status: str, finished_at: Optional[datetime] = None) -> int:
        """
        Update run status.
        Returns number of rows updated.
        """
        updates = {"status": status}
        if finished_at:
            if isinstance(finished_at, datetime):
                finished_at = finished_at.isoformat()
            updates["finished_at"] = finished_at
        
        return self.execute_update("runs", updates, {"run_id": run_id})
    
    def update_run(self, run_id: str, updates: dict) -> int:
        """Update run fields."""
        # Handle datetime serialization
        for key, value in updates.items():
            if isinstance(value, datetime):
                updates[key] = value.isoformat()
        
        return self.execute_update("runs", updates, {"run_id": run_id})


# Convenience functions
def create_run(run_data: dict) -> str:
    """Create a new run."""
    with RunDAO() as dao:
        return dao.create_run(run_data)

def get_latest_run() -> Optional[dict]:
    """Get the latest run."""
    with RunDAO() as dao:
        return dao.get_latest_run()

def update_run_status(run_id: str, status: str, finished_at: Optional[datetime] = None) -> int:
    """Update run status."""
    with RunDAO() as dao:
        return dao.update_run_status(run_id, status, finished_at)
