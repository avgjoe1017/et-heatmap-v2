"""
Time window utilities: 6AM PT → 6AM PT window logic, recency weighting.
"""

from datetime import datetime, timedelta
import pytz
import math

PACIFIC = pytz.timezone("America/Los_Angeles")

def get_daily_window(window_start: datetime = None) -> tuple:
    """
    Get daily window (6AM PT → 6AM PT).
    Returns (window_start, window_end).
    """
    # TODO: Implement
    # - If window_start provided, use it
    # - Else calculate latest 6AM PT boundary
    # - Return (window_start, window_end)
    pass

def recency_weight(timestamp: datetime, window_end: datetime, half_life_hours: float = 8.0) -> float:
    """
    Compute recency weight using exponential decay.
    Returns weight [0, 1].
    """
    # TODO: Implement
    # - Compute hours since timestamp
    # - Apply exponential decay with half_life_hours
    # - Return weight
    pass
