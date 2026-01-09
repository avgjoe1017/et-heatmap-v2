# --------------------------------------------
# Resolver + Implicit Attribution (v1-safe)
# Deterministic, two-pass:
#   PASS A: Explicit entity mentions (NER + alias) -> resolve to canonical IDs
#   PASS B: Pronoun / implied-subject sentences -> attribute ONLY to unambiguous active subject
# --------------------------------------------

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any
import re
import math


# ---------- Data Models ----------

@dataclass
class ContentItem:
    item_id: str
    source: str                  # ET_YT, GDELT_NEWS, REDDIT, YT
    url: str
    timestamp: str
    title: str
    description: str
    body_text: str               # transcript / caption / snippet / comments slice
    engagement: Dict[str, float] # platform-specific counts
    # Optional fields (if available later)
    chapters: Optional[List[str]] = None


@dataclass
class CatalogEntity:
    entity_id: str
    canonical_name: str
    type: str  # PERSON, SHOW, FILM, FRANCHISE, NETWORK_STREAMER, COUPLE, BRAND, CHARACTER
    aliases: List[str]
    context_hints: List[str]     # tokens/phrases helpful for disambiguation
    prior_weight: float          # e.g. normalized frequency in ET seed / last 90d
    external_ids: Dict[str, str] # wikidata/imdb/tmdb/etc (optional)


@dataclass
class Mention:
    item_id: str
    sent_idx: int
    span: Tuple[int, int]        # char offsets within sentence
    surface: str                 # the string matched
    entity_id: Optional[str]     # resolved canonical entity_id OR None
    entity_type: Optional[str]   # if resolved
    confidence: float
    is_implicit: bool            # False for explicit, True for pronoun/implied attribution
    weight: float                # 1.0 explicit, <1.0 implicit
    features: Dict[str, float]   # pos/neg/support/desire, etc.
    debug: Dict[str, Any]        # candidates, scores, etc. (for resolve queue / QA)


@dataclass
class UnresolvedMention:
    item_id: str
    sent_idx: int
    surface: str
    context: str
    candidates: List[Dict[str, Any]]  # [{entity_id, score, reasons}, ...]


@dataclass
class RunMetrics:
    total_sentences: int = 0
    total_mentions_explicit: int = 0
    resolved_mentions_explicit: int = 0
    unresolved_mentions_explicit: int = 0

    implicit_mentions_attributed: int = 0
    implicit_mentions_ignored_ambiguous: int = 0

    unresolved_distinct_strings: int = 0
    unresolved_mentions_by_source: Dict[str, int] = None

    # Ratios (computed at end)
    unresolved_mentions_rate: float = 0.0
    implicit_to_explicit_ratio: float = 0.0

    # Helpful rollups
    unresolved_top_20: List[Dict[str, Any]] = None

    def finalize(self):
        if self.unresolved_mentions_by_source is None:
            self.unresolved_mentions_by_source = {}
        if self.unresolved_top_20 is None:
            self.unresolved_top_20 = []
        denom = max(1, self.total_mentions_explicit)
        self.unresolved_mentions_rate = self.unresolved_mentions_explicit / denom
        denom2 = max(1, self.total_mentions_explicit)
        self.implicit_to_explicit_ratio = self.implicit_mentions_attributed / denom2


# ---------- Parameters (tuneable, start strict) ----------

WINDOW_N_SENTENCES = 2                # focus window size
IMPLICIT_WEIGHT = 0.5                 # down-weight implicit attribution
RESOLVE_MIN_CONF = 0.70               # minimum accept confidence
RESOLVE_MIN_MARGIN = 0.15             # min gap vs #2 candidate
MAX_CANDIDATES = 7

# Scoring weights for disambiguation (sum to 1.0)
W_PRIOR = 0.40
W_CONTEXT = 0.25
W_COMENTION = 0.20
W_TYPEFIT = 0.10
W_SOURCE = 0.05


# ---------- Simple NLP utilities ----------

PRONOUN_RE = re.compile(r"\b(they|them|their|theirs|he|him|his|she|her|hers)\b", re.I)

def split_sentences(text: str) -> List[str]:
    # Replace with a deterministic sentence splitter you trust
    # For v1: simple rule-based split is okay
    parts = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]

