"""
Ingest Wikipedia pageviews (optional baseline confirmation).
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta, timezone
import requests

from src.catalog.catalog_loader import load_catalog
from src.storage.dao.snapshots import SnapshotDAO

logger = logging.getLogger(__name__)


def ingest_wikipedia_pageviews(week_start: Optional[datetime] = None) -> Dict[str, int]:
    """
    Fetch Wikipedia pageviews for entities (lagged baseline).
    Updates entity_weekly_baseline table.
    
    Returns dict of entity_id -> pageview count.
    """
    if week_start is None:
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Load entities with Wikidata IDs
    catalog = load_catalog()
    
    # Wikipedia pageviews API endpoint
    base_url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user"
    
    # Use last 7 days (Wikipedia data is lagged ~24h)
    end_date = week_start - timedelta(days=1)  # Yesterday (lagged)
    start_date = end_date - timedelta(days=7)
    
    pageview_counts = {}
    
    for entity in catalog:
        entity_id = entity["entity_id"]
        canonical_name = entity["canonical_name"]
        
        # Get Wikidata ID
        external_ids = entity.get("external_ids", {})
        wikidata_id = external_ids.get("wikidata")
        
        if not wikidata_id:
            continue  # Skip entities without Wikidata IDs
        
        try:
            # Convert canonical name to Wikipedia title format
            # Note: This is simplified - ideally we'd use Wikidata API to get exact Wikipedia title
            # Wikipedia titles are case-sensitive and use underscores
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
                
                pageview_counts[entity_id] = total_views
                
                logger.info(f"Fetched {total_views} pageviews for {canonical_name}")
            elif response.status_code == 404:
                # Page doesn't exist or title mismatch
                logger.debug(f"Wikipedia page not found for {canonical_name} (title: {title})")
                pageview_counts[entity_id] = 0
            else:
                logger.warning(f"Wikipedia API returned {response.status_code} for {canonical_name}")
                pageview_counts[entity_id] = 0
            
            # Rate limiting - be nice to Wikimedia
            import time
            time.sleep(0.5)
            
        except Exception as e:
            logger.warning(f"Failed to fetch Wikipedia pageviews for {canonical_name}: {e}")
            pageview_counts[entity_id] = 0
    
    # Update baseline records with Wikipedia data
    if pageview_counts:
        with SnapshotDAO() as dao:
            for entity_id, pageviews in pageview_counts.items():
                try:
                    # Get existing baseline
                    baseline = dao.get_baseline_for_entity(entity_id, week_start.isoformat())
                    
                    if baseline:
                        # Normalize pageviews to 0-100 scale
                        import math
                        normalized = min(100.0, (math.log1p(pageviews) / math.log1p(1000000)) * 100.0) if pageviews > 0 else 0.0
                        
                        # Update baseline record
                        dao.execute_update("entity_weekly_baseline", {
                            "wikipedia_pageviews": float(normalized)
                        }, {
                            "entity_id": entity_id,
                            "week_start": week_start.isoformat()
                        })
                except Exception as e:
                    logger.warning(f"Failed to update baseline with Wikipedia data for {entity_id}: {e}")
    
    logger.info(f"Fetched Wikipedia pageviews for {len(pageview_counts)} entities")
    return pageview_counts
