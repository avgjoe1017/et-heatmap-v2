"""
Build top drivers (linked evidence) for entity drilldowns.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
import math

from src.common.config import load_yaml_config

logger = logging.getLogger(__name__)


def build_drivers(
    mentions: List[dict],
    entity_metrics: List[dict],
    documents: List[dict],
    source_items: List[dict],
    limit: int = 10
) -> List[dict]:
    """
    Identify top source_items that drove entity metrics.
    Ranked by impact_score (engagement-weighted).
    
    Returns list of entity_daily_drivers records grouped by entity_id.
    """
    if not mentions or not entity_metrics:
        return []
    
    # Build lookup maps
    documents_map = {doc["doc_id"]: doc for doc in documents}
    source_items_map = {item["item_id"]: item for item in source_items}
    entity_map = {m["entity_id"]: m for m in entity_metrics}
    
    # Group mentions by entity_id and item_id
    entity_item_mentions: Dict[str, Dict[str, List[dict]]] = {}
    
    for mention in mentions:
        entity_id = mention.get("entity_id")
        doc_id = mention.get("doc_id")
        
        if not entity_id or not doc_id:
            continue
        
        doc = documents_map.get(doc_id)
        if not doc:
            continue
        
        item_id = doc.get("item_id")
        if not item_id:
            continue
        
        # Group by entity -> item
        entity_item_mentions.setdefault(entity_id, {}).setdefault(item_id, []).append(mention)
    
    # Build drivers for each entity
    all_drivers = []
    
    for entity_id, item_mentions in entity_item_mentions.items():
        if entity_id not in entity_map:
            continue
        
        entity_metric = entity_map[entity_id]
        
        # Compute impact score for each item
        item_impacts = []
        
        for item_id, item_mention_list in item_mentions.items():
            item = source_items_map.get(item_id)
            if not item:
                continue
            
            # Get engagement from item
            engagement = item.get("engagement", {})
            if isinstance(engagement, str):
                import json
                try:
                    engagement = json.loads(engagement)
                except:
                    engagement = {}
            
            # Compute impact score
            # Factors:
            # - Mention count (more mentions = more impact)
            # - Engagement (score, comments, views)
            # - Sentiment (positive sentiment amplifies)
            # - Recency (more recent = more impact)
            
            mention_count = len(item_mention_list)
            
            # Engagement score (log scale)
            score = engagement.get("score", 0) or 0
            num_comments = engagement.get("num_comments", 0) or 0
            engagement_score = math.log1p(score + num_comments)
            
            # Average sentiment (positive = higher impact)
            total_sentiment = 0.0
            for mention in item_mention_list:
                features = mention.get("features", {})
                pos = features.get("sentiment_pos", 0.0)
                neg = features.get("sentiment_neg", 0.0)
                sentiment = pos - neg  # -1 to 1
                total_sentiment += sentiment
            
            avg_sentiment = total_sentiment / max(1, mention_count)
            sentiment_multiplier = 1.0 + (avg_sentiment * 0.5)  # 0.5 to 1.5
            
            # Impact score
            impact_score = (
                mention_count * 10.0 +  # Base impact from mentions
                engagement_score * 5.0  # Engagement boost
            ) * sentiment_multiplier
            
            # Get source weight
            source = item.get("source", "UNKNOWN")
            weights_config = load_yaml_config("config/weights.yaml")
            source_weights = weights_config.get("source_weights", {})
            fame_weights = source_weights.get("fame", {})
            source_weight = fame_weights.get(source.lower(), 1.0)
            
            impact_score *= source_weight
            
            # Generate driver reason
            driver_reason = _generate_driver_reason(item, mention_count, engagement, avg_sentiment)
            
            item_impacts.append({
                "entity_id": entity_id,
                "item_id": item_id,
                "impact_score": float(impact_score),
                "mention_count": mention_count,
                "engagement": engagement,
                "driver_reason": driver_reason,
            })
        
        # Sort by impact and take top N
        item_impacts.sort(key=lambda x: x["impact_score"], reverse=True)
        top_items = item_impacts[:limit]
        
        # Create driver records
        for rank, item_impact in enumerate(top_items, start=1):
            all_drivers.append({
                "entity_id": item_impact["entity_id"],
                "rank": rank,
                "item_id": item_impact["item_id"],
                "impact_score": item_impact["impact_score"],
                "driver_reason": item_impact["driver_reason"],
            })
    
    logger.info(f"Built {len(all_drivers)} drivers for {len(entity_item_mentions)} entities")
    return all_drivers


def _generate_driver_reason(item: dict, mention_count: int, engagement: dict, avg_sentiment: float) -> str:
    """Generate a short narrative reason for why this item is a driver."""
    title = item.get("title", "")[:100]  # Truncate
    source = item.get("source", "UNKNOWN")
    
    reasons = []
    
    if mention_count > 5:
        reasons.append(f"{mention_count} mentions")
    
    score = engagement.get("score", 0) or 0
    if score > 100:
        reasons.append(f"{score} upvotes")
    
    if avg_sentiment > 0.3:
        reasons.append("positive sentiment")
    elif avg_sentiment < -0.3:
        reasons.append("negative sentiment")
    
    if reasons:
        reason_str = f"{title} ({', '.join(reasons)})"
    else:
        reason_str = f"{title} from {source}"
    
    return reason_str[:200]  # Limit length