def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())

def has_pronoun(sentence: str) -> bool:
    return PRONOUN_RE.search(sentence) is not None

def log1p(x: float) -> float:
    return math.log(1.0 + max(0.0, x))

def sentiment_support_desire(sentence: str) -> Dict[str, float]:
    """
    Deterministic placeholder for v1.
    Replace sentiment with an off-the-shelf classifier later.
    For now, implement:
      - sentiment_pos, sentiment_neg in [0,1]
      - support_score in [0,1] from lexicon
      - desire_score in [0,1] from lexicon
    """
    s = normalize(sentence)

    # Minimal lexicons (expand over time)
    support_terms = ["iconic", "legend", "queen", "goat", "no notes", "we love", "mother"]
    desire_terms = ["can't wait", "need them back", "renew", "sequel", "bring back", "give us", "season"]

    support = sum(1 for t in support_terms if t in s)
    desire = sum(1 for t in desire_terms if t in s)

    # ultra-simple sentiment heuristics (swap out ASAP)
    neg_terms = ["hate", "awful", "terrible", "worst", "cringe", "disgusting"]
    pos_terms = ["love", "amazing", "incredible", "great", "perfect", "best"]

    pos = sum(1 for t in pos_terms if t in s)
    neg = sum(1 for t in neg_terms if t in s)

    # squash to 0..1
    sentiment_pos = min(1.0, pos / 2.0)
    sentiment_neg = min(1.0, neg / 2.0)

    return {
        "sentiment_pos": sentiment_pos,
        "sentiment_neg": sentiment_neg,
        "support_score": min(1.0, support / 2.0),
        "desire_score": min(1.0, desire / 2.0),
    }


# ---------- Catalog + matching ----------

def build_alias_index(catalog: List[CatalogEntity]) -> Dict[str, List[str]]:
    """
    Returns alias -> [entity_id,...] allowing collisions (TAYLOR).
    """
    idx: Dict[str, List[str]] = {}
    for e in catalog:
        for a in e.aliases + [e.canonical_name]:
            key = normalize(a)
            idx.setdefault(key, []).append(e.entity_id)
    return idx

def find_alias_mentions(sentence: str, alias_index: Dict[str, List[str]]) -> List[Tuple[str, Tuple[int,int]]]:
    """
    Deterministic alias scan. For speed, you will eventually want Aho–Corasick or similar.
    Returns list of (surface, span).
    """
    s_lower = sentence.lower()
    found = []
    for alias_norm in alias_index.keys():
        # crude exact substring match for v1; upgrade to word-boundary and smarter matching
        alias_raw = alias_norm
        pos = s_lower.find(alias_raw)
        if pos != -1:
            found.append((sentence[pos:pos+len(alias_raw)], (pos, pos+len(alias_raw))))
    return found

def generate_candidates(surface: str, alias_index: Dict[str, List[str]], catalog_by_id: Dict[str, CatalogEntity]) -> List[CatalogEntity]:
    # Exact alias match candidates
    key = normalize(surface)
    ids = alias_index.get(key, [])
    cands = [catalog_by_id[i] for i in ids]

    # If none, consider fuzzy candidate generation (omitted for brevity; add token overlap)
    return cands[:MAX_CANDIDATES]


# ---------- Disambiguation scoring ----------

def context_tokens(text: str) -> List[str]:
    # v1: simple tokenization
    return re.findall(r"[a-z0-9']+", normalize(text))

