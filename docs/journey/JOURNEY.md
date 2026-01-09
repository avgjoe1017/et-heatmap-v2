# Build Journey

A running log of what we built, why we built it, and what we learned—written so it can later become a narrative.

## Index (optional)
- Add links here if the file gets long.

---

## 2024-12-XX (Day 1) — Repository Structure and Schema Setup

**Time:** HH:MM (local)  
**Context:** Initial setup of the Entertainment Feelings Heatmap project based on product specification document (psd.md).  
**Objective:** Create a complete, repo-ready folder structure with database schemas, API contracts, configuration files, and placeholder code modules following the blueprint specification.

**What changed**
- Created complete folder structure (`config/`, `schemas/`, `src/`, `ui/`, `scripts/`)
- Created database schema file (`schemas/db.schema.sql`) with Postgres-compatible SQL and SQLite migration notes
- Created JSON API schemas (`schemas/api.*.schema.json`) for snapshot, drilldown, and resolve queue responses
- Created configuration files (`config/pinned_entities.json`, `config/sources.yaml`, `config/weights.yaml`, etc.)
- Created root project files (`README.md`, `pyproject.toml`)
- Created placeholder Python modules for pipeline, NLP, catalog, storage, and API layers
- Created React/TypeScript UI structure with components, pages, and API client
- Created database migration script (`scripts/migrate_db.py`)

**Decisions**
- Decision: Use Postgres as primary database with SQLite migration path
  - Why: Postgres supports JSONB natively for flexible metadata storage; SQLite option provides easy local development
  - Alternatives: Considered DuckDB for analytics, but Postgres provides better transaction support for catalog edits
- Decision: FastAPI for backend API
  - Why: Modern async Python framework with automatic OpenAPI docs, type hints support
  - Alternatives: Flask, Django REST Framework
- Decision: React + TypeScript + Vite for frontend
  - Why: Modern React development experience, type safety, fast dev server
  - Alternatives: Vue, Svelte, vanilla JS
- Decision: Separate pipeline steps into individual modules
  - Why: Better testability, clearer separation of concerns, easier to parallelize later
  - Alternatives: Single monolithic pipeline script

**Gotchas / Debugging notes (if any)**
- Note: Existing `src/resolution/entity_resolver.py` exists but is not yet integrated into the new structure
  - Action needed: Integrate existing resolver logic into `src/pipeline/steps/entity_resolver.py`
- Note: `.env.example` file was blocked by globalignore
  - Action needed: Create manually or adjust ignore rules

**Verification**
- Folder structure matches blueprint specification
- All required files created with appropriate placeholders
- Database schema includes all tables from specification
- JSON schemas validate structure matches API contract requirements

**Next steps**
- [x] Integrate existing `src/resolution/entity_resolver.py` into new pipeline structure
- [x] Implement database migration script execution
- [ ] Set up Python virtual environment and install dependencies
- [ ] Set up Node.js dependencies for UI
- [ ] Implement first pipeline step (ingest ET YouTube)
- [x] Create database connection and DAO implementations
- [ ] Implement FastAPI route handlers

---

## 2024-12-XX (Day 1, continued) — Core Infrastructure Implementation

**Time:** HH:MM (local)  
**Context:** Implementing core database and pipeline infrastructure after initial structure setup.  
**Objective:** Get database layer, entity resolver integration, and basic pipeline orchestration working.

**What changed**
- Improved database migration script (`scripts/migrate_db.py`) with better SQLite support and error handling
- Created database connection module (`src/storage/db.py`) with session management
- Implemented base DAO class (`src/storage/dao/base.py`) with common database operations
- Implemented EntityDAO (`src/storage/dao/entities.py`) with CRUD operations and JSON field handling
- Implemented RunDAO (`src/storage/dao/runs.py`) for pipeline run tracking
- Implemented SourceItemDAO (`src/storage/dao/source_items.py`) for source item storage
- Integrated existing entity resolver (`src/pipeline/steps/entity_resolver.py`) with wrapper functions
- Implemented catalog loader (`src/catalog/catalog_loader.py`) to load pinned + discovered entities
- Created pipeline orchestrator skeleton (`src/pipeline/daily_run.py`) with 10-stage structure
- Updated FastAPI main app (`src/app/main.py`) to register all routes
- Created setup script (`scripts/setup.py`) for one-command initialization

