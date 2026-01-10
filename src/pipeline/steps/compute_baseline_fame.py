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
    
    # Fetch Google Trends scores
    trends_scores = _fetch_google_trends(entities, week_start)
    
    # Fetch Wikipedia pageviews
    wikipedia_scores = _fetch_wikipedia_pageviews(entities, week_start)
    
    # For v1, compute baseline from 90-day rolling average of mentions
    for entity in entities:
        entity_id = entity["entity_id"]
        canonical_name = entity["canonical_name"]
        
        # Get 90-day mention volume from database
        baseline_fame = _compute_90d_mention_volume(entity_id, week_start)
        
        # Get Google Trends score (or default to 50.0)
        trends_score = trends_scores.get(entity_id, 50.0)
        
        # Get Wikipedia pageviews score (or default to 50.0)
        wikipedia_score = wikipedia_scores.get(entity_id, 50.0)
        
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
    
    window_start = week_start - timedelta(days=90)
    
    with MentionDAO() as dao:
        # Count mentions in 90-day window
        query_str = """
            SELECT COUNT(*) as mention_count
            FROM mentions m
            JOIN documents d ON m.doc_id = d.doc_id
            WHERE m.entity_id = :entity_id
            AND d.doc_timestamp >= :window_start
            AND d.doc_timestamp < :week_start
        """
        
        result = dao.execute_raw(query_str, {
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


def _fetch_google_trends(entities: List[dict], week_start: datetime) -> Dict[str, float]:
    """
    Fetch Google Trends interest scores for entities.
    Returns dict of entity_id -> trends_score (0-100).
    """
    trends_scores = {}
    
    try:
        from pytrends.request import TrendReq
        import time
        
        pytrends = TrendReq(hl='en-US', tz=360)
        
        # Google Trends requires date range
        # Use last 7 days for weekly baseline
        end_date = week_start
        start_date = week_start - timedelta(days=7)
        
        for entity in entities:
            entity_id = entity["entity_id"]
            canonical_name = entity["canonical_name"]
            
            try:
                # Build payload
                pytrends.build_payload(
                    [canonical_name],
                    cat=0,
                    timeframe=f'{start_date.strftime("%Y-%m-%d")} {end_date.strftime("%Y-%m-%d")}',
                    geo='',
                    gprop=''
                )
                
                # Get interest over time
                data = pytrends.interest_over_time()
                
                if not data.empty:
                    # Average interest over the period
                    avg_interest = data[canonical_name].mean()
                    # Google Trends returns 0-100, normalize to our scale
                    trends_scores[entity_id] = float(avg_interest)
                else:
                    trends_scores[entity_id] = 50.0  # Default if no data
                
                # Rate limiting - be nice to Google
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Failed to fetch Google Trends for {canonical_name}: {e}")
                trends_scores[entity_id] = 50.0  # Default on error
        
    except ImportError:
        logger.info("pytrends not installed, using default trends scores")
        for entity in entities:
            trends_scores[entity["entity_id"]] = 50.0
    except Exception as e:
        logger.warning(f"Google Trends API error: {e}, using default scores")
        for entity in entities:
            trends_scores[entity["entity_id"]] = 50.0
    
    return trends_scores


def _fetch_wikipedia_pageviews(entities: List[dict], week_start: datetime) -> Dict[str, float]:
    """
    Fetch Wikipedia pageviews for entities.
    Returns dict of entity_id -> normalized pageview score (0-100).
    """
    wikipedia_scores = {}
    
    try:
        import requests
        from datetime import timedelta
        
        # Wikipedia pageviews API endpoint
        base_url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user"
        
        # Use last 7 days (Wikipedia data is lagged ~24h)
        end_date = week_start - timedelta(days=1)  # Yesterday (lagged)
        start_date = end_date - timedelta(days=7)
        
        for entity in entities:
            entity_id = entity["entity_id"]
            canonical_name = entity["canonical_name"]
            
            # Get Wikidata ID
            external_ids = entity.get("external_ids", {})
            wikidata_id = external_ids.get("wikidata")
            
            if not wikidata_id:
                wikipedia_scores[entity_id] = 50.0  # Default if no Wikidata ID
                continue
            
            try:
                # Convert Wikidata QID to Wikipedia title
                # For now, use canonical name (this is simplified - should use Wikidata API to get Wikipedia title)
                title = canonical_name.replace(" ", "_")
                # URL encode the title
                import urllib.parse
                title_encoded = urllib.parse.quote(title, safe='')
                
                # Build API URL
                url = f"{base_url}/{title_encoded}/daily/{start_date.strftime('%Y%m%d')}/{end_date.strftime('%Y%m%d')}"
                
                # Add headers to avoid 403 (some APIs require User-Agent)
                headers = {
                    'User-Agent': 'ET-Heatmap/0.1.0 (https://github.com/yourusername/et-heatmap)'
                }
                
                response = requests.get(url, timeout=10, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Sum pageviews over the period
                    total_views = 0
                    if "items" in data:
                        for item in data["items"]:
                            total_views += item.get("views", 0)
                    
                    # Normalize to 0-100 scale (log scale, max at ~1M views)
                    if total_views > 0:
                        import math
                        normalized = min(100.0, (math.log1p(total_views) / math.log1p(1000000)) * 100.0)
                        wikipedia_scores[entity_id] = float(normalized)
                    else:
                        wikipedia_scores[entity_id] = 0.0
                else:
                    logger.warning(f"Wikipedia API returned {response.status_code} for {canonical_name}")
                    wikipedia_scores[entity_id] = 50.0  # Default on error
                
                # Rate limiting
                import time
                time.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Failed to fetch Wikipedia pageviews for {canonical_name}: {e}")
                wikipedia_scores[entity_id] = 50.0  # Default on error
        
    except ImportError:
        logger.info("requests not installed, using default Wikipedia scores")
        for entity in entities:
            wikipedia_scores[entity["entity_id"]] = 50.0
    except Exception as e:
        logger.warning(f"Wikipedia API error: {e}, using default scores")
        for entity in entities:
            wikipedia_scores[entity["entity_id"]] = 50.0
    
    return wikipedia_scores


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
