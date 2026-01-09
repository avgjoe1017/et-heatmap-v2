# ENTERTAINMENT FEELINGS HEATMAP

**Product Spec (v1 buildable)**
**Suggested filename:** `specs/entertainment_feelings_heatmap.product_spec.md`

---

## 0) One-liner

A daily-updated (6:00am PT) scatter-plot heatmap that places **people, shows, films, franchises, brands, characters, streamers/networks, and couples** on:

* **X-axis:** Fame (baseline + today’s attention)
* **Y-axis:** Love (hate → indifference → love)
* **Color (default):** Momentum (how fast the dot is moving recently), with toggles for **Polarization** and **Confidence**

---

## 1) Primary user, decisions, cadence

### Primary user

* **You** (v1 operator)
* Later: **ET execs** (v2+ stakeholders)

### Decisions this drives (daily)

* Who to **book** / feature
* Where to **spend promo**
* Which franchise/show/person to **lean into**
* **Crisis / backlash detection**
* “**Who’s rising**” / “who’s cooling”
* Portfolio view of culture: what’s **dominant**, what’s **polarizing**, what’s **quietly building**

### Cadence

* **Daily run**: window = **6:00am PT → 6:00am PT** (user-changeable), with recency weighting inside the window
* Persistent history so you can **track where they’ve been** (trails / time travel)

---

## 2) What appears on the map (entity model)

### Entity types (v1 must support)

* PERSON (celebs, creators, execs if needed)
* SHOW
* FILM
* FRANCHISE / IP
* BRAND (entertainment brands)
* STREAMER / NETWORK / STUDIO
* CHARACTER (optional v1, but supported by schema)
* COUPLE (special handling below)

### Unified map + filtering

* One unified dataset, UI supports filters:

  * Type (PERSON/SHOW/etc.)
  * Genre (if available)
  * Studio/network/streamer
  * Franchise membership
  * “ET-relevant” tags (custom)
  * Pinned vs discovered
  * “Only movers” / “Only polarizing” / “Only high confidence”

### Couples (v1 approach: first-class entity, minimal confusion)

Couples are their own entity, resolvable and clickable.

**How created**

* Discovered when:

  * Text explicitly indicates couple relationship (“dating”, “engaged”, “wife/husband”, “together”, ship-name, etc.)
  * Frequent **co-mentions** in the same doc cluster with relationship language

**How scored**

* Couple has its own Fame/Love signals from:

  * Mentions of the couple as a unit (“**X and Y**”, “**X/Y**”, ship-name)
  * Relationship-themed content clusters
* Optional “synergy” attribute:

  * `synergy = couple_attention - (attention_x + attention_y)/2` (normalized)
* **Important:** avoid double counting

  * If the mention is about the couple as a unit, it feeds the couple
  * If the mention is clearly about one partner, it feeds the individual

---

## 3) Inputs (v1 = free + start small, then expand)

You said: **Instagram, YouTube, Reddit, X, TikTok, Google Trends, News** (all free), plus **ET YouTube feed**.

### v1 “start small” recommendation (so this actually ships)

1. **News backbone**

* **GDELT 2.1** as the default discovery + article URL feed ([Wikitech][1]) (GDELT docs are the standard entry point; use GDELT 2.1 APIs)

2. **Google Trends (weekly baseline fame)**

* `pytrends` (unofficial) ([GitHub][2])
* Update weekly, used only for **baseline fame** (not “today attention”)

3. **Reddit**

* Use **PRAW** (official-ish wrapper around Reddit API) ([GitHub][3])
* Start with a curated list of subreddits that actually move entertainment talk

4. **YouTube**

* ET YouTube channel feed + transcripts
* Pull transcripts via `youtube-transcript-api` ([GitHub][3])
* (Optional later) comments + engagement

5. **X / TikTok / Instagram**

* Treat these as “phase 2 ingestion” because reliability changes frequently
* If you do v1 anyway:

  * `snscrape` as a general scraper toolkit ([GitHub][4])
  * `twscrape` is powerful but operationally heavier (requires authorized accounts/cookies) ([GitHub][5])
  * For TikTok/Instagram, plan on Playwright-based scraping (more effort, more brittle)

