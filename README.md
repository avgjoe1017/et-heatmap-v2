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
# Install Python dependencies
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your database and API keys

# Run database migrations
python -m src.storage.migrate

# Run daily pipeline
python -m src.pipeline.daily_run

# Start API server
python -m src.app.main

# Start UI dev server
cd ui && npm install && npm run dev
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
- `pinned_entities.json` - Entities always tracked on the heatmap
- `sources.yaml` - Source ingestion toggles
- `weights.yaml` - Source weights and scoring parameters
- `subreddits.txt` - Reddit subreddit list
- `news_domains.txt` - News domain allowlist

## Documentation

- Product Specification: `psd.md`
- Build Journey: `docs/journey/JOURNEY.md`
# et-heatmap-v2
