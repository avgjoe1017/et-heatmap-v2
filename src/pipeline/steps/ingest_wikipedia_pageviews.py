"""
Ingest Wikipedia pageviews (optional baseline confirmation).
"""

def ingest_wikipedia_pageviews(week_start: datetime) -> dict:
    """
    Fetch Wikipedia pageviews for entities (lagged baseline).
    Updates entity_weekly_baseline table.
    
    Returns dict of entity_id -> pageview count.
    """
    # TODO: Implement
    # - Load entities with Wikidata IDs
    # - Query Wikimedia Pageviews API
    # - Normalize to 0..100 scale
    # - Update entity_weekly_baseline
    # - Return summary dict
    pass
