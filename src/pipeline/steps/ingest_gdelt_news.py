"""
Ingest news articles from GDELT.
"""

def ingest_gdelt_news(window_start: datetime, window_end: datetime) -> List[dict]:
    """
    Fetch news articles from GDELT API for entertainment-related queries.
    Filters by news_domains.txt allowlist.
    
    Returns list of source_items (raw).
    """
    # TODO: Implement
    # - Query GDELT API for entertainment keywords
    # - Filter by news_domains.txt
    # - Extract article text via trafilatura
    # - Create source_items records
    # - Return list of items
    pass
