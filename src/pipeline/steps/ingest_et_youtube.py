"""
Ingest ET YouTube channel videos and transcripts.
"""

def ingest_et_youtube(window_start: datetime, window_end: datetime) -> List[dict]:
    """
    Fetch ET YouTube channel videos published in window.
    Extract transcripts using youtube-transcript-api.
    
    Returns list of source_items (raw).
    """
    # TODO: Implement
    # - Get ET YouTube channel ID from config
    # - Fetch videos via YouTube API (or yt-dlp)
    # - Extract transcripts via youtube-transcript-api
    # - Create source_items records
    # - Return list of items
    pass