**Decisions**
- Decision: Use context managers for DAO sessions
  - Why: Ensures proper session cleanup and transaction management, prevents connection leaks
  - Alternatives: Manual session management, dependency injection (FastAPI style)
- Decision: Handle JSON fields as strings in SQLite, native JSONB in Postgres
  - Why: Allows same code to work with both databases, with automatic serialization layer
  - Alternatives: Separate implementations per database type
- Decision: Integrate existing resolver via wrapper functions rather than refactoring immediately
  - Why: Preserves working code while allowing gradual migration to new structure
  - Alternatives: Complete rewrite, direct import without wrapper

**Gotchas / Debugging notes (if any)**
- Issue: SQLite doesn't support TIMESTAMPTZ, need string serialization
  - Fix: Convert datetime objects to ISO format strings in DAO layer
  - Prevention: Database abstraction layer handles this automatically
- Issue: JSONB fields need special handling in SQLite
  - Fix: Store as TEXT with JSON.dumps()/loads() conversion in DAO layer
  - Prevention: BaseDAO methods handle serialization transparently

**Verification**
- Database migration script runs successfully on SQLite
- DAO classes can create and query entities
- Catalog loader successfully loads pinned entities from config
- Pipeline orchestrator structure compiles without errors
- FastAPI app starts and registers routes

**Next steps**
- [x] Implement remaining DAO classes (documents, mentions, snapshots)
- [x] Implement FastAPI route handlers with actual database queries
- [ ] Implement first ingestion step (ET YouTube or Reddit)
- [ ] Add unit tests for DAO classes
- [ ] Set up logging configuration
- [ ] Create development environment setup guide

---

## 2024-12-XX (Day 1, continued) — DAO and API Implementation

**Time:** HH:MM (local)  
**Context:** Implementing remaining DAO classes and API route handlers with database queries.  
**Objective:** Complete data access layer and API endpoints for heatmap snapshots, entity drilldowns, resolve queue, and run status.

**What changed**
- Implemented DocumentDAO (`src/storage/dao/documents.py`) with document CRUD operations
- Implemented MentionDAO (`src/storage/dao/mentions.py`) with mention queries and aggregation
- Implemented SnapshotDAO (`src/storage/dao/snapshots.py`) for entity_daily_metrics, drivers, and themes
- Implemented UnresolvedDAO (`src/storage/dao/unresolved.py`) for resolve queue management
- Implemented snapshot service (`src/app/service/snapshot_service.py`) to build heatmap snapshots
- Implemented entity service (`src/app/service/entity_service.py`) for entity drilldowns with historical data
- Implemented resolve queue service (`src/app/service/resolve_queue_service.py`) for unresolved mentions
- Implemented run service (`src/app/service/run_service.py`) for pipeline run tracking
- Implemented all API route handlers with proper error handling and validation
- Fixed import issues and JSON serialization for SQLite/Postgres compatibility

**Decisions**
- Decision: Use context managers for all DAO operations
  - Why: Ensures proper session cleanup, prevents connection leaks, makes error handling cleaner
  - Alternatives: Dependency injection via FastAPI, manual session management
- Decision: Handle JSON fields as strings in DAO layer
  - Why: SQLite doesn't support JSONB, so serialize/deserialize in DAO for database-agnostic code
  - Alternatives: Separate implementations per database type, use ORM with native JSON support
- Decision: Return empty structures rather than errors when no data exists
  - Why: Better UX for frontend, allows graceful handling of missing data
  - Alternatives: Return 404 errors, return null values

**Gotchas / Debugging notes (if any)**
- Issue: JSON field serialization differs between SQLite and Postgres
  - Fix: Always use json.dumps()/loads() in DAO layer, never assume native JSON support
  - Prevention: BaseDAO helper methods handle this transparently
- Issue: Datetime serialization for SQLite (stores as TEXT)
  - Fix: Convert datetime to ISO format strings in DAO layer
  - Prevention: Helper functions in DAO layer handle conversion automatically
- Issue: Missing import in resolve_queue_service
  - Fix: Added json import at top of file
  - Prevention: Use linter to catch missing imports

