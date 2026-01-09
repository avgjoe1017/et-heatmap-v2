"""
Daily pipeline orchestrator (6AM PT → 6AM PT window).
"""

from datetime import datetime, timedelta, timezone
import pytz
import uuid
import json
from typing import Optional
from pathlib import Path

from src.storage.db import get_session
from src.storage.dao.runs import RunDAO
from src.storage.dao.source_items import SourceItemDAO
from src.common.logging import setup_logging
from src.common.constants import DAILY_WINDOW_HOUR, DAILY_WINDOW_TIMEZONE

# Setup logging
setup_logging()
import logging
logger = logging.getLogger(__name__)

PACIFIC = pytz.timezone(DAILY_WINDOW_TIMEZONE)


def get_daily_window(window_start: Optional[datetime] = None) -> tuple:
    """
    Get daily window (6AM PT → 6AM PT).
    Returns (window_start, window_end) as aware datetimes.
    """
    if window_start is None:
        # Calculate latest 6AM PT boundary
        now_utc = datetime.now(timezone.utc)
        now_pt = now_utc.astimezone(PACIFIC)
        
        # Find last 6AM PT
        window_end = now_pt.replace(hour=DAILY_WINDOW_HOUR, minute=0, second=0, microsecond=0)
        if window_end > now_pt:
            window_end = window_end - timedelta(days=1)
        
        window_start = window_end - timedelta(days=1)
    else:
        # Ensure window_start is timezone-aware
        if window_start.tzinfo is None:
            window_start = PACIFIC.localize(window_start)
        window_end = window_start + timedelta(days=1)
    
    # Convert to UTC for storage
    window_start_utc = window_start.astimezone(pytz.UTC)
    window_end_utc = window_end.astimezone(pytz.UTC)
    
    return window_start_utc, window_end_utc


def run_daily_pipeline(window_start: Optional[datetime] = None) -> str:
    """
    Orchestrates the full daily pipeline run.
    
    Stages:
    1. Ingest sources (GDELT, Reddit, YouTube, Trends if scheduled)
    2. Normalize documents
    3. Extract mentions (NER + alias)
    4. Resolve mentions (caption-first + queue fallback)
    5. Score mention-level sentiment + features
    6. Aggregate to entity daily signals
    7. Compute fame/love coordinates + color layers
    8. Generate snapshots + API payload for UI
    9. Emit instrumentation + run report
    
    Returns run_id.
    """
    # Calculate window
    window_start_utc, window_end_utc = get_daily_window(window_start)
    
    # Create run record
    run_id = str(uuid.uuid4())
    run_data = {
        "run_id": run_id,
        "window_start": window_start_utc,
        "window_end": window_end_utc,
        "started_at": datetime.now(timezone.utc),
        "status": "RUNNING",
    }
    
    with RunDAO() as run_dao:
        run_dao.create_run(run_data)
    
    logger.info(f"Starting daily pipeline run {run_id} for window {window_start_utc} to {window_end_utc}")
    
    try:
        # Stage 1: Ingest sources
        logger.info("Stage 1: Ingesting sources...")
        source_items = _ingest_sources(window_start_utc, window_end_utc)
        logger.info(f"Ingested {len(source_items)} source items")
        
        # Stage 2: Normalize documents
        logger.info("Stage 2: Normalizing documents...")
        documents = _normalize_documents(source_items)
        logger.info(f"Normalized {len(documents)} documents")
        
        # Stage 3: Extract mentions
        logger.info("Stage 3: Extracting mentions...")
        from src.catalog.catalog_loader import load_catalog
        catalog = load_catalog()
        mentions, unresolved_pre = _extract_mentions(documents, catalog)
        logger.info(f"Extracted {len(mentions)} mentions")
        
        # Stage 4: Resolve mentions
        logger.info("Stage 4: Resolving mentions...")
        # Catalog already loaded above
        resolved_mentions, unresolved_mentions, metrics = _resolve_mentions(
            mentions, documents, catalog, source_items
        )
        logger.info(f"Resolved {len(resolved_mentions)} mentions, {len(unresolved_mentions)} unresolved")
        
        # Stage 5: Score sentiment
        logger.info("Stage 5: Scoring sentiment...")
        scored_mentions = _score_sentiment(resolved_mentions)
        logger.info(f"Scored {len(scored_mentions)} mentions")
        
        # Stage 6: Aggregate to entity daily
        logger.info("Stage 6: Aggregating entity metrics...")
        entity_metrics = _aggregate_entity_daily(scored_mentions, window_start_utc, documents, source_items)
        logger.info(f"Aggregated metrics for {len(entity_metrics)} entities")
        
        # Stage 7: Compute axes
        logger.info("Stage 7: Computing axes...")
        final_metrics = _compute_axes(entity_metrics, window_start_utc)
        logger.info(f"Computed axes for {len(final_metrics)} entities")
        
        # Stage 8: Build drivers and themes
        logger.info("Stage 8: Building drivers and themes...")
        drivers = _build_drivers(scored_mentions, final_metrics, documents, source_items)
        themes = _build_themes(scored_mentions, documents, final_metrics)
        logger.info(f"Built {len(drivers)} drivers and {len(themes)} themes")
        
        # Stage 9: Write snapshot
        logger.info("Stage 9: Writing snapshot...")
        _write_snapshot(run_id, final_metrics, drivers, themes)
        
        # Stage 10: Write run metrics
        logger.info("Stage 10: Writing run metrics...")
        _write_run_metrics(run_id, metrics, source_items, documents, scored_mentions)
        
        # Update run status
        with RunDAO() as run_dao:
            run_dao.update_run_status(run_id, "SUCCESS", datetime.now(timezone.utc))
        
        logger.info(f"Daily pipeline run {run_id} completed successfully!")
        return run_id
        
    except Exception as e:
        logger.error(f"Pipeline run {run_id} failed: {e}", exc_info=True)
        
        # Update run status
        with RunDAO() as run_dao:
            run_dao.update_run_status(run_id, "FAILED", datetime.now(timezone.utc))
        
        raise


