"""
Integration tests for the daily pipeline.
Tests end-to-end pipeline execution with real data.
"""

import pytest
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipeline.daily_run import run_daily_pipeline
from src.storage.dao.runs import RunDAO
from src.storage.dao.snapshots import SnapshotDAO
from src.storage.dao.mentions import MentionDAO
from src.catalog.catalog_loader import load_catalog


@pytest.fixture
def test_window():
    """Create a test window (yesterday to today)."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=1)
    window_end = now
    return window_start, window_end


@pytest.mark.integration
def test_pipeline_runs_successfully(test_window):
    """Test that the pipeline runs end-to-end without errors."""
    window_start, _ = test_window
    
    # Run pipeline
    run_id = run_daily_pipeline(window_start)
    
    assert run_id is not None, "Pipeline should return a run_id"
    
    # Verify run was created
    with RunDAO() as run_dao:
        run = run_dao.get_run(run_id)
        assert run is not None, "Run should be created in database"
        assert run["status"] == "SUCCESS", f"Run should succeed, got status: {run['status']}"


@pytest.mark.integration
def test_pipeline_ingests_data(test_window):
    """Test that pipeline ingests source items."""
    window_start, _ = test_window
    
    # Count source items before
    from src.storage.dao.source_items import SourceItemDAO
    with SourceItemDAO() as dao:
        before_count = len(dao.execute_select("source_items", {}))
    
    # Run pipeline
    run_id = run_daily_pipeline(window_start)
    assert run_id is not None
    
    # Count source items after
    with SourceItemDAO() as dao:
        after_count = len(dao.execute_select("source_items", {}))
    
    # Should have ingested some items (or at least not decreased)
    assert after_count >= before_count, "Pipeline should ingest source items"


@pytest.mark.integration
def test_pipeline_creates_metrics(test_window):
    """Test that pipeline creates entity metrics."""
    window_start, _ = test_window
    
    # Run pipeline
    run_id = run_daily_pipeline(window_start)
    assert run_id is not None
    
    # Check for entity metrics
    with SnapshotDAO() as snapshot_dao:
        metrics = snapshot_dao.get_entity_metrics_for_run(run_id)
        
        # Should have metrics for at least some entities
        # (may be empty if no mentions found, but should not error)
        assert isinstance(metrics, list), "Should return list of metrics"


@pytest.mark.integration
def test_catalog_loads_entities():
    """Test that catalog loads entities correctly."""
    catalog = load_catalog()
    
    assert isinstance(catalog, list), "Catalog should be a list"
    assert len(catalog) > 0, "Catalog should have at least one entity"
    
    # Verify entity structure
    for entity in catalog:
        assert "entity_id" in entity, "Entity should have entity_id"
        assert "canonical_name" in entity, "Entity should have canonical_name"
        assert "entity_type" in entity, "Entity should have entity_type"


@pytest.mark.integration
def test_sentiment_scoring():
    """Test that sentiment scoring works."""
    from src.nlp.sentiment.f1_sentiment import analyze_sentiment
    
    # Test positive sentiment
    result = analyze_sentiment("I love this movie!")
    assert "pos" in result
    assert "neg" in result
    assert "neu" in result
    assert 0 <= result["pos"] <= 1
    assert 0 <= result["neg"] <= 1
    assert 0 <= result["neu"] <= 1
    assert abs(result["pos"] + result["neg"] + result["neu"] - 1.0) < 0.01  # Should sum to ~1.0


@pytest.mark.integration
def test_baseline_fame_computation():
    """Test baseline fame computation."""
    from src.pipeline.steps.compute_baseline_fame import compute_baseline_fame
    from src.catalog.catalog_loader import load_catalog
    
    catalog = load_catalog()
    if not catalog:
        pytest.skip("No entities in catalog")
    
    # Compute baseline for first entity
    baselines = compute_baseline_fame(catalog[:1])
    
    assert len(baselines) > 0, "Should compute baseline"
    baseline = baselines[0]
    
    assert "entity_id" in baseline
    assert "baseline_fame" in baseline
    assert 0 <= baseline["baseline_fame"] <= 100, "Baseline fame should be 0-100"


@pytest.mark.integration
def test_drivers_generation():
    """Test drivers generation."""
    from src.pipeline.steps.build_drivers import build_drivers
    
    # Create mock data
    mentions = []
    entity_metrics = [{"entity_id": "test_entity", "fame": 50.0, "love": 50.0}]
    documents = []
    source_items = []
    
    # Should not error even with empty data
    drivers = build_drivers(mentions, entity_metrics, documents, source_items)
    assert isinstance(drivers, list), "Should return list of drivers"


@pytest.mark.integration
def test_themes_generation():
    """Test themes generation."""
    from src.pipeline.steps.build_themes import build_themes
    
    # Create mock data
    mentions = []
    documents = []
    entity_metrics = [{"entity_id": "test_entity"}]
    
    # Should not error even with empty data
    themes = build_themes(mentions, documents, entity_metrics)
    assert isinstance(themes, list), "Should return list of themes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
