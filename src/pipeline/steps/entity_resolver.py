"""
Resolve mentions to entities (caption-first, implicit attribution).
Integrates logic from src/resolution/entity_resolver.py
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, Any
import re
import math
import json

# Import the existing resolver logic
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "resolution"))

try:
    from entity_resolver import (
        ContentItem, CatalogEntity, Mention, UnresolvedMention, RunMetrics,
        process_item, build_resolve_queue,
        WINDOW_N_SENTENCES, IMPLICIT_WEIGHT, RESOLVE_MIN_CONF, RESOLVE_MIN_MARGIN
    )
    RESOLVER_AVAILABLE = True
except ImportError:
    # Fallback if import fails - will be implemented inline
    ContentItem = None
    RESOLVER_AVAILABLE = False

def resolve_mentions(
    mentions: List[dict],
    documents: List[dict],
    catalog: List[dict],
    source_items: List[dict],
) -> Tuple[List[dict], List[dict], dict]:
    """
    Resolve mentions to entities using caption-first context and implicit attribution.
    
    Args:
        mentions: Pre-extracted mentions (from extract_mentions step)
        documents: Normalized documents
        catalog: Entity catalog (from catalog_loader)
        source_items: Source items for context
    
    Returns:
        (resolved_mentions, unresolved_mentions, run_metrics)
    """
    # TODO: Implement or use existing resolver
    # - Convert documents to ContentItem format
    # - Convert catalog to CatalogEntity format
    # - Run two-pass resolution:
    #   PASS A: Explicit mentions -> resolve to entities
    #   PASS B: Pronoun/implied -> attribute to unambiguous focus
    # - Apply caption-first weighting
    # - Generate resolve queue for ambiguous
    # - Return resolved, unresolved, metrics
    
    # Build lookup maps for context
    documents_by_id = {doc["doc_id"]: doc for doc in documents}
    source_items_by_id = {item["item_id"]: item for item in source_items}
    
    # For v1, use simple resolution: if only one candidate, resolve to it
    # If multiple candidates, use first one for now (can enhance with context later)
    resolved = []
    unresolved = []
    
    import uuid
    
    for mention in mentions:
        candidates = mention.get("entity_candidates", [])
        doc_id = mention.get("doc_id")
        doc = documents_by_id.get(doc_id)
        
        if not candidates:
            # No candidates - add to unresolved
            unresolved.append({
                "unresolved_id": f"unresolved_{uuid.uuid4().hex[:16]}",
                "doc_id": doc_id,
                "surface": mention.get("surface", ""),
                "surface_norm": mention.get("surface", "").lower(),
                "sent_idx": mention.get("sent_idx"),
                "context": mention.get("context", mention.get("sentence", ""))[:500],
                "candidates": [],
                "created_at": datetime.now(timezone.utc).isoformat() if doc else None,
            })
            continue
        
        # Resolve to first candidate for now
        # TODO: Enhance with context-based disambiguation
        entity_id = candidates[0]
        confidence = 1.0 if len(candidates) == 1 else 0.7
        
        resolved.append({
            "mention_id": f"mention_{uuid.uuid4().hex[:16]}",
            "doc_id": doc_id,
            "entity_id": entity_id,
            "sent_idx": mention.get("sent_idx"),
            "span_start": mention.get("span_start", 0),
            "span_end": mention.get("span_end", len(mention.get("surface", ""))),
            "surface": mention.get("surface", ""),
            "is_implicit": False,
            "weight": 1.0,
            "resolve_confidence": confidence,
            "features": {}  # Will be populated by sentiment scoring
        })
    
    metrics = {
        "total_sentences": sum(len(doc.get("text_all", "").split(".")) for doc in documents),
        "total_mentions_explicit": len(mentions),
        "resolved_mentions_explicit": len(resolved),
        "unresolved_mentions_explicit": len(unresolved),
        "implicit_mentions_attributed": 0,
        "implicit_mentions_ignored_ambiguous": 0,
        "unresolved_mentions_rate": len(unresolved) / max(1, len(mentions)),
        "implicit_to_explicit_ratio": 0.0,
    }
    
    return resolved, unresolved, metrics
    
    # Use existing resolver
    metrics = RunMetrics()
    resolved_all = []
    unresolved_all = []
    
    # Build alias index from catalog
    alias_index = _build_alias_index(catalog)
    
    # Convert catalog to CatalogEntity format
    catalog_entities = [_dict_to_catalog_entity(e) for e in catalog]
    
    # Build lookup maps
    documents_by_item = {doc["item_id"]: doc for doc in documents}
    source_items_by_id = {item["item_id"]: item for item in source_items}
    
    # Process each document
    for doc in documents:
        item_id = doc["item_id"]
        source_item = source_items_by_id.get(item_id)
        
        if not source_item:
            continue
        
        # Convert to ContentItem format
        content_item = _document_to_content_item(doc, source_item)
        
        # Process item using existing resolver
        resolved_mentions, unresolved_mentions = process_item(
            content_item,
            catalog_entities,
            alias_index,
            metrics
        )
        
        # Convert back to dict format
        resolved_all.extend([_mention_to_dict(m, doc["doc_id"]) for m in resolved_mentions])
        unresolved_all.extend([_unresolved_to_dict(u, doc["doc_id"]) for u in unresolved_mentions])
    
    metrics.finalize()
    
    return resolved_all, unresolved_all, _metrics_to_dict(metrics)


def _build_alias_index(catalog: List[dict]) -> Dict[str, List[str]]:
    """Build alias index from catalog dicts."""
    idx = {}
    for e in catalog:
        entity_id = e["entity_id"]
        aliases = e.get("aliases", []) + [e.get("canonical_name", "")]
        for alias in aliases:
            key = _normalize(alias)
            idx.setdefault(key, []).append(entity_id)
    return idx


def _normalize(s: str) -> str:
    """Normalize string for matching."""
    return re.sub(r"\s+", " ", s.strip().lower())


def _dict_to_catalog_entity(d: dict) -> Any:
    """Convert catalog dict to CatalogEntity."""
    if not RESOLVER_AVAILABLE:
        return d
    
    from entity_resolver import CatalogEntity
    return CatalogEntity(
        entity_id=d["entity_id"],
        canonical_name=d.get("canonical_name", ""),
        type=d.get("entity_type", ""),
        aliases=d.get("aliases", []),
        context_hints=d.get("context_hints", []),
        prior_weight=d.get("prior_weight", 0.5),
        external_ids=d.get("external_ids", {})
    )


def _document_to_content_item(doc: dict, source_item: dict) -> Any:
    """Convert document and source_item to ContentItem."""
    if not RESOLVER_AVAILABLE:
        return None
    
    from entity_resolver import ContentItem
    
    # Parse engagement from JSONB/TEXT field
    engagement = source_item.get("engagement", {})
    if isinstance(engagement, str):
        try:
            engagement = json.loads(engagement)
        except:
            engagement = {}
    
    return ContentItem(
        item_id=doc["item_id"],
        source=source_item.get("source", ""),
        url=source_item.get("url", ""),
        timestamp=doc.get("doc_timestamp", ""),
        title=doc.get("text_title", ""),
        description=doc.get("text_caption", ""),
        body_text=doc.get("text_body", ""),
        engagement=engagement
    )


def _mention_to_dict(mention: Any, doc_id: str) -> dict:
    """Convert Mention dataclass to dict."""
    return {
        "mention_id": f"{doc_id}_{mention.sent_idx}_{mention.span[0]}_{mention.span[1]}",
        "doc_id": doc_id,
        "entity_id": mention.entity_id,
        "sent_idx": mention.sent_idx,
        "span_start": mention.span[0],
        "span_end": mention.span[1],
        "surface": mention.surface,
        "is_implicit": mention.is_implicit,
        "weight": mention.weight,
        "resolve_confidence": mention.confidence,
        "features": json.dumps(mention.features) if isinstance(mention.features, dict) else mention.features
    }


def _unresolved_to_dict(unresolved: Any, doc_id: str) -> dict:
    """Convert UnresolvedMention dataclass to dict."""
    return {
        "unresolved_id": f"{doc_id}_{unresolved.sent_idx}_{hash(unresolved.surface)}",
        "doc_id": doc_id,
        "surface": unresolved.surface,
        "surface_norm": _normalize(unresolved.surface),
        "sent_idx": unresolved.sent_idx,
        "context": unresolved.context,
        "candidates": json.dumps(unresolved.candidates),
        "top_score": None,
        "second_score": None
    }


def _metrics_to_dict(metrics: Any) -> dict:
    """Convert RunMetrics to dict."""
    if hasattr(metrics, "__dict__"):
        return {
            k: v for k, v in metrics.__dict__.items()
            if not k.startswith("_")
        }
    return {
        "total_sentences": getattr(metrics, "total_sentences", 0),
        "total_mentions_explicit": getattr(metrics, "total_mentions_explicit", 0),
        "resolved_mentions_explicit": getattr(metrics, "resolved_mentions_explicit", 0),
        "unresolved_mentions_explicit": getattr(metrics, "unresolved_mentions_explicit", 0),
        "implicit_mentions_attributed": getattr(metrics, "implicit_mentions_attributed", 0),
        "implicit_mentions_ignored_ambiguous": getattr(metrics, "implicit_mentions_ignored_ambiguous", 0),
        "unresolved_mentions_rate": getattr(metrics, "unresolved_mentions_rate", 0.0),
        "implicit_to_explicit_ratio": getattr(metrics, "implicit_to_explicit_ratio", 0.0),
    }
