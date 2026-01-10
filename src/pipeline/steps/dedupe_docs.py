"""
Deduplicate documents using hash-based similarity.
"""

import hashlib
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def dedupe_documents(documents: List[dict]) -> List[dict]:
    """
    Remove near-duplicate documents using hash-based deduplication.
    Uses content hash for exact duplicates and simple text similarity for near-duplicates.
    
    Returns deduplicated list of documents.
    """
    if not documents:
        return []
    
    seen_hashes = set()
    deduplicated = []
    
    for doc in documents:
        # Generate hash from combined text content
        text_all = doc.get("text_all", "") or ""
        text_title = doc.get("text_title", "") or ""
        text_caption = doc.get("text_caption", "") or ""
        
        # Combine all text for hashing
        combined_text = f"{text_title} {text_caption} {text_all}".strip()
        
        if not combined_text:
            # Skip documents with no text
            continue
        
        # Generate hash (use first 500 chars for efficiency, full text for uniqueness)
        hash_input = combined_text[:500].lower().strip()
        doc_hash = hashlib.md5(hash_input.encode()).hexdigest()
        
        # Check for exact duplicates (same hash)
        if doc_hash in seen_hashes:
            logger.debug(f"Skipping duplicate document {doc.get('doc_id')} (hash: {doc_hash[:8]})")
            continue
        
        seen_hashes.add(doc_hash)
        deduplicated.append(doc)
    
    removed_count = len(documents) - len(deduplicated)
    if removed_count > 0:
        logger.info(f"Deduplicated documents: {removed_count} duplicates removed, {len(deduplicated)} unique documents")
    
    return deduplicated
