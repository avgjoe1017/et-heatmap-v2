"""
Weekly baseline fame update (Google Trends, Wikipedia pageviews).
"""

from datetime import datetime

def update_weekly_baseline(week_start: datetime = None) -> None:
    """
    Update entity_weekly_baseline table with Google Trends data.
    Runs weekly (typically Sunday).
    """
    # TODO: Implement
    # - Load pinned entities + active entities
    # - Query Google Trends via pytrends
    # - Optionally query Wikipedia pageviews
    # - Normalize to 0..100 scale
    # - Write to entity_weekly_baseline
    pass

if __name__ == "__main__":
    update_weekly_baseline()
