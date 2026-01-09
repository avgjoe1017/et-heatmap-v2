# ET Heatmap Quick Start Guide

## Prerequisites

- Python 3.10+
- Node.js 18+ (for UI)
- PostgreSQL or SQLite (SQLite for local development)

## Initial Setup

1. **Clone and install Python dependencies:**
   ```bash
   pip install -e .
   ```

2. **Set up environment variables:**
   ```bash
   # Create .env file (see .env.example for reference)
   # For SQLite (default):
   DATABASE_URL=sqlite:///./data/et_heatmap.db
   
   # For Postgres:
   DATABASE_URL=postgresql://user:password@localhost:5432/et_heatmap
   ```

3. **Run database migrations:**
   ```bash
   python scripts/setup.py
   ```
   
   This will:
   - Create database tables
   - Sync pinned entities from `config/pinned_entities.json`
   - Verify database connection

4. **Install UI dependencies:**
   ```bash
   cd ui
   npm install
   ```

## Running the Application

### Backend API

```bash
# Start FastAPI server (default port 8000)
python -m src.app.main

# Or with uvicorn directly:
uvicorn src.app.main:app --reload --port 8000
```

API will be available at:
- http://localhost:8000
- API docs: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

### Frontend UI

```bash
cd ui
npm run dev
```

UI will be available at:
- http://localhost:5173

## Testing the API

### Get Heatmap Snapshot

```bash
# Latest snapshot
curl http://localhost:8000/api/snapshots

# Specific window
curl "http://localhost:8000/api/snapshots?window_start=2024-12-01T00:00:00Z"
```

### Get Entity Drilldown

```bash
curl http://localhost:8000/api/entities/person_taylor_swift
```

### Get Resolve Queue

```bash
curl http://localhost:8000/api/resolve-queue
```

### Get Latest Run Status

```bash
curl http://localhost:8000/api/runs/latest
```

## Running the Pipeline

### Daily Pipeline

```bash
# Run daily pipeline (6AM PT → 6AM PT window)
python -m src.pipeline.daily_run
```

### Weekly Baseline Update

```bash
# Update weekly baseline fame (Google Trends)
python -m src.pipeline.weekly_baseline
```

## Database Management

### Migrate Database

```bash
# Run migrations manually
python scripts/migrate_db.py

# With custom database URL
python scripts/migrate_db.py --url sqlite:///./data/custom.db
```

### Sync Pinned Entities

```bash
# Sync pinned entities from config to database
python -m src.catalog.catalog_loader
```

## Development Workflow

1. **Make code changes**
2. **Test database operations:**
   ```bash
   python -m src.storage.db  # Test database connection
   ```

3. **Test catalog loading:**
   ```bash
   python -m src.catalog.catalog_loader
   ```

4. **Run pipeline (when steps are implemented):**
   ```bash
   python -m src.pipeline.daily_run
   ```

5. **Start API server:**
   ```bash
   python -m src.app.main
   ```

6. **Test API endpoints:**
   - Use curl or Postman
   - Or visit http://localhost:8000/docs for interactive API docs

## Troubleshooting

### Database Connection Issues

- Check `DATABASE_URL` in `.env` file
- Ensure database exists (Postgres) or data directory exists (SQLite)
- Run `python scripts/setup.py` to initialize database

### Import Errors

- Ensure you've run `pip install -e .` in the project root
- Check that Python path includes `src/` directory
- Verify all dependencies are installed: `pip list`

### API Not Starting

- Check if port 8000 is already in use
- Verify FastAPI and uvicorn are installed
- Check logs for error messages

### Empty Results

- Database might be empty (no pipeline runs yet)
- Verify pinned entities are synced: `python -m src.catalog.catalog_loader`
- Check that pipeline has been run at least once

## Next Steps

1. **Implement first ingestion step:**
   - Start with Reddit (easiest with PRAW)
   - Or ET YouTube transcripts

2. **Run full pipeline:**
   - Ingest sources
   - Normalize documents
   - Extract and resolve mentions
   - Score sentiment
   - Generate snapshots

3. **Test end-to-end:**
   - Run pipeline
   - Check API endpoints return data
   - View results in UI

4. **Add more sources:**
   - GDELT news
   - Wikipedia pageviews
   - Google Trends
