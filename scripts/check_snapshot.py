"""Quick script to check snapshot data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.db import get_session
from src.storage.dao.snapshots import SnapshotDAO
from src.storage.dao.runs import RunDAO

with RunDAO() as run_dao:
    # Get all runs to see what we have
    all_runs = run_dao.list_runs(limit=10)
    print(f"Total runs found: {len(all_runs)}")
    for run in all_runs[:5]:
        print(f"  - {run['run_id']}: {run.get('status')} at {run.get('started_at')}")
    
    latest = run_dao.get_latest_run()
    if not latest:
        print("\nNo runs found")
        sys.exit(1)
    
    print(f"\nLatest run ID: {latest['run_id']}")
    print(f"Status: {latest.get('status')}")
    print(f"Window: {latest.get('window_start')} to {latest.get('window_end')}")

with SnapshotDAO() as snapshot_dao:
    metrics = snapshot_dao.get_entity_metrics_for_run(latest['run_id'])
    print(f"\nMetrics found: {len(metrics)}")
    for m in metrics[:5]:
        print(f"  - {m['entity_id']}: fame={m.get('fame', 0):.2f}, love={m.get('love', 50):.2f}")

# Check the old successful run
old_success_id = "99665496-36a6-49ec-bbc3-6ce3b0700a36"
with RunDAO() as run_dao:
    old_success = run_dao.get_run(old_success_id)
    if old_success:
        print(f"\nChecking old successful run {old_success_id}:")
        with SnapshotDAO() as snapshot_dao:
            metrics = snapshot_dao.get_entity_metrics_for_run(old_success_id)
            print(f"  Metrics: {len(metrics)}")
            if metrics:
                for m in metrics[:3]:
                    print(f"    - {m['entity_id']}: fame={m.get('fame', 0):.2f}, love={m.get('love', 50):.2f}")

from src.app.service.snapshot_service import build_snapshot
snapshot = build_snapshot()
print(f"\nSnapshot points: {len(snapshot.get('points', []))}")
if snapshot.get('points'):
    for p in snapshot['points'][:3]:
        print(f"  - {p['name']}: fame={p['x_fame']:.2f}, love={p['y_love']:.2f}")
else:
    print("  (No points - check if latest run has metrics)")