def score_candidate(
    cand: CatalogEntity,
    item: ContentItem,
    sentence: str,
    neighbor_sentences: List[str],
    comention_entity_ids: List[str],
) -> Tuple[float, Dict[str, float]]:
    """
    Returns (score, feature_breakdown)
    """
    # PRIOR
    prior = cand.prior_weight  # assumed 0..1

    # CONTEXT MATCH: overlap with context_hints using local window + title/description
    local = " ".join([item.title, item.description, sentence] + neighbor_sentences)
    local_toks = set(context_tokens(local))
    hint_toks = set(context_tokens(" ".join(cand.context_hints)))
    context = 0.0
    if hint_toks:
        context = len(local_toks & hint_toks) / len(hint_toks)

    # COMENTION GRAPH: if known co-mentions exist; v1 uses simple boost if frequent co-mentions
    # Replace with learned co-mention graph later.
    comention = 1.0 if cand.entity_id in comention_entity_ids else 0.0

    # TYPE FIT: heuristic from sentence patterns (cast/director/trailer/season etc.)
    s = normalize(sentence)
    typefit = 0.5
    if "season" in s or "episode" in s:
        typefit = 1.0 if cand.type in ["SHOW", "FRANCHISE"] else 0.3
    if "starring" in s or "cast" in s:
        typefit = 1.0 if cand.type in ["PERSON", "CHARACTER"] else 0.3

    # SOURCE HEURISTIC: ET titles/description carry strong signal
    source = 1.0 if item.source == "ET_YT" else 0.6

    score = (
        W_PRIOR * prior +
        W_CONTEXT * context +
        W_COMENTION * comention +
        W_TYPEFIT * typefit +
        W_SOURCE * source
    )

    return score, {
        "prior": prior,
        "context": context,
        "comention": comention,
        "typefit": typefit,
        "source": source,
    }


def resolve_mention(
    surface: str,
    item: ContentItem,
    sent_idx: int,
    sentences: List[str],
    candidates: List[CatalogEntity],
    catalog_by_id: Dict[str, CatalogEntity],
    resolved_in_item: List[str], # entity_ids already resolved in this item (for co-mention)
) -> Tuple[Optional[str], float, Dict[str, Any], Optional[UnresolvedMention]]:
    """
    Returns (entity_id or None, confidence, debug, unresolved_obj_if_any)
    """
    sentence = sentences[sent_idx]
    neighbors = []
    if sent_idx - 1 >= 0: neighbors.append(sentences[sent_idx - 1])
    if sent_idx + 1 < len(sentences): neighbors.append(sentences[sent_idx + 1])

    scored = []
    for cand in candidates:
        score, feats = score_candidate(cand, item, sentence, neighbors, resolved_in_item)
        scored.append((cand.entity_id, score, feats))

    scored.sort(key=lambda x: x[1], reverse=True)

    if not scored:
        unresolved = UnresolvedMention(
            item_id=item.item_id,
            sent_idx=sent_idx,
            surface=surface,
            context=" ".join([item.title, item.description, sentence]),
            candidates=[],
        )
        return None, 0.0, {"reason": "no_candidates"}, unresolved

    top_id, top_score, top_feats = scored[0]
    second_score = scored[1][1] if len(scored) > 1 else 0.0
    margin = top_score - second_score

    # Convert raw score to "confidence" (v1: use score directly; later calibrate)
    confidence = max(0.0, min(1.0, top_score))

    if confidence >= RESOLVE_MIN_CONF and margin >= RESOLVE_MIN_MARGIN:
        return top_id, confidence, {
            "chosen": top_id,
            "confidence": confidence,
            "margin": margin,
            "candidates": scored[:MAX_CANDIDATES],
        }, None

    # Unresolved: record candidates with reasons for resolve queue
    unresolved = UnresolvedMention(
        item_id=item.item_id,
        sent_idx=sent_idx,
        surface=surface,
        context=" ".join([item.title, item.description, sentence]),
        candidates=[
            {"entity_id": eid, "score": sc, "features": feats}
            for (eid, sc, feats) in scored[:MAX_CANDIDATES]
        ],
    )
    return None, confidence, {
        "reason": "ambiguous",
        "top": scored[0],
        "second": scored[1] if len(scored) > 1 else None,
        "confidence": confidence,
        "margin": margin,
    }, unresolved


# ---------- PASS A: Explicit mentions ----------