**Verification**
- All DAO classes compile without errors
- API route handlers import successfully
- Service layer functions return proper data structures
- Error handling works for missing data cases
- JSON serialization works for both SQLite and Postgres

**Next steps**
- [x] Implement first ingestion step (ET YouTube or Reddit) to get data flowing
- [ ] Add integration tests for API endpoints
- [ ] Add unit tests for DAO classes
- [x] Implement pipeline steps to populate database
- [ ] Test end-to-end flow: ingest → normalize → resolve → score → snapshot

---

## 2024-12-XX (Day 1, continued) — Pipeline Steps Implementation

**Time:** HH:MM (local)  
**Context:** Implementing first ingestion and processing steps to get data flowing through the pipeline.  
**Objective:** Get Reddit ingestion, document normalization, and mention extraction working end-to-end.

**What changed**
- Created configuration loader (`src/common/config.py`) for YAML config and environment variables
- Implemented Reddit ingestion (`src/pipeline/steps/ingest_reddit.py`) with PRAW integration
- Implemented document normalization (`src/pipeline/steps/normalize_docs.py`) with text cleaning
- Enhanced text utilities (`src/nlp/utils/text.py`) with cleaning, sentence splitting, language detection
- Implemented basic mention extraction (`src/pipeline/steps/extract_mentions.py`) with alias matching
- Updated pipeline orchestrator (`src/pipeline/daily_run.py`) to wire implemented steps together
- Added database storage for source_items and documents as they're ingested

**Decisions**
- Decision: Use simple alias matching for v1 mention extraction (no spaCy NER yet)
  - Why: Faster to ship, spaCy requires model downloads and more setup
  - Alternatives: spaCy NER, flashText for faster alias matching, pyahocorasick for multi-pattern matching
- Decision: Store source_items and documents immediately after ingestion/normalization
  - Why: Allows pipeline to be interrupted and resumed, enables debugging individual steps
  - Alternatives: Batch insert at end, in-memory only until final step
- Decision: Simple word-boundary alias matching for v1
  - Why: Fast, works for most cases, avoids false positives from substring matches
  - Alternatives: Fuzzy matching, tokenization-based matching, ML-based extraction

**Gotchas / Debugging notes (if any)**
- Issue: Reddit API requires proper user_agent string
  - Fix: Use descriptive user_agent format "et-heatmap/0.1.0" with contact info
  - Prevention: Document in README that Reddit credentials are required
- Issue: Text normalization needs to handle Reddit markdown and special characters
  - Fix: Enhanced clean_text() to handle unicode quotes, control characters
  - Prevention: Test with real Reddit data early
- Issue: Datetime handling between Reddit timestamps (Unix) and database (ISO strings)
  - Fix: Convert Unix timestamps to datetime objects, then serialize for database
  - Prevention: Centralize datetime conversion in utility functions

**Verification**
- Reddit ingestion loads subreddits from config file
- Documents are normalized and stored with proper text fields
- Mention extraction finds aliases in text
- Pipeline orchestrator calls all steps in correct order
- Source items and documents are stored in database

**Next steps**
- [ ] Implement sentiment scoring step
- [ ] Implement entity aggregation step
- [ ] Implement axes computation (fame/love)
- [ ] Test end-to-end pipeline with real Reddit data
- [ ] Add error handling for API rate limits
- [ ] Implement deduplication step to prevent duplicate documents

**Narrative nugget**
Setting up the repository structure felt like laying the foundation for a complex machine. The product spec was comprehensive but theoretical—translating it into an actual folder structure with real files made the scope tangible. The decision to use placeholder modules with TODO comments rather than empty files was deliberate: it creates a clear roadmap for implementation while keeping the structure immediately understandable. The tension between wanting to implement everything now versus shipping v1 quickly is already present, but the phased approach in the spec (Phase 1 core, Phase 2 edge, Phase 3 expansion) provides a clear prioritization framework.

---

### 2026-01-08 (Wednesday) — Pipeline Completion: Sentiment, Aggregation, and Axes

**Time:** 22:45 (local)  
**Context:** After implementing Reddit ingestion, normalization, and mention extraction, the pipeline needed sentiment scoring, entity aggregation, and fame/love axis computation to complete the core data flow.  
**Objective:** Implement sentiment scoring, entity daily aggregation, axes computation, and snapshot persistence so the pipeline can produce complete heatmap data.

