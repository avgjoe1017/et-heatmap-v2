# Entertainment Feelings Heatmap

A daily-updated scatter-plot heatmap that places **people, shows, films, franchises, brands, characters, streamers/networks, and couples** on:

- **X-axis:** Fame (baseline + today's attention)
- **Y-axis:** Love (hate → indifference → love)
- **Color (default):** Momentum (how fast the dot is moving recently), with toggles for **Polarization** and **Confidence**

## Architecture

### Backend (Python)
- FastAPI application serving heatmap data and entity drilldowns
- Daily pipeline orchestration for 6AM PT → 6AM PT windows
- NLP processing for entity extraction, sentiment analysis, and theme clustering
- Postgres/SQLite database for entity catalog, documents, mentions, and metrics

### Frontend (React/TypeScript)
- Interactive scatter plot heatmap visualization
- Entity drilldown panels
- Resolve queue management interface
- Timeline scrubbing and trail visualization

## Quick Start

```bash
# 1. Install Python dependencies
pip install -e .

# 2. Set up environment variables
# Create .env file with:
#   - DATABASE_URL (defaults to SQLite: sqlite:///./data/et_heatmap.db)
#   - YOUTUBE_API_KEY (required for YouTube ingestion)
#   - REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET (required for Reddit ingestion)
#   - REDDIT_USERNAME, REDDIT_PASSWORD (optional, for authenticated access)
#   - LOG_LEVEL (optional, defaults to INFO)
#   - LOG_FILE (optional, defaults to logs/app.log, set to "none" to disable)

# 3. Validate configuration
python scripts/validate_config.py

# 4. Initialize database and load entities
python scripts/setup.py

# 5. Test individual components (optional)
python scripts/test_youtube.py  # Test YouTube ingestion
python scripts/test_pipeline.py  # Test full pipeline

# 6. Run daily pipeline
python scripts/run_pipeline.py
# Or with custom window: python scripts/run_pipeline.py 2024-01-01T00:00:00Z

# 7. Start API server
python scripts/run_api.py
# API will be available at http://localhost:8000
# API Documentation: http://localhost:8000/docs
# Health Check: http://localhost:8000/health

# 8. Start UI dev server (in separate terminal)
cd ui && npm install && npm run dev
# UI will be available at http://localhost:5173
```

## Project Structure

```
et-heatmap/
  config/          # Configuration files (pinned entities, source weights, etc.)
  schemas/         # JSON schemas for API contracts
  src/
    app/           # FastAPI application
    pipeline/      # Daily/weekly pipeline orchestration
    nlp/           # Sentiment analysis, entity extraction, themes
    catalog/       # Entity catalog management
    storage/       # Database access layer
    common/        # Shared types and utilities
  ui/              # React frontend application
```

## Configuration

See `config/` for:
- `pinned_entities.json` - Entities always tracked on the heatmap (10 entities pre-configured)
- `sources.yaml` - Source ingestion toggles (Reddit, YouTube, GDELT enabled by default)
- `weights.yaml` - Source weights and scoring parameters (fame/love weights, engagement normalization)
- `subreddits.txt` - Reddit subreddit list
- `news_domains.txt` - News domain allowlist (Entertainment news sites)

### Key Features

- **Multi-source ingestion**: Reddit (posts + comments), YouTube (videos + comments), GDELT News
- **Analytics capture**: Views, likes, comments with cross-source normalization
- **ML-powered**: Sentiment analysis (transformers), theme clustering (BERTopic), entity resolution
- **Graceful degradation**: Works without ML dependencies, falls back to simpler methods
- **Real-time APIs**: Google Trends, Wikipedia pageviews for baseline fame computation

## Documentation

- Product Specification: `psd.md`
- Build Journey: `docs/journey/JOURNEY.md`
# et-heatmap-v2
