"""
Build resolve queue from unresolved mentions.
"""

import json
import math
from typing import List, Dict, Any


def _normalize(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.lower().split())


def _parse_engagement(engagement: Any) -> Dict[str, float]:
    if isinstance(engagement, dict):
        return engagement
    if isinstance(engagement, str):
        try:
            parsed = json.loads(engagement)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _compute_item_weight(item: dict) -> float:
    source = item.get("source", "")
    base = 1.0
    if source == "ET_YT":
        base = 2.0
    elif source == "GDELT_NEWS":
        base = 1.3
    elif source == "REDDIT":
        base = 1.2
    elif source == "YT":
        base = 1.1

    engagement = _parse_engagement(item.get("engagement"))
    total_engagement = 0.0
    for value in engagement.values():
        try:
            total_engagement += float(value)
        except (TypeError, ValueError):
            continue

    return base * (1.0 + 0.2 * math.log1p(total_engagement))


def _normalize_candidates(candidates: Any) -> List[dict]:
    if isinstance(candidates, list):
        normalized = []
        for cand in candidates:
            if isinstance(cand, dict):
                if "entity_id" in cand:
                    score = cand.get("score")
                    normalized.append({
                        "entity_id": cand["entity_id"],
                        "score": float(score) if score is not None else 0.0,
                        "features": cand.get("features", {}),
                    })
            elif isinstance(cand, str):
                normalized.append({"entity_id": cand, "score": 0.0, "features": {}})
        return normalized
    return []


def build_resolve_queue(unresolved_mentions: List[dict], source_items: List[dict]) -> List[dict]:
    """
    Aggregate unresolved mentions by surface_norm.
    Impact-weighted for prioritization.
    
    Returns list for resolve queue UI.
    """
    item_lookup = {item.get("item_id"): item for item in source_items}
    aggregated: Dict[str, dict] = {}

    for mention in unresolved_mentions:
        surface = mention.get("surface", "")
        key = _normalize(mention.get("surface_norm") or surface)
        if not key:
            continue

        item_id = mention.get("item_id")
        item = item_lookup.get(item_id)
        weight = _compute_item_weight(item) if item else 1.0

        entry = aggregated.setdefault(key, {
            "surface": surface,
            "count": 0,
            "impact": 0.0,
            "examples": [],
        })
        entry["count"] += 1
        entry["impact"] += weight

        if len(entry["examples"]) < 3:
            entry["examples"].append({
                "source": item.get("source", "UNKNOWN") if item else "UNKNOWN",
                "context": (mention.get("context") or "")[:280],
                "candidates": _normalize_candidates(mention.get("candidates", [])),
            })

    queue = list(aggregated.values())
    queue.sort(key=lambda x: x["impact"], reverse=True)
    return queue
