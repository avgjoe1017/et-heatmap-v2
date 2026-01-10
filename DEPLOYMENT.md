# Deployment Guide

## Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] Database migrations run (`python scripts/setup.py`)
- [ ] Configuration validated (`python scripts/validate_config.py`)
- [ ] Entity catalog synced (`python scripts/setup.py`)
- [ ] Logs directory writable
- [ ] Required API keys configured (YouTube, Reddit)

## Production Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/et_heatmap

# API Keys
YOUTUBE_API_KEY=your_key_here
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# CORS (comma-separated)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Starting the Services

### API Server

```bash
# Direct execution
python scripts/run_api.py

# Or using entry point (after pip install -e .)
et-heatmap-api
```

### Pipeline (Cron Job)

Add to crontab for daily execution at 6:30 AM PT:

```bash
30 6 * * * cd /path/to/et-heatmap-v2 && /usr/bin/python3 scripts/run_pipeline.py >> logs/pipeline.log 2>&1
```

Or use systemd timer for more control.

### Weekly Baseline (Sunday 1 AM PT)

```bash
0 1 * * 0 cd /path/to/et-heatmap-v2 && /usr/bin/python3 -m src.pipeline.steps.compute_baseline_fame >> logs/baseline.log 2>&1
```

## Health Checks

The API provides health check endpoints:

- `GET /health` - Database connectivity and system status
- `GET /info` - API metadata and features

Monitor these endpoints for:
- Database connectivity issues
- Service availability
- Version information

## Logging

Logs are written to:
- File: `logs/app.log` (configurable via LOG_FILE)
- Console: stdout (for containerized deployments)

Log rotation:
- Max file size: 10MB
- Backups: 5 files
- Automatic cleanup

## Monitoring Recommendations

1. **Pipeline Runs**: Monitor run status in database (`runs` table)
2. **API Health**: Regular health check pings
3. **Log Aggregation**: Ship logs to centralized logging (ELK, Datadog, etc.)
4. **Error Tracking**: Integrate with error tracking service (Sentry, Rollbar)
5. **Metrics**: Track API response times, pipeline duration, error rates

## Database Backups

### SQLite
```bash
# Simple backup
cp data/et_heatmap.db data/et_heatmap.db.backup

# With timestamp
cp data/et_heatmap.db data/et_heatmap.db.$(date +%Y%m%d_%H%M%S)
```

### Postgres
```bash
# Using pg_dump
pg_dump -U user -d et_heatmap > backup_$(date +%Y%m%d).sql

# Restore
psql -U user -d et_heatmap < backup_20240109.sql
```

## Scaling Considerations

- **Database**: Postgres recommended for production (better concurrency)
- **API Server**: Use process manager (systemd, supervisor) or container orchestrator
- **Pipeline**: Run on separate worker node if resource-intensive
- **Caching**: Consider Redis for frequently accessed snapshots
- **CDN**: Serve frontend via CDN for better performance

## Troubleshooting

### Pipeline Fails
1. Check logs: `tail -f logs/app.log`
2. Verify API keys: `python scripts/validate_config.py`
3. Check database: `python -c "from src.storage.db import test_connection; print(test_connection())"`
4. Test individual steps: `python scripts/test_pipeline.py`

### API Returns 500 Errors
1. Check logs: `tail -f logs/app.log`
2. Enable debug mode: `DEBUG=true python scripts/run_api.py`
3. Verify database connectivity: `curl http://localhost:8000/health`

### Database Connection Issues
1. Verify DATABASE_URL format
2. Check network connectivity
3. Verify credentials
4. Check Postgres logs if using Postgres

## Security Considerations

- [ ] Use HTTPS in production
- [ ] Restrict CORS origins to known domains
- [ ] Store API keys securely (env vars, secret manager)
- [ ] Use database connection pooling
- [ ] Implement rate limiting (consider nginx, API gateway)
- [ ] Regular security updates for dependencies
- [ ] Monitor for suspicious activity in logs