### Additional *free* “non-text fame” signals that give a real edge

**Wikipedia pageviews** is one of the best “public attention” proxies that’s not tied to any one platform.

* Wikimedia Pageviews API exists and is documented ([Wikimedia][6])
* Note: pageviews can lag (often ~24h) ([Pageviews][7])
  Use it for baseline/lagged trend confirmation, not minute-by-minute.

---

## 4) Core definitions (the things you store and compute)

### SourceItem (raw)

A single ingested unit:

* News article URL + title + snippet + timestamp (from GDELT)
* Reddit post/comment
* YouTube video title/description/transcript segment
* Tweet/post/comment (later)

### NormalizedDocument (what you actually analyze)

A normalized text bundle created from SourceItem:

* `headline/title`
* `caption/description`
* `body/transcript`
* `platform metadata` (source, author id if allowed, engagement counts)
* `doc_timestamp` (the moment it was posted/published)

### Mention

An extracted reference to an entity candidate:

* mention text span
* doc context (caption/title/body)
* candidate entity list (pre-resolution)
* resolver decision (resolved entity_id or unresolved)

### EntityDailySignal

Aggregated daily metrics per entity:

* mention volume, engagement, source diversity
* sentiment distribution
* attention score
* fame baseline score
* final fame/love coordinates
* momentum, polarization, confidence

---

## 5) The strict resolver rule (no phantom dots)

### Rule

**Exclude unresolved mentions from scoring until resolved.**
No placeholder entities. No “Taylor_unknown” dots.

### Why

* Keeps map explainable: **every dot is real**
* Resolve Queue makes high-impact ambiguities surface quickly
* Long-tail ambiguous junk gets ignored (good)

### Instrumentation requirement

Track:

* `unresolved_mentions_total`
* `unresolved_mentions_share = unresolved_mentions_total / total_mentions_detected`
* `top_unresolved_strings` (what keeps failing)
  If unresolved share grows, you fix catalog/resolver instead of polluting the map.

---

## 6) Entity extraction + disambiguation (caption-first, pronouns, implied subjects)

You asked: “Use caption/content for context clues. Pronouns/implied subjects refer to whoever is referenced in caption/content.”

### v1 resolution strategy (fast + shippable)

**Step 0: Entity Catalog (your truth set)**

* Backed by **Wikidata** IDs + optional IMDb IDs for film/TV
* Store:

  * canonical name
  * aliases (nicknames, ship names, abbreviations)
  * type + metadata (genre, network, franchise)
  * external ids (Wikidata QID, IMDb, etc.)

Use a Wikidata client to build/refresh catalog:

* `qwikidata` ([GitHub][8])
* (Optional) other Wikidata python clients exist ([GitHub][9])

**Step 1: Mention detection (NER + alias match)**

* Run NER over normalized text:

  * spaCy core library ([GitHub][10])
  * For social-y text specifically, consider CardiffNLP’s TweetNLP stack ([GitHub][11])
* Also run dictionary/alias matching for known entities (faster + more reliable than NER alone):

  * `FlashText` for keyword matching ([GitHub][12])
  * `pyahocorasick` for fast multi-pattern matching ([GitHub][13])

**Step 2: Candidate generation**
For each mention string:

* exact alias hits
* fuzzy alias hits (to catch misspellings):

  * `RapidFuzz` ([GitHub][14])

**Step 3: Caption-first context rule**
Resolver uses a weighted context stack:

1. **Caption/title** (highest weight)
2. **Body/transcript**
3. Neighboring entities in the same doc (co-mentions)
4. Known type constraints (if it’s clearly a show vs a person)

**Step 4: Pronouns + implied subject**
If a sentence has no explicit name (“They were amazing”):

* If caption/title resolves to a single primary entity → assign to that entity
* Else if prior sentence resolves a primary entity with high confidence → assign
* Else unresolved

For coreference support (optional but powerful):

* `fastcoref` ([GitHub][15])
* `coreferee` (spaCy extension) ([GitHub][16])

**Step 5: Disambiguation fallback (entity linking)**
If you want a real edge beyond rules, add entity linking for ambiguous names:

