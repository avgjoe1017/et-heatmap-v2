-- ENTITIES
CREATE TABLE entities (
  entity_id           TEXT PRIMARY KEY,      -- e.g. "person_q26876" or UUID
  entity_key          TEXT UNIQUE NOT NULL,   -- stable slug ("person_taylor_swift")
  canonical_name      TEXT NOT NULL,
  entity_type         TEXT NOT NULL,          -- PERSON/SHOW/FILM/FRANCHISE/...
  is_pinned           BOOLEAN NOT NULL DEFAULT FALSE,
  is_active           BOOLEAN NOT NULL DEFAULT TRUE,
  first_seen_at       TIMESTAMPTZ,
  last_seen_at        TIMESTAMPTZ,
  dormant_since       TIMESTAMPTZ,
  external_ids        JSONB NOT NULL DEFAULT '{}'::jsonb,   -- {wikidata:"Q..", imdb:".."}
  context_hints       JSONB NOT NULL DEFAULT '[]'::jsonb,   -- ["ERAS TOUR", ...]
  metadata            JSONB NOT NULL DEFAULT '{}'::jsonb    -- genres, network, etc.
);

CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_last_seen ON entities(last_seen_at);

-- ALIASES
CREATE TABLE entity_aliases (
  alias_id            BIGSERIAL PRIMARY KEY,
  entity_id           TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  alias               TEXT NOT NULL,
  alias_norm          TEXT NOT NULL,
  is_primary          BOOLEAN NOT NULL DEFAULT FALSE,
  confidence          REAL NOT NULL DEFAULT 1.0
);

CREATE UNIQUE INDEX uq_entity_aliases_entity_aliasnorm
  ON entity_aliases(entity_id, alias_norm);

CREATE INDEX idx_entity_aliases_aliasnorm
  ON entity_aliases(alias_norm);

-- RELATIONSHIPS (parent/child and couple membership)
CREATE TABLE entity_relationships (
  rel_id              BIGSERIAL PRIMARY KEY,
  parent_entity_id    TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  child_entity_id     TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  rel_type            TEXT NOT NULL, -- "PARENT_CHILD" | "COUPLE_MEMBER" | "BRAND_OWNS" ...
  metadata            JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_entity_relationships_parent ON entity_relationships(parent_entity_id);
CREATE INDEX idx_entity_relationships_child  ON entity_relationships(child_entity_id);
CREATE INDEX idx_entity_relationships_type   ON entity_relationships(rel_type);
