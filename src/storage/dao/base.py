"""
Base DAO functionality.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import text, select
from sqlalchemy.orm import Session

from src.storage.db import get_session


class BaseDAO:
    """Base DAO with common database operations."""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session
        self._own_session = session is None
    
    def __enter__(self):
        if self._own_session:
            self.session = get_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._own_session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()
    
    def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Execute raw SQL query."""
        if params is None:
            params = {}
        return self.session.execute(text(query), params)
    
    def execute_select(self, table_name: str, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None):
        """Execute SELECT query on table."""
        query = f"SELECT * FROM {table_name}"
        params = {}
        
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = :{key}")
                params[key] = value
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        if limit:
            query += f" LIMIT {limit}"
        
        result = self.execute_raw(query, params)
        return [dict(row._mapping) for row in result]
    
    def execute_insert(self, table_name: str, data: Dict[str, Any]) -> str:
        """Execute INSERT query."""
        columns = list(data.keys())
        placeholders = [f":{col}" for col in columns]
        
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        result = self.execute_raw(query, data)
        self.session.commit()
        return str(result.lastrowid) if hasattr(result, 'lastrowid') else "0"
    
    def execute_update(self, table_name: str, data: Dict[str, Any], filters: Dict[str, Any]):
        """Execute UPDATE query."""
        set_clauses = [f"{key} = :{key}_new" for key in data.keys()]
        where_clauses = [f"{key} = :{key}_filter" for key in filters.keys()]
        
        params = {f"{k}_new": v for k, v in data.items()}
        params.update({f"{k}_filter": v for k, v in filters.items()})
        
        query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
        result = self.execute_raw(query, params)
        self.session.commit()
        return result.rowcount
    
    def execute_delete(self, table_name: str, filters: Dict[str, Any]):
        """Execute DELETE query."""
        where_clauses = [f"{key} = :{key}" for key in filters.keys()]
        params = filters
        
        query = f"DELETE FROM {table_name} WHERE {' AND '.join(where_clauses)}"
        result = self.execute_raw(query, params)
        self.session.commit()
        return result.rowcount
