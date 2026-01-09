"""
Compute fame/love coordinates and color layers (momentum, polarization, confidence).
"""

from typing import List, Dict, Any
from datetime import datetime
import math
import logging

from src.common.config import load_yaml_config

logger = logging.getLogger(__name__)


def compute_axes(entity_metrics: List[dict], window_start: datetime) -> List[dict]:
    """
    Compute final axes scores:
    - Fame (baseline + attention)
    - Love (sentiment -> 0..100)
    - Momentum (velocity in fame/love space)
    - Polarization (extreme sentiment share)
    - Confidence (signal quality)
    
    Returns entity_metrics with axes computed.
    """
    # Load config for weights
    weights_config = load_yaml_config("config/weights.yaml")
    fame_config = weights_config.get("fame", {})
    baseline_weight = fame_config.get("baseline_weight", 0.3)
    attention_weight = fame_config.get("attention_weight", 0.7)
    
    # Load weekly baseline fame for entities
    from src.storage.dao.snapshots import SnapshotDAO
    
    final_metrics = []
    
    # Get baseline for all entities
    baselines = {}
    with SnapshotDAO() as snapshot_dao:
        entity_ids = [m["entity_id"] for m in entity_metrics]
        for entity_id in entity_ids:
            baseline = snapshot_dao.get_baseline_for_entity(entity_id)
            if baseline:
                baselines[entity_id] = baseline.get("baseline_fame", 0.0)
            else:
                baselines[entity_id] = 0.0
    
    for metrics in entity_metrics:
        entity_id = metrics["entity_id"]
        
        # Load baseline fame from database or use 0
        baseline_fame = baselines.get(entity_id, 0.0)
        
        # Compute fame = baseline_weight * baseline + attention_weight * attention
        attention = metrics.get("attention", 0.0)
        
        # Normalize attention to 0..100 scale (log scale, max at ~10)
        attention_normalized = min(100.0, (attention / 10.0) * 100.0)
        
        # Compute fame
        fame = (baseline_weight * baseline_fame) + (attention_weight * attention_normalized)
        fame = min(100.0, max(0.0, fame))
        
        # Compute love from sentiment (-1 to 1 -> 0 to 100)
        # love = 50 + 50 * (pos - neg)
        sentiment_pos = metrics.get("sentiment_pos", 0.0)
        sentiment_neg = metrics.get("sentiment_neg", 0.0)
        
        love_raw = sentiment_pos - sentiment_neg  # -1 to 1
        love = 50.0 + (50.0 * love_raw)  # 0 to 100
        love = min(100.0, max(0.0, love))
        
        # Momentum (for now, set to 0 - will need historical data for real calculation)
        momentum = 0.0
        
        # Polarization (already computed in aggregation)
        polarization = metrics.get("polarization", 0.0) * 100.0  # Convert to 0..100
        
        # Confidence (already computed in aggregation)
        confidence = metrics.get("confidence", 0.0)
        
        # Update metrics
        metrics["fame"] = float(fame)
        metrics["love"] = float(love)
        metrics["momentum"] = float(momentum)
        metrics["polarization"] = float(polarization)
        metrics["confidence"] = float(confidence)
        metrics["baseline_fame"] = float(baseline_fame) if baseline_fame else None
        metrics["attention"] = float(attention_normalized)
        metrics["mentions_explicit"] = int(metrics.get("explicit_count", 0))
        metrics["mentions_implicit"] = int(metrics.get("implicit_count", 0))
        metrics["sources_distinct"] = int(metrics.get("sources_distinct", 0))
        
        final_metrics.append(metrics)
    
    logger.info(f"Computed axes for {len(final_metrics)} entities")
    return final_metrics