**What changed**
- Implemented basic lexicon-based sentiment analysis (`src/nlp/sentiment/f1_sentiment.py`)
- Implemented support and desire scoring (`src/nlp/sentiment/f2_support.py`, `f3_desire.py`)
- Implemented sentiment scoring step (`src/pipeline/steps/score_sentiment.py`)
- Implemented entity daily aggregation (`src/pipeline/steps/aggregate_entity_day.py`)
- Implemented axes computation (`src/pipeline/steps/compute_axes.py`)
- Implemented snapshot persistence (`src/pipeline/steps/write_snapshot.py`)
- Implemented run metrics persistence (`src/pipeline/steps/write_run_metrics.py`)
- Fixed datetime timezone issues in Reddit ingestion (naive vs aware datetimes)
- Fixed database migration script to create tables before indexes
- Fixed entity resolver to work with pre-extracted mentions
- Fixed duplicate source item handling (graceful skip)
- Fixed run_metrics table column mapping
- Fixed deprecated datetime.utcnow() calls throughout codebase

**Decisions**
- Decision: Use lexicon-based sentiment for v1 instead of ML models
  - Why: Faster to implement, no model dependencies, good enough for initial testing
  - Alternatives: CardiffNLP models (twitter-roberta-base-sentiment-latest) - deferred to Phase 2
- Decision: Simple entity resolution (first candidate) instead of full disambiguation
  - Why: Get data flowing first, improve resolution later with context-based disambiguation
  - Alternatives: Full caption-first context weighting, pronoun resolution - deferred to Phase 2
- Decision: Store run_metrics in separate table with specific JSON columns
  - Why: Matches schema design, allows querying specific metrics without parsing JSON
  - Alternatives: Single JSON column in runs table - rejected for queryability

**Gotchas / Debugging notes**
- Symptom: "can't compare offset-naive and offset-aware datetimes" in Reddit ingestion
- Root cause: Reddit API returns naive UTC timestamps, but window_start/window_end are timezone-aware
- Fix: Explicitly set timezone when converting from timestamp: `datetime.fromtimestamp(post.created_utc, tz=timezone.utc)`
- Prevention: Always use timezone-aware datetimes throughout pipeline

- Symptom: Database migration errors: "no such table: entities" when creating indexes
- Root cause: Migration script tried to create indexes before tables
- Fix: Separate CREATE TABLE statements from CREATE INDEX, execute in order
- Prevention: Split SQL parsing to execute DDL in correct sequence

- Symptom: "no such column: run_metrics" when trying to update runs table
- Root cause: Attempted to store metrics in runs.run_metrics column that doesn't exist
- Fix: Use run_metrics table with proper column structure (source_counts, mention_counts, etc.)
- Prevention: Check schema before attempting writes

**Verification**
- How we verified: Ran full pipeline end-to-end with Reddit data
- Result: 
  - Successfully ingested 6,742 Reddit items
  - Normalized 6,742 documents
  - Extracted 136 mentions (Taylor Swift - only pinned entity)
  - Resolved all 136 mentions
  - Scored sentiment for all mentions
  - Aggregated metrics for 1 entity
  - Computed fame/love axes
  - Wrote snapshot to database
  - Wrote run metrics successfully
  - Pipeline completed without errors

**Next steps**
- [ ] Implement baseline fame computation (Google Trends, Wikipedia pageviews)
- [ ] Implement momentum calculation (requires historical data)
- [ ] Implement drivers and themes generation
- [ ] Upgrade sentiment to ML models (CardiffNLP)
- [ ] Improve entity resolution with context-based disambiguation
- [ ] Add more entities to catalog (currently only Taylor Swift)

**Narrative nugget**
This was the moment the pipeline came alive. After fixing timezone bugs and database schema issues, watching 6,742 Reddit posts flow through ingestion → normalization → mention extraction → resolution → sentiment → aggregation → axes computation felt like witnessing a machine learning itself. The lexicon-based sentiment is crude—it's basically keyword matching—but it works. The simple "first candidate wins" resolution is naive, but 136 mentions resolved successfully. The real win was proving the architecture: each stage is independent, testable, and replaceable. The ML models can come later; for now, simple is enough to see data on the heatmap.