* **REL (Radboud Entity Linker)** ([GitHub][17])
* **BLINK** exists but is archived (still useful as reference/baseline) ([GitHub][18])
* REL also has batch tooling via REBL ([GitHub][19])

**Step 6: Resolve Queue**
Unresolved mention strings land in:

* A queue UI/table with:

  * mention string
  * top contexts (caption/title)
  * sample docs
  * candidate suggestions
  * “resolve to existing entity” or “create new entity”
* Once resolved, backfill future runs automatically.

---

## 7) Axis definitions + scoring (the heart)

### Time windows

* **Daily window (default):** 6am PT → 6am PT
* **Rolling history:** 90 days
* **Pinned list:** always included even if dormant (your “permanent culture index”)

### Recency weighting (within daily window)

Use exponential decay so “yesterday morning” matters less than “last night”:

* half-life suggestion: **6–10 hours** (tunable)

---

## 8) Fame axis (baseline + attention + buzz)

You want:

* “Fame is a point”
* “Buzz is velocity of rising fame”
* Fame should include **baseline + today’s attention**

### Inputs to fame

**Baseline Fame (weekly-updated)**

* Google Trends interest (weekly) (normalized) via pytrends ([GitHub][2])
* (Optional) Wikipedia pageviews (lagged) ([Wikimedia][6])
* 90-day rolling average conversation volume (normalized)

**Today Attention (daily)**

* mention volume (log-scaled)
* engagement (log-scaled)
* source diversity bonus (more sources = more real)

### Output

* `fame_score` scaled 0–100

### Buzz velocity (not an axis; a derived metric)

* `buzz_velocity = attention_today - attention_7d_ema` (normalized)
  Used in drilldowns and “movers” lists.

---

## 9) Love axis (hate → indifferent → love)

You want:

* “Love is a mix of sentiment and favorability”
* bottom is **hate** (not indifference)

### v1 operational definition

Compute mention-level sentiment, then aggregate to entity daily:

**Sentiment models (strong v1 choices)**

* `cardiffnlp/twitter-roberta-base-sentiment-latest` (social-tuned sentiment) ([Hugging Face][20])
* For *entity-targeted* sentiment (critical for “X was great” vs “movie was great”):

  * `cardiffnlp/twitter-roberta-base-topic-sentiment-latest` ([Hugging Face][21])

**Toxicity / hate amplifier (optional but useful)**

* Detoxify ([GDELT Project][22])
  Use as a penalty factor when negativity is abusive/intense (vs mild criticism).

### Aggregation

* Convert model outputs into a continuous score per mention in [-1, +1]
* Apply recency weighting + source weighting
* `love_raw = weighted_mean(sentiment_scores)`
* Convert to axis scale:

  * `love_score = 50 * (love_raw + 1)` → 0..100

    * 0 = hated, 50 = indifferent/neutral, 100 = loved

---

## 10) Color layer (default = Momentum; toggles = Polarization + Confidence)

### Default: Momentum (how fast the dot is moving)

Define movement in the fame/love space:

* `delta_fame = fame_today - fame_7d_ema`
* `delta_love = love_today - love_7d_ema`
* `momentum = magnitude(delta_fame, delta_love)` (signed if you want “up vs down”)

Color mapping (conceptually):

* positive movement → “hot”
* negative movement → “cooling”
* near zero → stable

### Toggle: Polarization

People can be famous and divisive.

Compute from sentiment distribution:

* `pos_extreme = share(sentiment > +0.6)`
* `neg_extreme = share(sentiment < -0.6)`
* `polarization = pos_extreme + neg_extreme` (0..1)

### Toggle: Confidence

Confidence answers: “Do we have enough signal to believe this dot’s location?”

Compute from:

* effective sample size (mentions)
* source diversity
* engagement-weighted volume
  Output a 0..1 score.

---

## 11) Weighting (sources + engagement)

### Source weights (v1 suggestion)

* News: higher weight for “attention”, moderate for “love” (news tone can skew negative)
* Reddit: strong for “love/polarization”
* YouTube (ET): strong for “attention” + ET relevance
* X/TikTok/IG: strong for velocity, but only once ingestion is stable

### Engagement normalization