def extract_explicit_mentions(
    item: ContentItem,
    catalog: List[CatalogEntity],
    alias_index: Dict[str, List[str]],
    metrics: RunMetrics,
) -> Tuple[List[Mention], List[UnresolvedMention]]:
    catalog_by_id = {e.entity_id: e for e in catalog}
    sentences = split_sentences(" ".join([item.title, item.description, item.body_text]))
    metrics.total_sentences += len(sentences)

    resolved_mentions: List[Mention] = []
    unresolved: List[UnresolvedMention] = []
    resolved_in_item: List[str] = []

    for i, sent in enumerate(sentences):
        # Find explicit surface forms (alias scan; you can merge NER output here)
        found = find_alias_mentions(sent, alias_index)

        for surface, span in found:
            metrics.total_mentions_explicit += 1

            candidates = generate_candidates(surface, alias_index, catalog_by_id)
            entity_id, conf, debug, unresolved_obj = resolve_mention(
                surface=surface,
                item=item,
                sent_idx=i,
                sentences=sentences,
                candidates=candidates,
                catalog_by_id=catalog_by_id,
                resolved_in_item=resolved_in_item,
            )

            if entity_id is None:
                metrics.unresolved_mentions_explicit += 1
                if metrics.unresolved_mentions_by_source is None:
                    metrics.unresolved_mentions_by_source = {}
                metrics.unresolved_mentions_by_source[item.source] = metrics.unresolved_mentions_by_source.get(item.source, 0) + 1
                unresolved.append(unresolved_obj)
                continue

            metrics.resolved_mentions_explicit += 1
            resolved_in_item.append(entity_id)

            feats = sentiment_support_desire(sent)
            ent = catalog_by_id[entity_id]

            resolved_mentions.append(Mention(
                item_id=item.item_id,
                sent_idx=i,
                span=span,
                surface=surface,
                entity_id=entity_id,
                entity_type=ent.type,
                confidence=conf,
                is_implicit=False,
                weight=1.0,
                features=feats,
                debug=debug,
            ))

    return resolved_mentions, unresolved


# ---------- PASS B: Implicit attribution (pronouns / implied subject) ----------

def choose_primary_focus(
    focus_entity_ids: List[str],
    recency_order: List[str],
) -> Optional[str]:
    """
    Deterministic focus: most recent entity mentioned (recency wins).
    You can enhance with repetition counts later.
    """
    if not focus_entity_ids:
        return None
    # recency_order already ordered by most recent first
    for eid in recency_order:
        if eid in focus_entity_ids:
            return eid
    return focus_entity_ids[-1]

def is_unambiguous_focus(
    primary: str,
    focus_entity_ids: List[str],
    catalog_by_id: Dict[str, CatalogEntity],
) -> bool:
    """
    Unambiguous if no competing entities of the same "core referent class" in focus window.
    Core classes: PERSON, TITLE (SHOW/FILM/FRANCHISE/CHARACTER), ORG/BRAND, COUPLE.
    """
    def core_class(t: str) -> str:
        if t == "PERSON": return "PERSON"
        if t == "COUPLE": return "COUPLE"
        if t in ["SHOW", "FILM", "FRANCHISE", "CHARACTER"]: return "TITLE"
        return "BRAND"

    p_class = core_class(catalog_by_id[primary].type)
    competitors = [
        eid for eid in focus_entity_ids
        if eid != primary and core_class(catalog_by_id[eid].type) == p_class
    ]
    return len(competitors) == 0

