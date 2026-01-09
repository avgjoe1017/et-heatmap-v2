"""
Extract entity mentions from documents (NER + alias matching).
"""

import re
from typing import List, Dict, Tuple, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def extract_mentions(documents: List[dict], catalog: List[dict]) -> Tuple[List[dict], List[dict]]:
    """
    Extract mentions using alias matching.
    
    For v1, uses simple alias matching. Can be enhanced with spaCy NER later.
    
    Returns (mentions, unresolved_mentions).
    Mentions are pre-resolution (surface strings with candidates).
    Resolution happens in entity_resolver.py
    """
    mentions = []
    unresolved_mentions = []
    
    # Build alias index (alias -> list of entity_ids that have this alias)
    alias_index = {}
    entity_lookup = {e["entity_id"]: e for e in catalog}
    
    for entity in catalog:
        entity_id = entity["entity_id"]
        # Add canonical name
        canonical_norm = _normalize(entity.get("canonical_name", ""))
        if canonical_norm:
            alias_index.setdefault(canonical_norm, []).append(entity_id)
        
        # Add aliases
        for alias in entity.get("aliases", []):
            alias_norm = _normalize(alias)
            if alias_norm:
                alias_index.setdefault(alias_norm, []).append(entity_id)
    
    logger.info(f"Built alias index with {len(alias_index)} aliases for {len(catalog)} entities")
    
    # Extract mentions from each document
    for doc in documents:
        text = doc.get("text_all", "")
        if not text:
            continue
        
        # Split into sentences for better context
        from src.nlp.utils.text import split_sentences
        sentences = split_sentences(text)
        
        for sent_idx, sentence in enumerate(sentences):
            # Find all alias matches in this sentence
            found_aliases = _find_alias_matches(sentence, alias_index)
            
            for alias_norm, entity_ids in found_aliases.items():
                # Create mention for each candidate entity
                # Resolution will pick the best candidate
                for entity_id in entity_ids:
                    mention = {
                        "surface": alias_norm,  # Will be resolved to actual surface text
                        "sent_idx": sent_idx,
                        "span_start": sentence.lower().find(alias_norm),
                        "span_end": sentence.lower().find(alias_norm) + len(alias_norm),
                        "doc_id": doc["doc_id"],
                        "entity_candidates": entity_ids,  # Multiple candidates possible
                        "sentence": sentence,
                        "context": sentence[:200],  # First 200 chars for context
                    }
                    
                    # If only one candidate, it's likely resolved
                    # If multiple, it's ambiguous and needs resolution
                    if len(entity_ids) == 1:
                        mentions.append(mention)
                    else:
                        # Ambiguous - add to unresolved for now
                        # Actually, let's add to mentions with all candidates
                        # Resolution step will handle disambiguation
                        mentions.append(mention)
    
    logger.info(f"Extracted {len(mentions)} mentions from {len(documents)} documents")
    return mentions, unresolved_mentions


def _normalize(text: str) -> str:
    """Normalize text for matching."""
    if not text:
        return ""
    # Lowercase and remove punctuation
    text = text.lower()
    # Remove common punctuation but keep word boundaries
    text = re.sub(r'[^\w\s]', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _find_alias_matches(text: str, alias_index: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Find all alias matches in text.
    Returns dict of alias_norm -> list of entity_ids.
    """
    text_lower = text.lower()
    found = {}
    
    # Simple substring matching
    # For production, use FlashText or pyahocorasick for better performance
    for alias_norm, entity_ids in alias_index.items():
        # Only match whole words (simple word boundary check)
        pattern = r'\b' + re.escape(alias_norm) + r'\b'
        if re.search(pattern, text_lower):
            found[alias_norm] = entity_ids
    
    return found