Because each platform has different engagement mechanics:

* Transform counts using `log1p`
* Normalize within source per day to percentile ranks
* Combine across sources

---

## 12) Output + UX

### Main view

* Scatter plot with quadrants (each entity = one dot)
* Dot size: constant (per your request)
* Axes:

  * X = Fame (0..100)
  * Y = Love (0..100)
* Color:

  * default: Momentum
  * toggles: Polarization, Confidence

### Filtering

* By type, genre, platform source, pinned/discovered, franchise, network, etc.
* “Only movers” (top N by momentum)
* “Only polarizing” (threshold)
* “Only high confidence”

### Drill-down panel (click dot)

You said: **yes drill-down**, but **no representative quotes**.

Show:

* Current coordinates + trend arrows
* 7-day sparkline for:

  * fame
  * love
  * attention volume
* Top drivers (ranked):

  * top news URLs
  * top reddit posts
  * top youtube videos
  * top themes (topic clusters)
* “Why it moved” (narrative, light explainability)

  * Example format:

    * “Attention spiked from [source mix]. Love dropped due to negative targeted sentiment around [theme].”

---

## 13) Themes (so execs can understand “what the conversation is about”)

Use embedding + clustering, then label clusters.

Recommended stack:

* Sentence embeddings: Sentence-Transformers ([GitHub][23])
* Clustering: HDBSCAN ([GitHub][24])
* Dimensionality reduction (optional): UMAP ([GitHub][25])
* Topic modeling:

  * BERTopic ([GitHub][26])
* Keyword labeling:

  * KeyBERT ([GitHub][27])

Store:

* cluster label
* top keywords
* cluster volume
* sentiment mix per cluster

---

## 14) Data storage + pipeline architecture (v1 pragmatic)

### v1 recommended stores

* **DuckDB** for fast local analytics + snapshots ([GitHub][28])
* Optionally **SQLite** for transactional tables (resolve queue, catalog edits)
* If/when this becomes multi-user: Postgres

### Pipeline orchestrator

* Keep v1 simple: cron + python entrypoint
* If you want observability/retries:

  * Prefect ([GitHub][29])
  * Dagster ([GitHub][30])

### Daily run stages (6am PT)

1. Ingest sources (GDELT, Reddit, YouTube, Trends if scheduled)
2. Normalize documents
3. Extract mentions (NER + alias)
4. Resolve mentions (caption-first + queue fallback)
5. Score mention-level sentiment + features
6. Aggregate to entity daily signals
7. Compute fame/love coordinates + color layers
8. Generate snapshots + API payload for UI
9. Emit instrumentation + run report

---

## 15) Content extraction & scraping helpers (high leverage)

News page text extraction (because URLs are messy):

* `trafilatura` ([GitHub][10])
* (Alt) `newspaper3k` ([GitHub][31])

General scraping automation:

* Playwright (Python) ([GitHub][27])

YouTube utilities:

* youtube-transcript-api ([GitHub][3])
* yt-dlp (if you need metadata/download fallback) ([GitHub][32])
* If no transcript exists:

  * Whisper (ASR fallback; treat as lower-trust text)

---

## 16) The pinned list + naming

### Pinned list file (v1)

**Use a JSON file in repo** (versioned, simple).

**Filename:** `config/pinned_entities.json`

Example schema:

```json
[
  {
    "entity_id": "person_q26876",
    "canonical_name": "Taylor Swift",
    "type": "PERSON",
    "aliases": ["T-Swift", "Tay"],
    "external_ids": { "wikidata": "Q26876" },
    "pin_reason": "Always culturally relevant"
  }
]
```

---

## 17) Open-source “edge pack” (GitHub + Hugging Face)

These are the pieces that most directly improve **signal quality**, **resolution**, and **exec-trust**.

### A) Entity resolution / catalog (biggest quality lever)

* spaCy (NER + pipelines) ([GitHub][10])
* TweetNLP (social-tuned NER and utilities) ([GitHub][11])
* RapidFuzz (fuzzy alias matching) ([GitHub][14])
* FlashText (fast alias/keyword detection) ([GitHub][12])
* pyahocorasick (fast multi-alias scanning) ([GitHub][13])
* qwikidata (Wikidata ingestion) ([GitHub][8])
* REL (entity linking / disambiguation) ([GitHub][17])
* BLINK (archived, still informative baseline) ([GitHub][33])

