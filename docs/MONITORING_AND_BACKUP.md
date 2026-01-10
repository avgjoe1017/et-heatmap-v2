# Monitoring and Backup Guide

This guide covers error monitoring, quota tracking, and database backup strategies for the ET Heatmap project.

---

## Table of Contents

1. [Error Monitoring with Sentry](#error-monitoring-with-sentry)
2. [YouTube API Quota Monitoring](#youtube-api-quota-monitoring)
3. [Database Backups](#database-backups)
4. [Production Checklist](#production-checklist)

---

## Error Monitoring with Sentry

### Overview

The application integrates with [Sentry](https://sentry.io) for error tracking and performance monitoring. Sentry automatically captures:

- **Errors and Exceptions**: Unhandled exceptions, logged errors
- **Breadcrumbs**: Info-level logs leading up to errors
- **Performance**: Transaction traces (configurable sampling)
- **Context**: Environment, release version, user context

### Setup

#### 1. Create Sentry Account

1. Sign up at https://sentry.io
2. Create a new project (select "Python")
3. Copy your DSN (Data Source Name)

#### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Required: Sentry DSN (from your Sentry project settings)
SENTRY_DSN=https://your-key@sentry.io/your-project-id

# Optional: Environment (defaults to "development")
SENTRY_ENVIRONMENT=production

# Optional: Release version (defaults to "et-heatmap@0.1.0")
SENTRY_RELEASE=et-heatmap@0.2.0

# Optional: Performance sampling rate (0.0 to 1.0, defaults to 0.1 = 10%)
SENTRY_TRACES_SAMPLE_RATE=0.1
```

#### 3. Verify Integration

Sentry is automatically initialized when `setup_logging()` is called. To test:

```python
from src.common.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

# This error will be sent to Sentry
logger.error("Test error for Sentry")

# Or trigger an exception
raise Exception("Test exception for Sentry")
```

### Configuration Options

#### Disable Sentry

To disable Sentry (e.g., in local development):

```python
from src.common.logging import setup_logging

# Disable Sentry
setup_logging(enable_sentry=False)
```

Or simply don't set `SENTRY_DSN` in your environment.

#### Sampling Rates

- **Error Sampling** (`sample_rate`): Set to 1.0 (100%) - all errors are sent
- **Performance Sampling** (`traces_sample_rate`): Set to 0.1 (10%) by default
  - In production with high traffic, reduce to 0.01 (1%) to minimize overhead

#### Custom Context

Add custom context to errors:

```python
import sentry_sdk

# Set user context
sentry_sdk.set_user({"id": "123", "email": "user@example.com"})

# Set custom tags
sentry_sdk.set_tag("pipeline_stage", "ingest")

# Add extra context
sentry_sdk.set_context("pipeline", {
    "run_id": "abc123",
    "window_start": "2024-01-01",
    "source": "youtube"
})
```

### Viewing Errors in Sentry

1. Log in to https://sentry.io
2. Navigate to your project
3. View **Issues** to see all errors
4. Click on an issue to see:
   - Stack trace
   - Breadcrumbs (logs leading to error)
   - Environment info
   - Frequency and affected users

### Alerts

Set up alerts in Sentry to notify you when errors occur:

1. Go to **Alerts** → **Create Alert**
2. Choose trigger (e.g., "Issue is first seen" or "Issue happens more than X times")
3. Set notification channel (email, Slack, PagerDuty, etc.)

---

## YouTube API Quota Monitoring

### Overview

YouTube Data API v3 has a default quota of **10,000 units per day**. Different operations cost different amounts:

| Operation | Cost (units) |
|-----------|--------------|
| search.list | 100 |
| videos.list | 1 |
| channels.list | 1 |
| playlistItems.list | 1 |
| commentThreads.list | 1 |

The quota tracker automatically monitors usage and warns when approaching limits.

### How It Works

The quota tracker:

1. **Tracks every API call** and logs usage in `data/youtube_quota.json`
2. **Warns at 80%** of daily quota (8,000 units)
3. **Errors at 100%** (10,000 units)
4. **Resets daily** at midnight UTC

### Automatic Tracking

Quota tracking is automatically integrated into the YouTube ingestion pipeline (`src/pipeline/steps/ingest_et_youtube.py`). No additional configuration needed.

### Viewing Quota Status

#### In Logs

The quota status is logged at the start of each YouTube ingestion:

```
2024-01-09 10:30:00 - src.pipeline.steps.ingest_et_youtube - INFO - YouTube API quota: 2500/10000 units (25.0%)
```

#### Programmatically

```python
from src.common.youtube_quota import get_quota_tracker

tracker = get_quota_tracker()
status = tracker.get_status()

print(f"Usage: {status['usage']}/{status['limit']} units")
print(f"Remaining: {status['remaining']} units")
print(f"Percentage: {status['percentage']:.1%}")
print(f"Warning: {status['is_warning']}")
print(f"Exceeded: {status['is_exceeded']}")
```

#### Quota File

View the quota file directly:

```bash
cat data/youtube_quota.json
```

Example output:

```json
{
  "date": "2024-01-09T10:30:00Z",
  "usage": 2500,
  "operations": [
    {
      "timestamp": "2024-01-09T10:25:00Z",
      "operation": "channel",
      "cost": 1,
      "count": 1,
      "total_cost": 1
    },
    {
      "timestamp": "2024-01-09T10:25:05Z",
      "operation": "playlist_items",
      "cost": 1,
      "count": 50,
      "total_cost": 50
    }
  ],
  "daily_limit": 10000
}
```

### Warning Levels

| Usage | Level | Action |
|-------|-------|--------|
| 0-79% | ✅ Normal | Continue normally |
| 80-99% | ⚠️ Warning | Logged as WARNING |
| 100%+ | 🚨 Exceeded | Logged as ERROR |

### Managing Quota

#### Check Before Large Operations

```python
from src.common.youtube_quota import get_quota_tracker

tracker = get_quota_tracker()

# Check if we can fetch 100 videos
if tracker.can_perform("video", count=100):
    print("✅ Sufficient quota")
else:
    print("❌ Insufficient quota")

# Get remaining budget
remaining_videos = tracker.get_remaining_budget("video")
print(f"Can fetch {remaining_videos} more videos today")
```

#### Manually Reset (Testing Only)

```python
from src.common.youtube_quota import get_quota_tracker

tracker = get_quota_tracker()
tracker.reset()  # Reset to 0 usage
```

### Optimization Strategies

If hitting quota limits:

1. **Reduce comment fetching**: Set `fetch_comments: false` in `config/sources.yaml`
2. **Limit comments per video**: Reduce `max_comments_per_video` (default: 50)
3. **Increase baseline interval**: Run baseline weekly instead of daily
4. **Request quota increase**: Apply at https://support.google.com/youtube/contact/yt_api_form

### Monitoring Quota in Production

**Option 1: Log Monitoring**

Set up log monitoring to alert on quota warnings:

```bash
# Example with grep
tail -f logs/app.log | grep "YouTube API quota warning"
```

**Option 2: Custom Alerts**

Add custom alerting to `src/common/youtube_quota.py`:

```python
if usage_percentage >= self.warning_threshold:
    # Send alert (email, Slack, etc.)
    send_alert(f"YouTube quota at {usage_percentage:.1%}")
```

**Option 3: Sentry Integration**

Quota warnings are automatically logged and sent to Sentry if configured.

---

## Database Backups

### Overview

Automated database backups with:

- **Compression**: gzip compression (optional)
- **Rotation**: Keep daily, weekly, and monthly backups
- **Support**: SQLite and PostgreSQL
- **Restoration**: Easy restore from any backup

### Backup Strategy

Default retention policy:

- **Daily backups**: Last 7 days
- **Weekly backups**: Last 4 weeks (one per week)
- **Monthly backups**: Last 12 months (one per month)

### Manual Backup

#### SQLite

```bash
python scripts/backup_database.py --action backup

# With custom settings
python scripts/backup_database.py \
  --action backup \
  --db-url "sqlite:///./data/et_heatmap.db" \
  --backup-dir backups \
  --keep-daily 14 \
  --keep-weekly 8 \
  --keep-monthly 24
```

#### PostgreSQL

```bash
# Requires pg_dump to be installed
python scripts/backup_database.py \
  --action backup \
  --db-url "postgresql://user:password@localhost:5432/et_heatmap"
```

### Automated Backups

#### Option 1: Cron (Linux/macOS)

Setup automated daily backups at 3 AM:

```bash
chmod +x scripts/setup_backup_cron.sh
./scripts/setup_backup_cron.sh
```

Manual cron setup:

```bash
# Edit crontab
crontab -e

# Add entry (daily at 3 AM)
0 3 * * * cd /path/to/et-heatmap-v2 && python scripts/backup_database.py --action backup >> logs/backup.log 2>&1
```

#### Option 2: systemd Timer (Linux)

Create `/etc/systemd/system/et-heatmap-backup.service`:

```ini
[Unit]
Description=ET Heatmap Database Backup

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/path/to/et-heatmap-v2
ExecStart=/usr/bin/python3 /path/to/et-heatmap-v2/scripts/backup_database.py --action backup
StandardOutput=append:/path/to/et-heatmap-v2/logs/backup.log
StandardError=append:/path/to/et-heatmap-v2/logs/backup.log
```

Create `/etc/systemd/system/et-heatmap-backup.timer`:

```ini
[Unit]
Description=ET Heatmap Database Backup Timer

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:

```bash
sudo systemctl enable et-heatmap-backup.timer
sudo systemctl start et-heatmap-backup.timer
```

#### Option 3: Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 3:00 AM
4. Action: Start a program
   - Program: `python`
   - Arguments: `scripts/backup_database.py --action backup`
   - Start in: `C:\path\to\et-heatmap-v2`

### Restore from Backup

#### SQLite

```bash
python scripts/backup_database.py \
  --action restore \
  --backup-file backups/et_heatmap_sqlite_20240109_030000.db.gz \
  --db-url "sqlite:///./data/et_heatmap.db"
```

#### PostgreSQL

```bash
# Requires pg_restore to be installed
python scripts/backup_database.py \
  --action restore \
  --backup-file backups/et_heatmap_postgres_20240109_030000.sql \
  --db-url "postgresql://user:password@localhost:5432/et_heatmap"
```

### Backup Rotation

Rotate backups manually (automatically done after each backup):

```bash
python scripts/backup_database.py --action rotate
```

### Backup Storage

#### Local Storage

Backups are stored in `backups/` directory by default.

#### Remote Storage (Recommended for Production)

**Option 1: AWS S3**

```bash
# After backup, sync to S3
python scripts/backup_database.py --action backup
aws s3 sync backups/ s3://your-bucket/et-heatmap-backups/
```

**Option 2: rsync to Remote Server**

```bash
# After backup, rsync to remote server
python scripts/backup_database.py --action backup
rsync -avz backups/ user@backup-server:/backups/et-heatmap/
```

**Option 3: Cloud Provider Backup**

- **AWS RDS**: Automated backups and snapshots
- **Google Cloud SQL**: Automated backups with point-in-time recovery
- **Azure Database**: Automated backups with geo-redundancy

### Backup Verification

Periodically test restores to ensure backups are valid:

```bash
# 1. Create test database
python scripts/backup_database.py \
  --action restore \
  --backup-file backups/et_heatmap_sqlite_20240109_030000.db.gz \
  --db-url "sqlite:///./data/et_heatmap_test.db"

# 2. Verify data integrity
python scripts/run_api.py  # Start API with test DB
# Run smoke tests

# 3. Clean up
rm data/et_heatmap_test.db
```

---

## Production Checklist

### Error Monitoring

- [ ] Sentry account created
- [ ] `SENTRY_DSN` configured in `.env`
- [ ] `SENTRY_ENVIRONMENT=production` set
- [ ] Sentry alerts configured (Slack, email, etc.)
- [ ] Test error sent to verify integration

### Quota Monitoring

- [ ] YouTube API key configured
- [ ] Quota tracker tested with initial run
- [ ] Log monitoring set up for quota warnings
- [ ] Alerting configured for quota exceeded
- [ ] Quota increase requested (if needed)

### Database Backups

- [ ] Backup script tested manually
- [ ] Automated backups configured (cron/systemd/Task Scheduler)
- [ ] Backup retention policy configured
- [ ] Remote backup storage configured (S3/rsync)
- [ ] Restore procedure tested
- [ ] Backup monitoring/alerts configured

### Logging

- [ ] `LOG_LEVEL=INFO` in production (DEBUG for troubleshooting)
- [ ] Log file rotation configured (RotatingFileHandler - 10MB, 5 backups)
- [ ] Structured logging considered (JSON format for log aggregation)
- [ ] Log aggregation service configured (optional: ELK, Datadog, CloudWatch)

### General Monitoring

- [ ] Health check endpoint monitored (`GET /health`)
- [ ] API response time monitoring
- [ ] Database size monitoring
- [ ] Disk space monitoring
- [ ] Pipeline run success/failure tracking (`GET /api/runs`)

---

## Environment Variables Summary

```bash
# Error Monitoring (Sentry)
SENTRY_DSN=https://your-key@sentry.io/your-project-id
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=et-heatmap@0.1.0
SENTRY_TRACES_SAMPLE_RATE=0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/et_heatmap

# YouTube API
YOUTUBE_API_KEY=your-api-key

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

---

## Support

For issues or questions:

- **GitHub Issues**: https://github.com/your-org/et-heatmap-v2/issues
- **Sentry Docs**: https://docs.sentry.io/platforms/python/
- **YouTube Quota**: https://developers.google.com/youtube/v3/getting-started#quota
