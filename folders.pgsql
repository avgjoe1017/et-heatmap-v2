ent-heatmap/
  README.md
  pyproject.toml
  .env.example

  config/
    pinned_entities.json
    sources.yaml
    subreddits.txt
    news_domains.txt
    weights.yaml

  schemas/
    api.snapshot.schema.json
    api.drilldown.schema.json
    api.resolve_queue.schema.json
    db.entity_catalog.schema.json

  src/
    app/
      main.py                 # FastAPI (or Flask) entrypoint
      api/
        routes_snapshot.py
        routes_entity.py
        routes_resolve_queue.py
        routes_runs.py
      service/
        snapshot_service.py
        entity_service.py
        resolve_queue_service.py
        run_service.py

    pipeline/
      daily_run.py            # orchestrates 6AM→6AM run
      weekly_baseline.py      # google trends baseline refresh
      steps/
        ingest_et_youtube.py
        ingest_gdelt_news.py
        ingest_reddit.py
        ingest_wikipedia_pageviews.py   # optional baseline confirmation
        normalize_docs.py
        dedupe_docs.py
        extract_mentions.py
        entity_resolver.py     # your two-pass explicit + implicit attribution
        score_sentiment.py
        aggregate_entity_day.py
        compute_axes.py
        build_drivers.py
        build_themes.py
        write_snapshot.py
        write_run_metrics.py
        build_resolve_queue.py

    nlp/
      sentiment/
        f1_sentiment.py       # sentiment model wrapper
        f2_support.py         # support lexicon + patterns
        f3_desire.py          # desire lexicon + patterns
        target_sentiment.py   # optional targeted sentiment wrapper
      themes/
        embed.py              # sentence embeddings
        cluster.py            # clustering + labeling
      utils/
        text.py               # cleaning, sentence splitting, lang checks
        time.py               # 6AM→6AM window logic

    catalog/
      catalog_loader.py       # load/merge pinned + discovered + resolved
      wikidata_enrich.py      # optional
      imdb_tmdb_enrich.py     # optional
      alias_tools.py          # normalization, alias generation

    storage/
      db.py                   # DB connection + migrations
      dao/
        entities.py
        source_items.py
        documents.py
        mentions.py
        snapshots.py
        runs.py
        unresolved.py

    common/
      types.py                # dataclasses/pydantic models
      constants.py
      logging.py

  ui/
    package.json
    vite.config.ts
    src/
      app/
        App.tsx
        pages/
          HeatmapPage.tsx
          EntityPage.tsx
          RunsPage.tsx
          ResolveQueuePage.tsx
        components/
          Heatmap.tsx
          Filters.tsx
          TimelineScrubber.tsx
          DrilldownPanel.tsx
          DriversList.tsx
          ThemesList.tsx
        api/
          client.ts
          types.ts
