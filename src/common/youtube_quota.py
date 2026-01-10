"""
YouTube API Quota Monitoring and Management.

YouTube Data API v3 has a default quota of 10,000 units per day.
Different API operations cost different amounts of units:

- search.list: 100 units
- videos.list: 1 unit
- channels.list: 1 unit
- playlistItems.list: 1 unit
- commentThreads.list: 1 unit
- comments.list: 1 unit

This module tracks quota usage and alerts when approaching limits.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class YouTubeQuotaTracker:
    """Track YouTube API quota usage to prevent hitting daily limits."""

    # YouTube API quota costs (in units)
    QUOTA_COSTS = {
        "search": 100,
        "video": 1,
        "channel": 1,
        "playlist_items": 1,
        "comment_threads": 1,
        "comments": 1,
    }

    def __init__(
        self,
        quota_file: str = "data/youtube_quota.json",
        daily_limit: int = 10000,
        warning_threshold: float = 0.8,  # 80%
    ):
        """
        Initialize quota tracker.

        Args:
            quota_file: Path to store quota usage data
            daily_limit: Daily quota limit (default: 10,000)
            warning_threshold: Warn when usage exceeds this percentage (default: 0.8 = 80%)
        """
        self.quota_file = Path(quota_file)
        self.quota_file.parent.mkdir(parents=True, exist_ok=True)

        self.daily_limit = daily_limit
        self.warning_threshold = warning_threshold

        self._load_quota_data()

    def _load_quota_data(self):
        """Load quota usage data from file."""
        if self.quota_file.exists():
            try:
                with open(self.quota_file, "r") as f:
                    data = json.load(f)

                # Check if data is from today
                last_date = datetime.fromisoformat(data.get("date", ""))
                if last_date.date() == datetime.now(timezone.utc).date():
                    self.usage = data.get("usage", 0)
                    self.operations = data.get("operations", [])
                    return
            except Exception as e:
                logger.warning(f"Failed to load quota data: {e}")

        # Initialize fresh quota data
        self.usage = 0
        self.operations = []

    def _save_quota_data(self):
        """Save quota usage data to file."""
        try:
            data = {
                "date": datetime.now(timezone.utc).isoformat(),
                "usage": self.usage,
                "operations": self.operations,
                "daily_limit": self.daily_limit,
            }

            with open(self.quota_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save quota data: {e}")

    def add_usage(self, operation: str, cost: Optional[int] = None, count: int = 1):
        """
        Record API operation usage.

        Args:
            operation: Operation type (search, video, channel, playlist_items, etc.)
            cost: Custom cost (if None, uses default from QUOTA_COSTS)
            count: Number of operations (default: 1)
        """
        if cost is None:
            cost = self.QUOTA_COSTS.get(operation, 1)

        total_cost = cost * count
        self.usage += total_cost

        # Record operation
        self.operations.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": operation,
                "cost": cost,
                "count": count,
                "total_cost": total_cost,
            }
        )

        # Save to file
        self._save_quota_data()

        # Check if approaching limit
        usage_percentage = self.usage / self.daily_limit
        remaining = self.daily_limit - self.usage

        if usage_percentage >= 1.0:
            logger.error(
                f"🚨 YouTube API quota EXCEEDED! Used {self.usage}/{self.daily_limit} units ({usage_percentage:.1%})"
            )
        elif usage_percentage >= self.warning_threshold:
            logger.warning(
                f"⚠️ YouTube API quota warning: {self.usage}/{self.daily_limit} units used ({usage_percentage:.1%}). "
                f"{remaining} units remaining."
            )
        else:
            logger.debug(
                f"YouTube API quota: {self.usage}/{self.daily_limit} units ({usage_percentage:.1%})"
            )

        return {
            "usage": self.usage,
            "limit": self.daily_limit,
            "remaining": remaining,
            "percentage": usage_percentage,
        }

    def can_perform(self, operation: str, count: int = 1) -> bool:
        """
        Check if operation can be performed without exceeding quota.

        Args:
            operation: Operation type
            count: Number of operations

        Returns:
            True if operation can be performed, False otherwise
        """
        cost = self.QUOTA_COSTS.get(operation, 1) * count
        return (self.usage + cost) <= self.daily_limit

    def get_status(self) -> Dict[str, Any]:
        """Get current quota status."""
        usage_percentage = self.usage / self.daily_limit
        remaining = self.daily_limit - self.usage

        return {
            "usage": self.usage,
            "limit": self.daily_limit,
            "remaining": remaining,
            "percentage": usage_percentage,
            "is_warning": usage_percentage >= self.warning_threshold,
            "is_exceeded": usage_percentage >= 1.0,
            "operations_count": len(self.operations),
        }

    def get_remaining_budget(self, operation: str) -> int:
        """
        Get number of operations that can still be performed.

        Args:
            operation: Operation type

        Returns:
            Number of operations possible with remaining quota
        """
        cost = self.QUOTA_COSTS.get(operation, 1)
        remaining = self.daily_limit - self.usage
        return max(0, remaining // cost)

    def reset(self):
        """Manually reset quota (for testing or new day)."""
        self.usage = 0
        self.operations = []
        self._save_quota_data()
        logger.info("YouTube API quota reset")


# Global singleton instance
_quota_tracker: Optional[YouTubeQuotaTracker] = None


def get_quota_tracker() -> YouTubeQuotaTracker:
    """Get global quota tracker instance."""
    global _quota_tracker
    if _quota_tracker is None:
        _quota_tracker = YouTubeQuotaTracker()
    return _quota_tracker


def track_youtube_api_call(operation: str, count: int = 1) -> Dict[str, Any]:
    """
    Convenience function to track YouTube API call.

    Args:
        operation: Operation type (search, video, channel, etc.)
        count: Number of operations

    Returns:
        Quota status dict
    """
    tracker = get_quota_tracker()
    return tracker.add_usage(operation, count=count)