def extract_implicit_mentions(
    item: ContentItem,
    explicit_mentions: List[Mention],
    catalog: List[CatalogEntity],
    metrics: RunMetrics,
) -> List[Mention]:
    catalog_by_id = {e.entity_id: e for e in catalog}
    sentences = split_sentences(" ".join([item.title, item.description, item.body_text]))

    # Map sentence -> explicit entity_ids resolved there
    explicit_by_sent: Dict[int, List[str]] = {}
    for m in explicit_mentions:
        explicit_by_sent.setdefault(m.sent_idx, []).append(m.entity_id)

    implicit_mentions: List[Mention] = []

    # Track focus window: last N sentences entity_ids
    # Also track recency order for deterministic primary selection.
    focus_queue: List[List[str]] = []      # list of entity_id lists per sentence (for window)
    recency_order: List[str] = []          # most recent first

    for i, sent in enumerate(sentences):
        explicit_ids = explicit_by_sent.get(i, [])

        # Update focus queue
        focus_queue.append(explicit_ids)
        if len(focus_queue) > WINDOW_N_SENTENCES:
            focus_queue.pop(0)

        # Update recency order (most recent first, unique)
        for eid in explicit_ids:
            if eid in recency_order:
                recency_order.remove(eid)
            recency_order.insert(0, eid)

        # Determine current focus set
        focus_entity_ids = [eid for sub in focus_queue for eid in sub]
        focus_entity_ids = list(dict.fromkeys(focus_entity_ids))  # unique, preserve order

        # If sentence has explicit mentions, we do NOT add implicit mentions for that sentence
        if explicit_ids:
            continue

        # If no explicit, only proceed if pronoun exists (or you can add implied-subject markers)
        if not has_pronoun(sent):
            continue

        primary = choose_primary_focus(focus_entity_ids, recency_order)
        if primary is None:
            metrics.implicit_mentions_ignored_ambiguous += 1
            continue

        if not is_unambiguous_focus(primary, focus_entity_ids, catalog_by_id):
            metrics.implicit_mentions_ignored_ambiguous += 1
            continue

        # Attribute this pronoun sentence to primary focus entity
        metrics.implicit_mentions_attributed += 1
        feats = sentiment_support_desire(sent)
        ent = catalog_by_id[primary]

        implicit_mentions.append(Mention(
            item_id=item.item_id,
            sent_idx=i,
            span=(0, len(sent)),
            surface="__IMPLICIT_PRONOUN__",
            entity_id=primary,
            entity_type=ent.type,
            confidence=1.0,              # attribution confidence; separate from resolve confidence
            is_implicit=True,
            weight=IMPLICIT_WEIGHT,
            features=feats,
            debug={
                "rule": "implicit_pronoun_attribution",
                "primary_focus": primary,
                "focus_set": focus_entity_ids,
                "window_n": WINDOW_N_SENTENCES,
            },
        ))

    return implicit_mentions


# ---------- Orchestrator per ContentItem ----------

def process_item(
    item: ContentItem,
    catalog: List[CatalogEntity],
    alias_index: Dict[str, List[str]],
    metrics: RunMetrics,
) -> Tuple[List[Mention], List[UnresolvedMention]]:
    explicit, unresolved = extract_explicit_mentions(item, catalog, alias_index, metrics)

    # OPTION 1 locked: unresolved do not contribute to scoring.
    # Pronouns/implied subjects can contribute ONLY if anchored to resolved explicit focus.
    implicit = extract_implicit_mentions(item, explicit, catalog, metrics)

    # Return combined mentions for scoring; unresolved separately for resolve queue
    return explicit + implicit, unresolved


# ---------- Daily resolve queue aggregation (impact-weighted) ----------

def compute_item_weight(item: ContentItem) -> float:
    # v1: engagement-weighted importance (tune per source)
    base = 1.0
    if item.source == "ET_YT":
        base = 2.0
    elif item.source == "GDELT_NEWS":
        base = 1.3
    elif item.source == "REDDIT":
        base = 1.2
    elif item.source == "YT":
        base = 1.1
    # Use whatever engagement fields you have
    eng = sum(item.engagement.values()) if item.engagement else 0.0
    return base * (1.0 + 0.2 * log1p(eng))

def build_resolve_queue(
    unresolved: List[UnresolvedMention],
    item_lookup: Dict[str, ContentItem],
) -> List[Dict[str, Any]]:
    agg: Dict[str, Dict[str, Any]] = {}
    for u in unresolved:
        item = item_lookup[u.item_id]
        w = compute_item_weight(item)
        key = normalize(u.surface)
        if key not in agg:
            agg[key] = {
                "surface": u.surface,
                "count": 0,
                "impact": 0.0,
                "examples": [],
            }
        agg[key]["count"] += 1
        agg[key]["impact"] += w
        if len(agg[key]["examples"]) < 3:
            agg[key]["examples"].append({
                "item_id": u.item_id,
                "source": item.source,
                "context": u.context[:280],
                "candidates": u.candidates,
            })

    # Sort by impact desc
    queue = list(agg.values())
    queue.sort(key=lambda x: x["impact"], reverse=True)
    return queue


# ---------- Key v1 guarantees ----------
# 1) Only explicit resolved mentions + unambiguous implicit pronoun attributions affect scoring.
# 2) Unresolved mentions are excluded from scoring and routed to resolve queue.
# 3) Implicit mentions are down-weighted and never create new entities.
# 4) If multiple plausible referents exist in the focus window, pronoun sentence is ignored.
