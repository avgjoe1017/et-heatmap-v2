"""
Data access object for snapshots (entity_daily_metrics, drivers, themes).
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from .base import BaseDAO


class SnapshotDAO(BaseDAO):
    """DAO for entity_daily_metrics, drivers, and themes."""
    
    def create_entity_daily_metrics(self, metrics_data: dict) -> None:
        """
        Create entity_daily_metrics record.
        """
        metadata = metrics_data.get("metadata", {})
        if isinstance(metadata, dict):
            metadata = json.dumps(metadata)
        elif isinstance(metadata, str):
            pass
        else:
            metadata = "{}"
        
        data = {
            "run_id": metrics_data["run_id"],
            "entity_id": metrics_data["entity_id"],
            "fame": metrics_data.get("fame", 0.0),
            "love": metrics_data.get("love", 50.0),
            "attention": metrics_data.get("attention", 0.0),
            "baseline_fame": metrics_data.get("baseline_fame"),
            "momentum": metrics_data.get("momentum", 0.0),
            "polarization": metrics_data.get("polarization", 0.0),
            "confidence": metrics_data.get("confidence", 0.0),
            "mentions_explicit": metrics_data.get("mentions_explicit", 0),
            "mentions_implicit": metrics_data.get("mentions_implicit", 0),
            "sources_distinct": metrics_data.get("sources_distinct", 0),
            "is_dormant": metrics_data.get("is_dormant", False),
            "dormant_reason": metrics_data.get("dormant_reason"),
            "metadata": metadata,
        }
        
        # Insert or update (upsert)
        try:
            self.execute_insert("entity_daily_metrics", data)
        except Exception:
            # If exists, update instead
            updates = {k: v for k, v in data.items() if k not in ["run_id", "entity_id"]}
            self.execute_update("entity_daily_metrics", updates, {
                "run_id": data["run_id"],
                "entity_id": data["entity_id"]
            })
    
    def get_entity_metrics_for_run(self, run_id: str) -> List[dict]:
        """
        Get entity_daily_metrics for a run.
        """
        results = self.execute_select("entity_daily_metrics", {"run_id": run_id})
        for metrics in results:
            metrics["metadata"] = json.loads(metrics.get("metadata", "{}"))
        return results
    
    def get_entity_metrics_for_window(self, entity_id: str, window_start: datetime, window_end: datetime) -> List[dict]:
        """
        Get historical entity_daily_metrics for an entity.
        """
        if isinstance(window_start, datetime):
            window_start = window_start.isoformat()
        if isinstance(window_end, datetime):
            window_end = window_end.isoformat()
        
        query = """
            SELECT m.* FROM entity_daily_metrics m
            JOIN runs r ON m.run_id = r.run_id
            WHERE m.entity_id = :entity_id
            AND r.window_start >= :window_start
            AND r.window_start < :window_end
            ORDER BY r.window_start ASC
        """
        params = {
            "entity_id": entity_id,
            "window_start": window_start,
            "window_end": window_end
        }
        result = self.execute_raw(query, params)
        
        metrics = []
        for row in result:
            m = dict(row._mapping)
            m["metadata"] = json.loads(m.get("metadata", "{}"))
            metrics.append(m)
        
        return metrics
    
    def get_latest_metrics_for_entity(self, entity_id: str) -> Optional[dict]:
        """Get latest metrics for an entity."""
        query = """
            SELECT m.* FROM entity_daily_metrics m
            JOIN runs r ON m.run_id = r.run_id
            WHERE m.entity_id = :entity_id
            ORDER BY r.window_start DESC
            LIMIT 1
        """
        params = {"entity_id": entity_id}
        result = self.execute_raw(query, params)
        
        rows = [dict(row._mapping) for row in result]
        if not rows:
            return None
        
        metrics = rows[0]
        metrics["metadata"] = json.loads(metrics.get("metadata", "{}"))
        return metrics
    
    def create_entity_daily_driver(self, driver_data: dict) -> None:
        """Create entity_daily_drivers record."""
        data = {
            "run_id": driver_data["run_id"],
            "entity_id": driver_data["entity_id"],
            "rank": driver_data["rank"],
            "item_id": driver_data["item_id"],
            "impact_score": driver_data["impact_score"],
            "driver_reason": driver_data.get("driver_reason"),
        }
        
        try:
            self.execute_insert("entity_daily_drivers", data)
        except Exception:
            # If exists, update
            updates = {k: v for k, v in data.items() if k not in ["run_id", "entity_id", "rank"]}
            self.execute_update("entity_daily_drivers", updates, {
                "run_id": data["run_id"],
                "entity_id": data["entity_id"],
                "rank": data["rank"]
            })
    
    def get_drivers_for_entity(self, run_id: str, entity_id: str) -> List[dict]:
        """Get drivers for an entity in a run."""
        query = """
            SELECT d.* FROM entity_daily_drivers d
            WHERE d.run_id = :run_id AND d.entity_id = :entity_id
            ORDER BY d.rank ASC
        """
        params = {"run_id": run_id, "entity_id": entity_id}
        result = self.execute_raw(query, params)
        return [dict(row._mapping) for row in result]
    
    def create_entity_daily_theme(self, theme_data: dict) -> None:
        """Create entity_daily_themes record."""
        keywords = theme_data.get("keywords", [])
        if isinstance(keywords, list):
            keywords = json.dumps(keywords)
        
        sentiment_mix = theme_data.get("sentiment_mix", {})
        if isinstance(sentiment_mix, dict):
            sentiment_mix = json.dumps(sentiment_mix)
        
        data = {
            "run_id": theme_data["run_id"],
            "entity_id": theme_data["entity_id"],
            "theme_id": theme_data["theme_id"],
            "label": theme_data["label"],
            "keywords": keywords,
            "volume": theme_data.get("volume", 0),
            "sentiment_mix": sentiment_mix,
        }
        
        try:
            self.execute_insert("entity_daily_themes", data)
        except Exception:
            # If exists, update
            updates = {k: v for k, v in data.items() if k not in ["run_id", "entity_id", "theme_id"]}
            self.execute_update("entity_daily_themes", updates, {
                "run_id": data["run_id"],
                "entity_id": data["entity_id"],
                "theme_id": data["theme_id"]
            })
    
    def get_themes_for_entity(self, run_id: str, entity_id: str) -> List[dict]:
        """Get themes for an entity in a run."""
        query = """
            SELECT t.* FROM entity_daily_themes t
            WHERE t.run_id = :run_id AND t.entity_id = :entity_id
            ORDER BY t.volume DESC
        """
        params = {"run_id": run_id, "entity_id": entity_id}
        result = self.execute_raw(query, params)
        
        themes = []
        for row in result:
            theme = dict(row._mapping)
            theme["keywords"] = json.loads(theme.get("keywords", "[]"))
            theme["sentiment_mix"] = json.loads(theme.get("sentiment_mix", "{}"))
            themes.append(theme)
        
        return themes
    
    def create_entity_weekly_baseline(self, baseline_data: dict) -> None:
        """Create or update entity_weekly_baseline record."""
        metadata = baseline_data.get("metadata", {})
        if isinstance(metadata, dict):
            metadata = json.dumps(metadata)
        
        data = {
            "entity_id": baseline_data["entity_id"],
            "week_start": baseline_data["week_start"],
            "baseline_fame": baseline_data.get("baseline_fame", 0.0),
            "google_trends_score": baseline_data.get("google_trends_score"),
            "wikipedia_pageviews": baseline_data.get("wikipedia_pageviews"),
            "mention_volume_90d": baseline_data.get("mention_volume_90d"),
            "metadata": metadata,
        }
        
        try:
            self.execute_insert("entity_weekly_baseline", data)
        except Exception:
            # If exists, update
            updates = {k: v for k, v in data.items() if k not in ["entity_id", "week_start"]}
            self.execute_update("entity_weekly_baseline", updates, {
                "entity_id": data["entity_id"],
                "week_start": data["week_start"]
            })
    
    def get_baseline_for_entity(self, entity_id: str, week_start: Optional[str] = None) -> Optional[dict]:
        """Get baseline fame for an entity."""
        if week_start:
            results = self.execute_select("entity_weekly_baseline", {
                "entity_id": entity_id,
                "week_start": week_start
            }, limit=1)
        else:
            # Get latest
            query = """
                SELECT * FROM entity_weekly_baseline
                WHERE entity_id = :entity_id
                ORDER BY week_start DESC
                LIMIT 1
            """
            result = self.execute_raw(query, {"entity_id": entity_id})
            results = [dict(row._mapping) for row in result]
        
        return results[0] if results else None


# Convenience functions
def create_entity_daily_metrics(metrics_data: dict) -> None:
    """Create entity_daily_metrics record."""
    with SnapshotDAO() as dao:
        dao.create_entity_daily_metrics(metrics_data)

def get_entity_metrics_for_run(run_id: str) -> List[dict]:
    """Get entity_daily_metrics for a run."""
    with SnapshotDAO() as dao:
        return dao.get_entity_metrics_for_run(run_id)

def get_entity_metrics_for_window(entity_id: str, window_start: datetime, window_end: datetime) -> List[dict]:
    """Get historical entity_daily_metrics for an entity."""
    with SnapshotDAO() as dao:
        return dao.get_entity_metrics_for_window(entity_id, window_start, window_end)
