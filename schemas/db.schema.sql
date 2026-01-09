-- Entertainment Feelings Heatmap Database Schema
-- Postgres-compatible (for SQLite: swap JSONB -> TEXT, TIMESTAMPTZ -> TEXT)

-- ============================================================================
-- 1. CORE CATALOG
-- ============================================================================

-- ENTITIES: The main entity catalog (people, shows, films, etc.)
CREATE TABLE IF NOT EXISTS entities (
  entity_id           TEXT PRIMARY KEY,      -- e.g. "person_q26876" or UUID
  entity_key          TEXT UNIQUE NOT NULL,  -- stable slug ("person_taylor_swift")
  canonical_name      TEXT NOT NULL,
  entity_type         TEXT NOT NULL,         -- PERSON/SHOW/FILM/FRANCHISE/...
  is_pinned           BOOLEAN NOT NULL DEFAULT FALSE,
  is_active           BOOLEAN NOT NULL DEFAULT TRUE,
  first_seen_at       TIMESTAMPTZ,
  last_seen_at        TIMESTAMPTZ,
  dormant_since       TIMESTAMPTZ,
  external_ids        JSONB NOT NULL DEFAULT '{}'::jsonb,   -- {wikidata:"Q..", imdb:".."}
  context_hints       JSONB NOT NULL DEFAULT '[]'::jsonb,   -- ["ERAS TOUR", ...]
  metadata            JSONB NOT NULL DEFAULT '{}'::jsonb    -- genres, network, etc.
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_last_seen ON entities(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_entities_pinned ON entities(is_pinned) WHERE is_pinned = TRUE;

-- ALIASES: Known aliases/nicknames for entities
CREATE TABLE IF NOT EXISTS entity_aliases (
  alias_id            BIGSERIAL PRIMARY KEY,
  entity_id           TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  alias               TEXT NOT NULL,
  alias_norm          TEXT NOT NULL,
  is_primary          BOOLEAN NOT NULL DEFAULT FALSE,
  confidence          REAL NOT NULL DEFAULT 1.0
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_entity_aliases_entity_aliasnorm
  ON entity_aliases(entity_id, alias_norm);

CREATE INDEX IF NOT EXISTS idx_entity_aliases_aliasnorm
  ON entity_aliases(alias_norm);

-- RELATIONSHIPS: Parent/child (franchise->film) and couple membership
CREATE TABLE IF NOT EXISTS entity_relationships (
  rel_id              BIGSERIAL PRIMARY KEY,
  parent_entity_id    TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  child_entity_id     TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  rel_type            TEXT NOT NULL,         -- "PARENT_CHILD" | "COUPLE_MEMBER" | "BRAND_OWNS" ...
  metadata            JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_entity_relationships_parent ON entity_relationships(parent_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_relationships_child ON entity_relationships(child_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_relationships_type ON entity_relationships(rel_type);

-- ============================================================================
-- 2. INGESTED CONTENT (raw + normalized)
-- ============================================================================

-- RAW ITEMS: Platform-native ingested content
CREATE TABLE IF NOT EXISTS source_items (
  item_id             TEXT PRIMARY KEY,
  source              TEXT NOT NULL,         -- ET_YT/GDELT_NEWS/REDDIT/...
  url                 TEXT,
  published_at        TIMESTAMPTZ,
  fetched_at          TIMESTAMPTZ NOT NULL,
  title               TEXT,
  description         TEXT,
  author              TEXT,
  engagement          JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {views:100, likes:10, ...}
  raw_payload         JSONB NOT NULL DEFAULT '{}'::jsonb   -- original API response
);

CREATE INDEX IF NOT EXISTS idx_source_items_source_time ON source_items(source, published_at);
CREATE INDEX IF NOT EXISTS idx_source_items_fetched_at ON source_items(fetched_at);
CREATE INDEX IF NOT EXISTS idx_source_items_url ON source_items(url) WHERE url IS NOT NULL;

-- NORMALIZED DOCS: What NLP runs on (cleaned, standardized)
CREATE TABLE IF NOT EXISTS documents (
  doc_id              TEXT PRIMARY KEY,
  item_id             TEXT NOT NULL REFERENCES source_items(item_id) ON DELETE CASCADE,
  doc_timestamp       TIMESTAMPTZ NOT NULL,  -- the time we attribute it to in the 6AM→6AM window
  lang                TEXT NOT NULL DEFAULT 'en',
  text_title          TEXT,
  text_caption        TEXT,
  text_body           TEXT,
  text_all            TEXT NOT NULL,         -- concatenated canonical text used for extraction
  quality_flags       JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {garbled:true, asr_used:true}
  hash_sim            TEXT                   -- for dedupe (minhash/signature id)
);

CREATE INDEX IF NOT EXISTS idx_documents_timestamp ON documents(doc_timestamp);
CREATE INDEX IF NOT EXISTS idx_documents_item ON documents(item_id);
CREATE INDEX IF NOT EXISTS idx_documents_hash_sim ON documents(hash_sim) WHERE hash_sim IS NOT NULL;

-- ============================================================================
-- 3. MENTIONS + UNRESOLVED
-- ============================================================================

-- RESOLVED + IMPLICIT MENTIONS: The only ones that affect scoring
CREATE TABLE IF NOT EXISTS mentions (
  mention_id          TEXT PRIMARY KEY,
  doc_id              TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  entity_id           TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  sent_idx            INT,
  span_start          INT,
  span_end            INT,
  surface             TEXT,
  is_implicit         BOOLEAN NOT NULL DEFAULT FALSE,
  weight              REAL NOT NULL DEFAULT 1.0,           -- implicit down-weight (e.g., 0.5)
  resolve_confidence  REAL NOT NULL DEFAULT 1.0,
  features            JSONB NOT NULL DEFAULT '{}'::jsonb   -- sentiment_pos/neg/support/desire
);

CREATE INDEX IF NOT EXISTS idx_mentions_entity ON mentions(entity_id);
CREATE INDEX IF NOT EXISTS idx_mentions_doc ON mentions(doc_id);
CREATE INDEX IF NOT EXISTS idx_mentions_entity_doc ON mentions(entity_id, doc_id);
CREATE INDEX IF NOT EXISTS idx_mentions_implicit ON mentions(is_implicit) WHERE is_implicit = TRUE;

-- UNRESOLVED MENTIONS: Excluded from scoring; used only for resolve queue + instrumentation
CREATE TABLE IF NOT EXISTS unresolved_mentions (
  unresolved_id       TEXT PRIMARY KEY,
  doc_id              TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  surface             TEXT NOT NULL,
  surface_norm        TEXT NOT NULL,
  sent_idx            INT,
  context             TEXT,
  candidates          JSONB NOT NULL DEFAULT '[]'::jsonb,  -- [{entity_id, score, features}, ...]
  top_score           REAL,
  second_score        REAL,
  created_at          TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_unresolved_surface_norm ON unresolved_mentions(surface_norm);
CREATE INDEX IF NOT EXISTS idx_unresolved_doc ON unresolved_mentions(doc_id);
CREATE INDEX IF NOT EXISTS idx_unresolved_created_at ON unresolved_mentions(created_at DESC);

-- ============================================================================
-- 4. DAILY WINDOWS + SNAPSHOTS
-- ============================================================================

-- RUNS: One per daily window (6AM PT → 6AM PT)
CREATE TABLE IF NOT EXISTS runs (
  run_id              TEXT PRIMARY KEY,
  window_start        TIMESTAMPTZ NOT NULL,
  window_end          TIMESTAMPTZ NOT NULL,
  started_at          TIMESTAMPTZ NOT NULL,
  finished_at         TIMESTAMPTZ,
  status              TEXT NOT NULL,         -- "SUCCESS" | "FAILED" | "PARTIAL"
  config_hash         TEXT,
  notes               TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_runs_window ON runs(window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at DESC);

-- RUN METRICS: Instrumentation per run
CREATE TABLE IF NOT EXISTS run_metrics (
  run_id              TEXT PRIMARY KEY REFERENCES runs(run_id) ON DELETE CASCADE,
  source_counts       JSONB NOT NULL DEFAULT '{}'::jsonb,  -- items ingested per source
  mention_counts      JSONB NOT NULL DEFAULT '{}'::jsonb,  -- total/resolved/unresolved/implicit
  unresolved_top      JSONB NOT NULL DEFAULT '[]'::jsonb,  -- top 20 unresolved summary
  timings_ms          JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {ingest:..., resolve:...}
  created_at          TIMESTAMPTZ NOT NULL
);

-- PER-ENTITY DAILY METRICS: The "dot" on the heatmap
CREATE TABLE IF NOT EXISTS entity_daily_metrics (
  run_id              TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
  entity_id           TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,

  fame                REAL NOT NULL,         -- 0..100
  love                REAL NOT NULL,         -- 0..100 (0=hate, 50=neutral, 100=love)
  attention           REAL NOT NULL,         -- normalized 0..100
  baseline_fame       REAL,                  -- normalized 0..100 (weekly)
  momentum            REAL NOT NULL,         -- normalized -?..? (or 0..100)
  polarization        REAL NOT NULL,         -- 0..100
  confidence          REAL NOT NULL,         -- 0..100

  mentions_explicit   INT NOT NULL DEFAULT 0,
  mentions_implicit   INT NOT NULL DEFAULT 0,
  sources_distinct    INT NOT NULL DEFAULT 0,

  is_dormant          BOOLEAN NOT NULL DEFAULT FALSE,
  dormant_reason      TEXT,

  metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,

  PRIMARY KEY (run_id, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_entity_daily_metrics_entity ON entity_daily_metrics(entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_daily_metrics_run ON entity_daily_metrics(run_id);
CREATE INDEX IF NOT EXISTS idx_entity_daily_metrics_fame ON entity_daily_metrics(fame);
CREATE INDEX IF NOT EXISTS idx_entity_daily_metrics_love ON entity_daily_metrics(love);

-- TOP DRIVERS: Linked evidence for drilldown
CREATE TABLE IF NOT EXISTS entity_daily_drivers (
  run_id              TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
  entity_id           TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  rank                INT NOT NULL,
  item_id             TEXT NOT NULL REFERENCES source_items(item_id) ON DELETE CASCADE,
  impact_score        REAL NOT NULL,
  driver_reason       TEXT,                  -- short reason for drilldown
  PRIMARY KEY (run_id, entity_id, rank)
);

CREATE INDEX IF NOT EXISTS idx_entity_daily_drivers_entity ON entity_daily_drivers(entity_id, run_id);

-- THEMES: Clustered topics for drilldown
CREATE TABLE IF NOT EXISTS entity_daily_themes (
  run_id              TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
  entity_id           TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  theme_id            TEXT NOT NULL,
  label               TEXT NOT NULL,
  keywords            JSONB NOT NULL DEFAULT '[]'::jsonb,
  volume              INT NOT NULL DEFAULT 0,
  sentiment_mix       JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {pos:0.3, neu:0.4, neg:0.3}
  PRIMARY KEY (run_id, entity_id, theme_id)
);

CREATE INDEX IF NOT EXISTS idx_entity_daily_themes_entity ON entity_daily_themes(entity_id, run_id);

-- ============================================================================
-- 5. BASELINES (weekly trends)
-- ============================================================================

-- WEEKLY BASELINE FAME: Google Trends, Wikipedia pageviews, etc.
CREATE TABLE IF NOT EXISTS entity_weekly_baseline (
  entity_id           TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  week_start          DATE NOT NULL,
  baseline_fame       REAL NOT NULL,         -- 0..100
  source              TEXT NOT NULL DEFAULT 'google_trends',
  metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (entity_id, week_start, source)
);

CREATE INDEX IF NOT EXISTS idx_entity_weekly_baseline_week ON entity_weekly_baseline(week_start);
CREATE INDEX IF NOT EXISTS idx_entity_weekly_baseline_entity ON entity_weekly_baseline(entity_id);

-- ============================================================================
-- NOTES FOR SQLITE MIGRATION
-- ============================================================================
-- To use with SQLite:
-- 1. Replace JSONB with TEXT (store JSON strings)
-- 2. Replace TIMESTAMPTZ with TEXT (ISO 8601 format)
-- 3. Replace BIGSERIAL with INTEGER (auto-increment)
-- 4. Remove IF NOT EXISTS from CREATE INDEX (or handle separately)
-- 5. Remove ::jsonb casts in DEFAULT clauses
-- 6. Adjust ON DELETE CASCADE syntax if needed