def _ingest_sources(window_start: datetime, window_end: datetime) -> list:
    """Ingest sources from configured providers."""
    source_items = []
    
    # Import ingestion modules
    from src.pipeline.steps.ingest_reddit import ingest_reddit
    from src.common.config import load_yaml_config
    
    # Check which sources are enabled
    sources_config = load_yaml_config("config/sources.yaml")
    sources = sources_config.get("sources", {})
    
    # Reddit ingestion
    if sources.get("reddit", {}).get("enabled", False):
        try:
            reddit_items = ingest_reddit(window_start, window_end)
            source_items.extend(reddit_items)
        except Exception as e:
            logger.error(f"Reddit ingestion failed: {e}", exc_info=True)
    
    # TODO: Add other sources
    # from src.pipeline.steps.ingest_gdelt_news import ingest_gdelt_news
    # from src.pipeline.steps.ingest_et_youtube import ingest_et_youtube
    
    # Store source items in database (skip duplicates gracefully)
    if source_items:
        from src.storage.dao.source_items import SourceItemDAO
        stored_count = 0
        skipped_count = 0
        with SourceItemDAO() as dao:
            for item in source_items:
                try:
                    dao.create_source_item(item)
                    stored_count += 1
                except Exception as e:
                    error_msg = str(e)
                    if "UNIQUE constraint" in error_msg or "duplicate" in error_msg.lower():
                        skipped_count += 1
                        # Item already exists, skip silently
                    else:
                        logger.warning(f"Failed to store source item {item.get('item_id')}: {e}")
        
        logger.info(f"Stored {stored_count} new source items, skipped {skipped_count} duplicates")
    
    return source_items


def _normalize_documents(source_items: list) -> list:
    """Normalize source items to documents."""
    from src.pipeline.steps.normalize_docs import normalize_documents
    
    documents = normalize_documents(source_items)
    
    # Store documents in database
    if documents:
        from src.storage.dao.documents import DocumentDAO
        with DocumentDAO() as dao:
            for doc in documents:
                try:
                    dao.create_document(doc)
                except Exception as e:
                    logger.warning(f"Failed to store document {doc.get('doc_id')}: {e}")
    
    return documents


def _extract_mentions(documents: list, catalog: list) -> tuple:
    """Extract mentions from documents."""
    from src.pipeline.steps.extract_mentions import extract_mentions
    
    # Extract mentions (pre-resolution)
    mentions, unresolved = extract_mentions(documents, catalog)
    
    # Store unresolved mentions in database
    if unresolved:
        from src.storage.dao.unresolved import UnresolvedDAO
        
        with UnresolvedDAO() as dao:
            for u in unresolved:
                try:
                    u_data = {
                        "unresolved_id": f"unresolved_{hash(u.get('surface', ''))}",
                        "doc_id": u.get("doc_id", ""),
                        "surface": u.get("surface", ""),
                        "surface_norm": u.get("surface", "").lower(),
                        "context": u.get("context", ""),
                        "candidates": u.get("candidates", []),
                        "created_at": datetime.now(timezone.utc),
                    }
                    dao.create_unresolved_mention(u_data)
                except Exception as e:
                    logger.warning(f"Failed to store unresolved mention: {e}")
    
    return mentions, unresolved


def _resolve_mentions(mentions: list, documents: list, catalog: list, source_items: list) -> tuple:
    """Resolve mentions to entities."""
    from src.pipeline.steps.entity_resolver import resolve_mentions
    return resolve_mentions(mentions, documents, catalog, source_items)


def _score_sentiment(mentions: list) -> list:
    """Score sentiment for mentions."""
    from src.pipeline.steps.score_sentiment import score_sentiment
    return score_sentiment(mentions)


def _aggregate_entity_daily(mentions: list, window_start: datetime, documents: list, source_items: list) -> list:
    """Aggregate mentions to entity daily metrics."""
    from src.pipeline.steps.aggregate_entity_day import aggregate_entity_daily
    return aggregate_entity_daily(mentions, window_start, documents, source_items)


def _compute_axes(entity_metrics: list, window_start: datetime) -> list:
    """Compute fame/love axes."""
    # TODO: Import and call compute_axes
    # from src.pipeline.steps.compute_axes import compute_axes
    return entity_metrics


def _build_drivers(mentions: list, entity_metrics: list, documents: list, source_items: list) -> list:
    """Build top drivers for entities."""
    from src.pipeline.steps.build_drivers import build_drivers
    return build_drivers(mentions, entity_metrics, documents, source_items)


def _build_themes(mentions: list, documents: list, entity_metrics: list) -> list:
    """Build themes for entities."""
    from src.pipeline.steps.build_themes import build_themes
    return build_themes(mentions, documents, entity_metrics)


def _write_snapshot(run_id: str, entity_metrics: list, drivers: list, themes: list):
    """Write snapshot to database."""
    from src.pipeline.steps.write_snapshot import write_snapshot
    write_snapshot(run_id, entity_metrics, drivers, themes)


def _write_run_metrics(run_id: str, metrics: dict, source_items: list, mentions: list, unresolved: list):
    """Write run metrics to database."""
    from src.pipeline.steps.write_run_metrics import write_run_metrics
    write_run_metrics(run_id, metrics, source_items, mentions, unresolved)


if __name__ == "__main__":
    # Can be called via cron
    run_id = run_daily_pipeline()
    print(f"Daily pipeline completed: {run_id}")
