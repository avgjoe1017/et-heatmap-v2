"""
Compute baseline fame for entities using Google Trends and Wikipedia pageviews.
Baseline fame is updated weekly and used as a stable reference point.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import json

from src.storage.dao.entities import EntityDAO
from src.storage.dao.snapshots import SnapshotDAO

logger = logging.getLogger(__name__)


def compute_baseline_fame(
    entities: List[dict],
    week_start: Optional[datetime] = None
) -> List[dict]:
    """
    Compute baseline fame for entities using:
    - Google Trends interest (weekly)
    - Wikipedia pageviews (lagged ~24h)
    - 90-day rolling average conversation volume
    
    Returns list of entity_weekly_baseline records.
    """
    if not entities:
        return []
    
    # Default to start of current week
    if week_start is None:
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    baseline_records = []
    
    # TODO: Integrate Google Trends via pytrends
    # For now, use placeholder logic
    
    # TODO: Integrate Wikipedia pageviews API
    # For now, use placeholder logic
    
    # For v1, compute baseline from 90-day rolling average of mentions
    # This is a proxy until external APIs are integrated
    for entity in entities:
        entity_id = entity["entity_id"]
        canonical_name = entity["canonical_name"]
        
        # Get 90-day mention volume from database
        baseline_fame = _compute_90d_mention_volume(entity_id, week_start)
        
        # Placeholder for Google Trends (0-100 scale)
        trends_score = 50.0  # TODO: Fetch from pytrends
        
        # Placeholder for Wikipedia pageviews (normalized)
        wikipedia_score = 50.0  # TODO: Fetch from Wikipedia API
        
        # Combine scores (weighted average)
        # For now, use mention volume as primary signal
        baseline = (
            0.4 * baseline_fame +  # 40% from mention volume
            0.3 * trends_score +   # 30% from Google Trends
            0.3 * wikipedia_score  # 30% from Wikipedia
        )
        
        baseline_records.append({
            "entity_id": entity_id,
            "week_start": week_start.isoformat(),
            "baseline_fame": float(baseline),
            "google_trends_score": float(trends_score),
            "wikipedia_pageviews": float(wikipedia_score),
            "mention_volume_90d": float(baseline_fame),
        })
    
    logger.info(f"Computed baseline fame for {len(baseline_records)} entities")
    return baseline_records


def _compute_90d_mention_volume(entity_id: str, week_start: datetime) -> float:
    """
    Compute 90-day rolling average mention volume for an entity.
    Returns normalized score 0-100.
    """
    from src.storage.dao.mentions import MentionDAO
    from sqlalchemy import text, func
    
    window_start = week_start - timedelta(days=90)
    
    with MentionDAO() as dao:
        # Count mentions in 90-day window
        query = text("""
            SELECT COUNT(*) as mention_count
            FROM mentions m
            JOIN documents d ON m.doc_id = d.doc_id
            WHERE m.entity_id = :entity_id
            AND d.doc_timestamp >= :window_start
            AND d.doc_timestamp < :week_start
        """)
        
        result = dao.execute_raw(query, {
            "entity_id": entity_id,
            "window_start": window_start.isoformat(),
            "week_start": week_start.isoformat()
        })
        
        rows = list(result)
        if rows:
            mention_count = rows[0][0] or 0
        else:
            mention_count = 0
    
    # Normalize to 0-100 scale (log scale, max at ~1000 mentions)
    # This is a rough heuristic - should be calibrated with actual data
    if mention_count == 0:
        return 0.0
    
    import math
    normalized = min(100.0, (math.log1p(mention_count) / math.log1p(1000)) * 100.0)
    return normalized


def update_baseline_fame(entities: List[dict], week_start: Optional[datetime] = None):
    """
    Compute and store baseline fame for entities.
    Updates entity_weekly_baseline table.
    """
    baseline_records = compute_baseline_fame(entities, week_start)
    
    if not baseline_records:
        return
    
    with SnapshotDAO() as dao:
        for record in baseline_records:
            try:
                # Create or update baseline record
                dao.create_entity_weekly_baseline(record)
            except Exception as e:
                logger.warning(f"Failed to store baseline fame for {record['entity_id']}: {e}")
