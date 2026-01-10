"""
Test script to run the full pipeline with all entities.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.daily_run import run_daily_pipeline
from src.catalog.catalog_loader import load_catalog
from src.storage.dao.snapshots import SnapshotDAO
from src.storage.dao.runs import RunDAO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_full_pipeline():
    """Run the full pipeline and verify results."""
    print("=" * 80)
    print("Testing Full Pipeline with All Entities")
    print("=" * 80)
    
    # Load catalog
    print("\n1. Loading entity catalog...")
    catalog = load_catalog()
    print(f"   [OK] Loaded {len(catalog)} entities")
    for entity in catalog[:5]:
        print(f"     - {entity['canonical_name']} ({entity['entity_type']})")
    if len(catalog) > 5:
        print(f"     ... and {len(catalog) - 5} more")
    
    # Set up test window (yesterday to today)
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=1)
    
    print(f"\n2. Running pipeline for window: {window_start.isoformat()} to {now.isoformat()}")
    
    try:
        # Run pipeline
        run_id = run_daily_pipeline(window_start)
        
        if not run_id:
            print("   [ERROR] Pipeline failed - no run_id returned")
            return False
        
        print(f"   [OK] Pipeline completed with run_id: {run_id}")
        
        # Verify run status
        print("\n3. Verifying run status...")
        with RunDAO() as run_dao:
            run = run_dao.get_run(run_id)
            if run:
                print(f"   [OK] Run status: {run['status']}")
                print(f"   [OK] Window: {run['window_start']} to {run['window_end']}")
            else:
                print("   [ERROR] Run not found in database")
                return False
        
        # Check entity metrics
        print("\n4. Checking entity metrics...")
        with SnapshotDAO() as snapshot_dao:
            metrics = snapshot_dao.get_entity_metrics_for_run(run_id)
            print(f"   [OK] Found metrics for {len(metrics)} entities")
            
            if metrics:
                print("\n   Sample metrics:")
                for m in metrics[:3]:
                    print(f"     - {m['entity_id']}: fame={m.get('fame', 0):.1f}, love={m.get('love', 50):.1f}, "
                          f"mentions={m.get('mentions_explicit', 0)}")
        
        # Check drivers
        print("\n5. Checking drivers...")
        with SnapshotDAO() as snapshot_dao:
            drivers_count = 0
            for entity in catalog[:3]:  # Check first 3 entities
                drivers = snapshot_dao.get_drivers_for_entity(run_id, entity["entity_id"])
                drivers_count += len(drivers)
            print(f"   [OK] Found {drivers_count} drivers")
        
        # Check themes
        print("\n6. Checking themes...")
        with SnapshotDAO() as snapshot_dao:
            themes_count = 0
            for entity in catalog[:3]:  # Check first 3 entities
                themes = snapshot_dao.get_themes_for_entity(run_id, entity["entity_id"])
                themes_count += len(themes)
            print(f"   [OK] Found {themes_count} themes")
        
        print("\n" + "=" * 80)
        print("Pipeline Test: SUCCESS [OK]")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n   ✗ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
