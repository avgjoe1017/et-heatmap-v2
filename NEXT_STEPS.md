# Next Steps - ET Heatmap v2

## ✅ Completed (Phase 1 Core)

### Backend Pipeline
- ✅ Reddit ingestion (PRAW)
- ✅ Document normalization and deduplication
- ✅ Mention extraction + resolution
- ✅ Sentiment scoring (ML with fallback)
- ✅ Entity aggregation + axes computation
- ✅ Baseline fame (Google Trends + Wikipedia + 90-day mentions)
- ✅ Drivers + themes generation
- ✅ Snapshot persistence
- ✅ Run metrics

### API Layer
- ✅ FastAPI application
- ✅ Snapshot endpoint (`/api/snapshots`)
- ✅ Entity drilldown endpoint (`/api/entities/{entity_id}`)
- ✅ Resolve queue endpoint (`/api/resolve-queue`)
- ✅ Runs status endpoint (`/api/runs`)

### Frontend UI
- ✅ Heatmap visualization
- ✅ Filters + drilldown panels
- ✅ Timeline navigation
- ✅ Resolve queue UI

---

## 🔥 Next Priority: Data Quality & Enrichment (Phase 1.1)

The core UI and API are in place. The next wins are data quality, enrichment, and signal tuning.

### High Priority
1. **Targeted Sentiment** (`src/nlp/sentiment/target_sentiment.py`)
   - Implement entity-targeted sentiment with `cardiffnlp/twitter-roberta-base-topic-sentiment-latest`.
   - Use when generic sentiment is misleading.

2. **Entity Enrichment** (`src/catalog/wikidata_enrich.py`, `src/catalog/imdb_tmdb_enrich.py`)
   - Pull aliases, genres, and network metadata to improve filters and disambiguation.
   - Store enriched fields in `entities.metadata`.

3. **Momentum Calculation** (`src/pipeline/steps/compute_axes.py`)
   - Replace placeholder momentum with 7-day deltas/EMA once enough history exists.

4. **Resolve Queue UX** (`ui/src/pages/ResolveQueuePage.tsx`)
   - Add sorting by impact, pagination, and quick-add alias actions.
   - Wire to `POST /api/resolve-queue/resolve`.

### Medium Priority
5. **Entity Discovery**
   - Promote high-confidence unresolved surfaces into new entities.
   - Auto-generate aliases via `src/catalog/alias_tools.py`.

6. **Snapshot Metadata**
   - Standardize `tags`, `parent_ids`, and `child_ids` for UI filters and trails.
   - Add tags to `entities.metadata` for consistent display.

---

## 🚀 Immediate Next Steps (Recommended Order)

1. **Implement targeted sentiment**
2. **Enrich entities from Wikidata/IMDb**
3. **Compute momentum from history** (needs 7+ days of data)
4. **Upgrade resolve queue UX**

---

## ⚡ Quick Wins

- Add pagination + sort order to resolve queue API response
- Add entity search endpoint for UI autocomplete
- Generate a small sample dataset for UI smoke tests

---

## 📝 Notes

- UI and API are in place; quality improvements are mostly data and ML tuning.
- ML features are optional and should fail gracefully without heavy dependencies.
- Momentum still needs historical data to be meaningful.
