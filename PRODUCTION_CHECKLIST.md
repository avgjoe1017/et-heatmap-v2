# Production Readiness Checklist

## ✅ Completed (Phase 1 Core)

### Data Sources
- ✅ Reddit ingestion (with comments)
- ✅ ET YouTube ingestion (with analytics: views, likes, comments)
- ✅ GDELT News ingestion
- ✅ Google Trends baseline (weekly)
- ✅ Wikipedia pageviews baseline (weekly)

### Data Processing
- ✅ Document normalization
- ✅ Entity mention extraction (alias matching)
- ✅ Entity resolution (strict resolver rule)
- ✅ Sentiment scoring (ML with fallback)
- ✅ Engagement metrics integration (views, likes normalized across sources)
- ✅ Entity aggregation (with engagement weighting)
- ✅ Axes computation (fame/love with baseline)
- ✅ Baseline fame computation (Google Trends + Wikipedia + 90-day mentions)
- ✅ Drivers generation (with engagement-based impact scores)
- ✅ Themes generation (BERTopic/KeyBERT with fallback)
- ✅ Snapshot persistence
- ✅ Run metrics instrumentation

### API Layer
- ✅ FastAPI application
- ✅ Snapshot endpoint (`/api/snapshots`)
- ✅ Entity drilldown endpoint (`/api/entities/{entity_id}`)
- ✅ Resolve queue endpoint (`/api/resolve-queue`)
- ✅ Runs status endpoint (`/api/runs`)
- ✅ CORS middleware configured

### Frontend UI
- ✅ Heatmap visualization (scatter plot with color modes)
- ✅ Filters component (type, movers, polarizing, confidence)
- ✅ Drilldown panel (metrics, trends, narrative, drivers, themes)
- ✅ Timeline scrubber (basic implementation)
- ✅ Entity page (full drilldown view)
- ✅ API client integration

### Configuration & Setup
- ✅ Entity catalog (10 entities configured)
- ✅ Source configuration (YAML)
- ✅ Weight configuration (YAML)
- ✅ Database schema (SQLite/Postgres compatible)
- ✅ Database migrations
- ✅ Setup script

### Testing
- ✅ Integration tests (pytest)
- ✅ Test scripts for individual components
- ✅ YouTube ingestion test script
- ✅ Pipeline test script

## ⚠️ Before Production Deployment

### Configuration Required
- [ ] Set `YOUTUBE_API_KEY` in environment
- [ ] Set `YOUTUBE_CHANNEL_ID` (or configure in sources.yaml)
- [ ] Set Reddit credentials (`REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, etc.)
- [ ] Configure `DATABASE_URL` (Postgres for production)
- [ ] Review and adjust source weights in `config/weights.yaml`
- [ ] Review news domains allowlist in `config/news_domains.txt`
- [ ] Review pinned entities in `config/pinned_entities.json`

### Testing Needed
- [ ] Run full pipeline end-to-end test
- [ ] Verify YouTube API quota limits (10,000 units/day)
- [ ] Test API endpoints with real data
- [ ] Test frontend with real API data
- [ ] Load testing for API endpoints
- [ ] Verify database performance with production data volumes

### Deployment
- [ ] Set up cron job for daily pipeline (6AM PT)
- [ ] Set up cron job for weekly baseline (Sundays)
- [ ] Configure logging (structured logs, rotation)
- [ ] Set up monitoring/alerting (pipeline failures, API errors)
- [ ] Set up backup strategy for database
- [ ] Configure rate limiting for external APIs
- [ ] Set up error tracking (Sentry, etc.)

### Documentation
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] Performance tuning guide

### Optional Enhancements (Post-v1)
- [ ] Reply threads for YouTube comments (nested comments)
- [ ] Video duration/watch time metrics
- [ ] Engagement rate calculations (likes/views ratio)
- [ ] Channel subscriber count for baseline fame
- [ ] Historical window navigation API endpoint
- [ ] Loading skeletons/spinners in frontend
- [ ] Error boundaries in React components

## 🚀 Quick Start for Testing

```bash
# 1. Setup
python scripts/setup.py

# 2. Test YouTube ingestion
python scripts/test_youtube.py

# 3. Run full pipeline (test mode)
python scripts/test_pipeline.py

# 4. Start API server
python -m src.app.main

# 5. Start UI dev server (in separate terminal)
cd ui && npm install && npm run dev

# 6. Access UI at http://localhost:5173
```

## 📊 Key Metrics to Monitor

- **Pipeline**: Run duration, source items ingested, mentions extracted, entities resolved
- **API**: Response times, error rates, request volume
- **Database**: Query performance, connection pool usage, table sizes
- **External APIs**: Quota usage (YouTube, Google Trends), rate limit errors
- **Engagement**: Views, likes, comments normalized and weighted correctly
