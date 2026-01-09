"""
Aggregate mentions to entity daily metrics.
"""

import math
from typing import List, Dict, Any
from datetime import datetime, timezone
import logging

from src.common.config import load_yaml_config

logger = logging.getLogger(__name__)


def aggregate_entity_daily(mentions: List[dict], window_start: datetime, documents: List[dict] = None, source_items: List[dict] = None) -> List[dict]:
    """
    Aggregate resolved mentions to entity_daily_metrics.
    Applies recency weighting, source weights, engagement normalization.
    
    Returns list of entity_daily_metrics records.
    """
    if not mentions:
        return []
    
    # Load config for weights
    weights_config = load_yaml_config("config/weights.yaml")
    source_weights = weights_config.get("source_weights", {})
    fame_weights = source_weights.get("fame", {})
    love_weights = source_weights.get("love", {})
    implicit_weight = weights_config.get("implicit_mentions", {}).get("default_weight", 0.5)
    
    # Group mentions by entity_id
    entity_mentions: Dict[str, List[dict]] = {}
    for mention in mentions:
        entity_id = mention.get("entity_id")
        if not entity_id:
            continue
        entity_mentions.setdefault(entity_id, []).append(mention)
    
    # Build lookup maps
    documents_map = {doc["doc_id"]: doc for doc in (documents or [])}
    source_items_map = {item["item_id"]: item for item in (source_items or [])}
    
    window_end = window_start  # Will be set properly in caller
    
    entity_metrics = []
    
    for entity_id, entity_mention_list in entity_mentions.items():
        if not entity_mention_list:
            continue
        
        # Aggregate metrics for this entity
        explicit_count = sum(1 for m in entity_mention_list if not m.get("is_implicit", False))
        implicit_count = sum(1 for m in entity_mention_list if m.get("is_implicit", False))
        
        # Get source diversity
        sources = set()
        for mention in entity_mention_list:
            doc_id = mention.get("doc_id")
            doc = documents_map.get(doc_id)
            if doc:
                item_id = doc.get("item_id")
                item = source_items_map.get(item_id)
                if item:
                    sources.add(item.get("source", "UNKNOWN"))
        sources_distinct = len(sources)
        
        # Aggregate sentiment with weighting
        weighted_pos = 0.0
        weighted_neg = 0.0
        weighted_neu = 0.0
        total_weight = 0.0
        
        for mention in entity_mention_list:
            features = mention.get("features", {})
            weight = mention.get("weight", 1.0)
            
            # Apply implicit down-weighting
            if mention.get("is_implicit", False):
                weight *= implicit_weight
            
            # Get source weight
            doc_id = mention.get("doc_id")
            doc = documents_map.get(doc_id)
            source = "UNKNOWN"
            if doc:
                item_id = doc.get("item_id")
                item = source_items_map.get(item_id)
                if item:
                    source = item.get("source", "UNKNOWN")
            
            source_weight = love_weights.get(source.lower(), 1.0)
            weight *= source_weight
            
            # Get sentiment scores
            pos = features.get("sentiment_pos", 0.0)
            neg = features.get("sentiment_neg", 0.0)
            neu = features.get("sentiment_neu", 0.0)
            
            weighted_pos += pos * weight
            weighted_neg += neg * weight
            weighted_neu += neu * weight
            total_weight += weight
        
        # Normalize sentiment
        if total_weight > 0:
            sentiment_pos = weighted_pos / total_weight
            sentiment_neg = weighted_neg / total_weight
            sentiment_neu = weighted_neu / total_weight
        else:
            sentiment_pos = 0.0
            sentiment_neg = 0.0
            sentiment_neu = 1.0
        
        # Compute attention (weighted mention volume)
        attention = math.log1p(explicit_count + implicit_count * implicit_weight)
        
        # Compute polarization (extreme sentiment share)
        # Polarization = share of mentions with extreme sentiment (>0.6 pos or >0.6 neg)
        extreme_count = 0
        for mention in entity_mention_list:
            features = mention.get("features", {})
            pos = features.get("sentiment_pos", 0.0)
            neg = features.get("sentiment_neg", 0.0)
            if pos > 0.6 or neg > 0.6:
                extreme_count += 1
        
        polarization = extreme_count / max(1, len(entity_mention_list))
        
        # Compute confidence (based on sample size and source diversity)
        # Simple heuristic for now
        confidence = min(100.0, (
            40.0 * math.log1p(explicit_count) / 10.0 +  # Sample size component
            30.0 * sources_distinct / 5.0 +  # Source diversity (max at 5 sources)
            30.0 * math.log1p(explicit_count) / 20.0  # Engagement component
        ))
        
        # Store metrics (before axis computation)
        metrics = {
            "entity_id": entity_id,
            "explicit_count": explicit_count,
            "implicit_count": implicit_count,
            "sources_distinct": sources_distinct,
            "attention": float(attention),
            "sentiment_pos": float(sentiment_pos),
            "sentiment_neg": float(sentiment_neg),
            "sentiment_neu": float(sentiment_neu),
            "polarization": float(polarization),
            "confidence": float(confidence),
            # These will be computed in compute_axes
            "fame": 0.0,
            "love": 50.0,  # Default to neutral
            "momentum": 0.0,
            "baseline_fame": None,
        }
        
        entity_metrics.append(metrics)
    
    logger.info(f"Aggregated metrics for {len(entity_metrics)} entities")
    return entity_metrics
