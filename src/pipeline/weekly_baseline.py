"""
Weekly baseline fame update job.
Should run weekly (e.g., Sunday night) to update baseline fame scores.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.steps.compute_baseline_fame import update_baseline_fame
from src.catalog.catalog_loader import load_catalog

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def run_weekly_baseline_update(week_start: datetime = None) -> None:
    """
    Run weekly baseline fame update for all entities.
    
    This should be scheduled to run weekly (e.g., Sunday 11pm PT).
    Updates baseline fame scores using:
    - Google Trends (weekly interest)
    - Wikipedia pageviews (lagged ~24h)
    - 90-day rolling mention volume
    """
    if week_start is None:
        # Default to start of current week
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    logger.info(f"Starting weekly baseline fame update for week starting {week_start.isoformat()}")
    
    # Load all entities
    catalog = load_catalog()
    logger.info(f"Loaded {len(catalog)} entities from catalog")
    
    if not catalog:
        logger.warning("No entities found in catalog, skipping baseline update")
        return
    
    # Update baseline fame for all entities
    try:
        update_baseline_fame(catalog, week_start)
        logger.info(f"Successfully updated baseline fame for {len(catalog)} entities")
    except Exception as e:
        logger.error(f"Failed to update baseline fame: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_weekly_baseline_update()