### B) Sentiment + targeted sentiment (your Love axis lives here)

* HF model: twitter-roberta sentiment latest ([Hugging Face][20])
* HF model: topic-sentiment (targeted sentiment) ([Hugging Face][21])
* Detoxify (toxicity intensity) ([GDELT Project][22])

### C) “What are they talking about” (themes that execs understand)

* Sentence-Transformers ([GitHub][23])
* BERTopic ([GitHub][26])
* KeyBERT ([GitHub][27])
* HDBSCAN ([GitHub][24])
* UMAP ([GitHub][25])
* FAISS (if you want fast similarity search later) ([GitHub][34])

### D) Dedupe / spam / near-duplicate cleanup

* datasketch (MinHash/LSH) ([GitHub][35])

### E) Source ingestion (free)

* GDELT + wrapper libraries (API backbone) ([Wikitech][1])
* PRAW (Reddit) ([GitHub][3])
* youtube-transcript-api ([GitHub][3])
* pytrends (Google Trends; unofficial) ([GitHub][2])
* Wikimedia Pageviews API (free attention proxy) ([Wikimedia][6])
* snscrape (multi-SNS scraping toolkit) ([GitHub][4])
* twscrape (X scraping, operationally heavy) ([GitHub][5])

### F) Pipeline + performance

* DuckDB ([GitHub][28])
* Polars (fast dataframe ops) ([GitHub][18])
* Prefect ([GitHub][29])
* Dagster ([GitHub][30])

### G) Visualization (open-source UI)

* Apache ECharts ([GitHub][8])
* Plotly.js ([GitHub][36])
* deck.gl (if you want high-performance scatter later) ([GitHub][37])

---

## 18) v1 milestones (so it ships)

### Phase 1 (core)

* GDELT + Reddit + ET YouTube transcripts + pinned list
* Resolver + Resolve Queue
* Fame/Love/Momentum computed daily
* Basic UI scatter + filters + drilldown (no quotes)

### Phase 2 (credibility + edge)

* Targeted sentiment everywhere
* Theme clustering per entity (BERTopic)
* Wikipedia pageviews baseline
* Confidence scoring tuned

### Phase 3 (platform expansion)

* X ingestion
* TikTok/IG ingestion (only once stable)
* Comments at scale + anti-spam

---

## 19) Assumptions I’m locking (so your engineer can build without back-and-forth)

* **All entities share one coordinate system** (0–100 fame, 0–100 love)
* **Daily window default is 6am PT → 6am PT**
* **Unresolved mentions are excluded** from scoring (but tracked)
* **Momentum = default color layer**
* **No representative quotes** stored/displayed
* **90-day rolling + pinned list** defines the active universe

---



