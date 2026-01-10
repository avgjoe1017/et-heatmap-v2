"""
Entity mention resolution (two-pass: explicit + implicit attribution).
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
import logging
import json
import re

logger = logging.getLogger(__name__)

# Try to import advanced resolver
RESOLVER_AVAILABLE = False
RunMetrics = None
process_item = None
ContentItem = None

try:
    from src.resolution.entity_resolver import (
        RunMetrics,
        process_item,
        ContentItem,
    )
    RESOLVER_AVAILABLE = True
except ImportError:
    # Fallback if import fails - will use simple resolution
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
    # Try to use existing resolver if available
    if RESOLVER_AVAILABLE and RunMetrics and process_item:
        try:
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
                
                if content_item is None:
                    continue
                
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
        except Exception as e:
            logger.warning(f"Advanced resolver failed, using simple resolution: {e}")
            # Fall through to simple resolution
    
    # Simple resolution (fallback or when resolver not available)
    # Build lookup maps for context
    documents_by_id = {doc["doc_id"]: doc for doc in documents}
    source_items_by_id = {item["item_id"]: item for item in source_items}
    catalog_by_id = {entity["entity_id"]: entity for entity in catalog}
    
    resolved = []
    unresolved = []
    
    import uuid
    
    for mention in mentions:
        candidates = mention.get("entity_candidates", [])
        doc_id = mention.get("doc_id")
        doc = documents_by_id.get(doc_id)
        context = mention.get("context") or mention.get("sentence") or ""
        
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
                "top_score": None,
                "second_score": None,
                "created_at": datetime.now(timezone.utc),
            })
            continue
        
        scored_candidates = _score_candidates(
            candidates=candidates,
            context=context,
            catalog_by_id=catalog_by_id,
        )
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_score = scored_candidates[0]["score"] if scored_candidates else None
        second_score = scored_candidates[1]["score"] if len(scored_candidates) > 1 else None
        margin = (top_score - second_score) if top_score is not None and second_score is not None else 0.0
        
        # Resolve to top candidate if confident enough
        entity_id = candidates[0]
        confidence = 1.0 if len(candidates) == 1 else 0.7
        if len(candidates) > 1 and scored_candidates:
            if top_score is not None and top_score >= _RESOLVE_MIN_SCORE and margin >= _RESOLVE_MIN_MARGIN:
                entity_id = scored_candidates[0]["entity_id"]
                confidence = top_score
        
        # If multiple candidates, add to unresolved for manual review
        if len(candidates) > 1 and (confidence < _RESOLVE_MIN_SCORE or margin < _RESOLVE_MIN_MARGIN):
            unresolved.append({
                "unresolved_id": f"unresolved_{uuid.uuid4().hex[:16]}",
                "doc_id": doc_id,
                "surface": mention.get("surface", ""),
                "surface_norm": mention.get("surface", "").lower(),
                "sent_idx": mention.get("sent_idx"),
                "context": mention.get("context", mention.get("sentence", ""))[:500],
                "candidates": scored_candidates,
                "top_score": top_score,
                "second_score": second_score,
                "created_at": datetime.now(timezone.utc),
            })
        else:
            # Single candidate - resolve
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
        "unresolved_mentions_rate": len(unresolved) / max(1, len(mentions)) if mentions else 0.0,
        "implicit_to_explicit_ratio": 0.0,
    }
    
    return resolved, unresolved, metrics


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
    if not s:
        return ""
    return s.lower().strip()


_RESOLVE_MIN_SCORE = 0.5
_RESOLVE_MIN_MARGIN = 0.1


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _score_candidates(
    candidates: List[str],
    context: str,
    catalog_by_id: Dict[str, dict],
) -> List[dict]:
    context_norm = _normalize_text(context)
    scored = []
    
    for entity_id in candidates:
        entity = catalog_by_id.get(entity_id, {})
        canonical = _normalize_text(entity.get("canonical_name", ""))
        context_hints = entity.get("context_hints", []) or []
        is_pinned = bool(entity.get("is_pinned", False))

        score = 0.0
        features = {
            "canonical_match": False,
            "context_hits": 0,
            "is_pinned": is_pinned,
        }

        if canonical and canonical in context_norm:
            score += 0.5
            features["canonical_match"] = True

        if context_hints:
            hits = 0
            for hint in context_hints:
                hint_norm = _normalize_text(hint)
                if hint_norm and hint_norm in context_norm:
                    hits += 1
            if hits:
                score += min(0.3, hits * 0.1)
                features["context_hits"] = hits

        if is_pinned:
            score += 0.1

        score = min(score, 1.0)
        scored.append({
            "entity_id": entity_id,
            "score": score,
            "features": features,
        })

    return scored


def _dict_to_catalog_entity(d: dict) -> Any:
    """Convert catalog dict to CatalogEntity format."""
    if not RESOLVER_AVAILABLE:
        return None
    
    try:
        from src.resolution.entity_resolver import CatalogEntity
        return CatalogEntity(
            entity_id=d["entity_id"],
            canonical_name=d.get("canonical_name", ""),
            entity_type=d.get("entity_type", "PERSON"),
            aliases=d.get("aliases", []),
            external_ids=d.get("external_ids", {})
        )
    except:
        return None


def _document_to_content_item(doc: dict, source_item: dict) -> Any:
    """Convert document and source_item to ContentItem."""
    if not RESOLVER_AVAILABLE:
        return None
    
    try:
        from src.resolution.entity_resolver import ContentItem
        
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
    except Exception as e:
        logger.debug(f"Failed to create ContentItem: {e}")
        return None


def _mention_to_dict(mention: Any, doc_id: str) -> dict:
    """Convert Mention dataclass to dict."""
    return {
        "mention_id": f"mention_{hash(str(mention))}",
        "doc_id": doc_id,
        "entity_id": mention.entity_id if hasattr(mention, 'entity_id') else "",
        "sent_idx": mention.sent_idx if hasattr(mention, 'sent_idx') else 0,
        "span_start": mention.span_start if hasattr(mention, 'span_start') else 0,
        "span_end": mention.span_end if hasattr(mention, 'span_end') else 0,
        "surface": mention.surface if hasattr(mention, 'surface') else "",
        "is_implicit": mention.is_implicit if hasattr(mention, 'is_implicit') else False,
        "weight": mention.weight if hasattr(mention, 'weight') else 1.0,
        "resolve_confidence": mention.resolve_confidence if hasattr(mention, 'resolve_confidence') else 1.0,
        "features": json.loads(mention.features) if isinstance(mention.features, str) else (
            mention.features if isinstance(mention.features, dict) else {}
        )
    }


def _unresolved_to_dict(unresolved: Any, doc_id: str) -> dict:
    """Convert UnresolvedMention dataclass to dict."""
    if hasattr(unresolved, 'surface'):
        # It's a dataclass
        return {
            "unresolved_id": f"{doc_id}_{unresolved.sent_idx}_{hash(unresolved.surface)}",
            "doc_id": doc_id,
            "surface": unresolved.surface,
            "surface_norm": _normalize(unresolved.surface),
            "sent_idx": unresolved.sent_idx,
            "context": unresolved.context[:500] if hasattr(unresolved, 'context') else "",
            "candidates": unresolved.candidates if hasattr(unresolved, 'candidates') else [],
            "top_score": getattr(unresolved, 'top_score', None),
            "second_score": getattr(unresolved, 'second_score', None),
            "created_at": datetime.now(timezone.utc),
        }
    else:
        # It's already a dict
        return unresolved


def _metrics_to_dict(metrics: Any) -> dict:
    """Convert RunMetrics to dict."""
    if hasattr(metrics, '__dict__'):
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
    else:
        # Already a dict
        return metrics
