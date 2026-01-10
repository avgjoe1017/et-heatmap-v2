"""Check if successful run exists in runs table."""
import sqlite3

conn = sqlite3.connect('data/et_heatmap.db')
cursor = conn.cursor()

# Check if the successful run exists
run_id = "79d959f0-53f9-47fb-bb32-cec00af45763"
cursor.execute("SELECT run_id, status, started_at FROM runs WHERE run_id = ?", (run_id,))
row = cursor.fetchone()

if row:
    print(f"OK Run {run_id} found in runs table")
    print(f"  Status: {row[1]}")
    print(f"  Started: {row[2]}")
else:
    print(f"X Run {run_id} NOT found in runs table")
    print("  (Metrics exist but run record doesn't)")

# Check metrics
cursor.execute("SELECT COUNT(*) FROM entity_daily_metrics WHERE run_id = ?", (run_id,))
count = cursor.fetchone()[0]
print(f"\nMetrics for this run: {count}")

# Get latest run
cursor.execute("SELECT run_id, status, started_at FROM runs ORDER BY started_at DESC LIMIT 1")
latest = cursor.fetchone()
if latest:
    print(f"\nLatest run by started_at: {latest[0]}")
    print(f"  Status: {latest[1]}")
    print(f"  Started: {latest[2]}")

conn.close()
