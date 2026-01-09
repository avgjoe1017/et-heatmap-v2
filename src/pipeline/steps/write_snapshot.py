"""
Write snapshot data to database (for API).
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
import logging

from src.storage.dao.snapshots import SnapshotDAO

logger = logging.getLogger(__name__)


def write_snapshot(run_id: str, entity_metrics: List[dict], drivers: List[dict] = None, themes: List[dict] = None) -> None:
    """
    Write entity_daily_metrics to database for a run.
    This is what the API reads to build snapshots.
    """
    if not entity_metrics:
        logger.warning("No entity metrics to write")
        return
    
    drivers = drivers or []
    themes = themes or []
    
    with SnapshotDAO() as dao:
        # Write entity daily metrics
        for metrics in entity_metrics:
            metrics_with_run = {**metrics, "run_id": run_id}
            dao.create_entity_daily_metrics(metrics_with_run)
        
        # Write drivers
        for driver in drivers:
            driver_with_run = {**driver, "run_id": run_id}
            dao.create_entity_daily_driver(driver_with_run)
        
        # Write themes
        for theme in themes:
            theme_with_run = {**theme, "run_id": run_id}
            dao.create_entity_daily_theme(theme_with_run)
    
    logger.info(f"Wrote snapshot for {len(entity_metrics)} entities, {len(drivers)} drivers, {len(themes)} themes")