[1]: https://wikitech.wikimedia.org/wiki/Data_Platform/AQS/Pageviews?utm_source=chatgpt.com "Data Platform/AQS/Pageviews - Wikitech - Wikimedia"
[2]: https://github.com/GeneralMills/pytrends?utm_source=chatgpt.com "GeneralMills/pytrends: Pseudo API for Google Trends"
[3]: https://github.com/jdepoix/youtube-transcript-api?utm_source=chatgpt.com "jdepoix/youtube-transcript-api"
[4]: https://github.com/JustAnotherArchivist/snscrape?utm_source=chatgpt.com "Snscrape - A social networking service scraper in Python"
[5]: https://github.com/vladkens/twscrape?utm_source=chatgpt.com "vladkens/twscrape"
[6]: https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/?utm_source=chatgpt.com "Wikimedia Analytics API"
[7]: https://pageviews.wmcloud.org/pageviews/faq/?utm_source=chatgpt.com "FAQ - Pageviews Analysis"
[8]: https://github.com/kensho-technologies/qwikidata?utm_source=chatgpt.com "kensho-technologies/qwikidata: Python tools for interacting ..."
[9]: https://github.com/dahlia/wikidata?utm_source=chatgpt.com "Wikidata client library for Python - dahlia dahlia"
[10]: https://github.com/unitaryai/detoxify?utm_source=chatgpt.com "unitaryai/detoxify: Trained models & code to predict toxic ..."
[11]: https://github.com/cardiffnlp/tweetnlp?utm_source=chatgpt.com "cardiffnlp/tweetnlp"
[12]: https://github.com/vi3k6i5/flashtext?utm_source=chatgpt.com "vi3k6i5/flashtext: Extract Keywords from sentence or ..."
[13]: https://github.com/WojciechMula/pyahocorasick?utm_source=chatgpt.com "WojciechMula/pyahocorasick: Python module (C extension ..."
[14]: https://github.com/rapidfuzz/RapidFuzz?utm_source=chatgpt.com "Rapid fuzzy string matching in Python using various ..."
[15]: https://github.com/shon-otmazgin/fastcoref?utm_source=chatgpt.com "shon-otmazgin/fastcoref"
[16]: https://github.com/msg-systems/coreferee?utm_source=chatgpt.com "msg-systems/coreferee"
[17]: https://github.com/informagi/REL?utm_source=chatgpt.com "informagi/REL - Radboud Entity Linker"
[18]: https://github.com/facebookresearch/BLINK?utm_source=chatgpt.com "facebookresearch/BLINK: Entity Linker solution"
[19]: https://github.com/informagi/REBL?utm_source=chatgpt.com "informagi/REBL: Entity linking of a JSON lines collection"
[20]: https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest?utm_source=chatgpt.com "cardiffnlp/twitter-roberta-base-sentiment-latest"
[21]: https://huggingface.co/cardiffnlp/twitter-roberta-base-topic-sentiment-latest?utm_source=chatgpt.com "cardiffnlp/twitter-roberta-base-topic-sentiment-latest"
[22]: https://www.gdeltproject.org/data.html?utm_source=chatgpt.com "Data: Querying, Analyzing and Downloading"
[23]: https://github.com/huggingface/sentence-transformers?utm_source=chatgpt.com "huggingface/sentence-transformers: State-of-the-Art Text ..."
[24]: https://github.com/scikit-learn-contrib/hdbscan?utm_source=chatgpt.com "A high performance implementation of HDBSCAN clustering."
[25]: https://github.com/lmcinnes/umap?utm_source=chatgpt.com "lmcinnes/umap: Uniform Manifold Approximation and ..."
[26]: https://github.com/MaartenGr/BERTopic?utm_source=chatgpt.com "MaartenGr/BERTopic: Leveraging BERT and c-TF-IDF to ..."
[27]: https://github.com/MaartenGr/KeyBERT?utm_source=chatgpt.com "MaartenGr/KeyBERT: Minimal keyword extraction with BERT"
[28]: https://github.com/explosion/spacy-models?utm_source=chatgpt.com "explosion/spacy-models"
[29]: https://github.com/PrefectHQ/prefect?utm_source=chatgpt.com "PrefectHQ/prefect"
[30]: https://github.com/adbar/trafilatura?utm_source=chatgpt.com "adbar/trafilatura: Python & Command-line tool to gather text ..."
[31]: https://github.com/praw-dev/praw?utm_source=chatgpt.com "PRAW, an acronym for \"Python Reddit API Wrapper\" ..."
[32]: https://github.com/yt-dlp/yt-dlp?utm_source=chatgpt.com "yt-dlp/yt-dlp: A feature-rich command-line audio/video ..."
[33]: https://github.com/facebookresearch/BLINK/issues?utm_source=chatgpt.com "Issues · facebookresearch/BLINK"
[34]: https://github.com/facebookresearch/faiss?utm_source=chatgpt.com "facebookresearch/faiss: A library for efficient similarity ..."
[35]: https://github.com/apache/echarts?utm_source=chatgpt.com "Apache ECharts is a powerful, interactive charting and data ..."
[36]: https://github.com/duckdb/duckdb?utm_source=chatgpt.com "DuckDB is an analytical in-process SQL database ..."
[37]: https://github.com/pola-rs/polars?utm_source=chatgpt.com "pola-rs/polars: Extremely fast Query Engine for ..."
