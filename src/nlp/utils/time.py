"""
Time window utilities: 6AM PT  6AM PT window logic, recency weighting.
"""

from datetime import datetime, timedelta, timezone
import math
import pytz

from src.common.constants import DAILY_WINDOW_HOUR, DAILY_WINDOW_TIMEZONE, RECENCY_HALF_LIFE_HOURS

PACIFIC = pytz.timezone(DAILY_WINDOW_TIMEZONE)


def get_daily_window(window_start: datetime = None) -> tuple:
    """
    Get daily window (6AM PT  6AM PT).
    Returns (window_start, window_end).
    """
    if window_start is None:
        now_utc = datetime.now(timezone.utc)
        now_pt = now_utc.astimezone(PACIFIC)

        window_end = now_pt.replace(hour=DAILY_WINDOW_HOUR, minute=0, second=0, microsecond=0)
        if window_end > now_pt:
            window_end = window_end - timedelta(days=1)

        window_start = window_end - timedelta(days=1)
    else:
        if window_start.tzinfo is None:
            window_start = PACIFIC.localize(window_start)
        window_end = window_start + timedelta(days=1)

    window_start_utc = window_start.astimezone(pytz.UTC)
    window_end_utc = window_end.astimezone(pytz.UTC)

    return window_start_utc, window_end_utc


def recency_weight(
    timestamp: datetime,
    window_end: datetime,
    half_life_hours: float = RECENCY_HALF_LIFE_HOURS
) -> float:
    """
    Compute recency weight using exponential decay.
    Returns weight [0, 1].
    """
    if timestamp.tzinfo is None:
        timestamp = pytz.UTC.localize(timestamp)
    if window_end.tzinfo is None:
        window_end = pytz.UTC.localize(window_end)

    hours_since = max(0.0, (window_end - timestamp).total_seconds() / 3600.0)
    if half_life_hours <= 0:
        return 1.0

    decay = math.log(2.0) * (hours_since / half_life_hours)
    return math.exp(-decay)
