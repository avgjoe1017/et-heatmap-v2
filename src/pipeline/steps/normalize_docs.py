"""
Normalize raw source_items into standardized documents.
"""

import hashlib
import uuid
from datetime import datetime
from typing import List, Dict, Any
import logging

from src.nlp.utils.text import clean_text, split_sentences, detect_language

logger = logging.getLogger(__name__)


def normalize_documents(source_items: List[dict]) -> List[dict]:
    """
    Convert source_items to normalized documents.
    Extracts text from URLs (trafilatura for news), cleans, standardizes.
    
    Returns list of documents (normalized).
    """
    documents = []
    
    for item in source_items:
        try:
            # Combine title, description, and body
            title = item.get("title", "") or ""
            description = item.get("description", "") or ""
            
            # For Reddit, description is the post/comment body
            # For news, we might need to extract from URL (skip for now)
            body = description  # For now, use description as body
            
            # Clean text
            text_title = clean_text(title) if title else ""
            text_caption = clean_text(description[:500]) if description else ""  # First 500 chars as caption
            text_body = clean_text(body) if body else ""
            
            # Combine all text for full text extraction
            text_all = " ".join([text_title, text_caption, text_body]).strip()
            
            if not text_all:
                logger.debug(f"Skipping item {item['item_id']}: no text content")
                continue
            
            # Detect language (default to English)
            lang = detect_language(text_all) if text_all else "en"
            
            # Generate document ID
            doc_id = f"doc_{uuid.uuid4().hex[:16]}"
            
            # Generate hash for deduplication (simple hash for now)
            hash_input = text_all.lower()[:1000]  # First 1000 chars
            hash_sim = hashlib.md5(hash_input.encode()).hexdigest()
            
            # Get timestamp (use published_at or current time)
            from datetime import timezone
            doc_timestamp = item.get("published_at")
            if isinstance(doc_timestamp, str):
                try:
                    doc_timestamp = datetime.fromisoformat(doc_timestamp.replace('Z', '+00:00'))
                except:
                    doc_timestamp = datetime.now(timezone.utc)
            elif not isinstance(doc_timestamp, datetime):
                doc_timestamp = datetime.now(timezone.utc)
            
            # Quality flags
            quality_flags = {}
            if not text_title and not text_body:
                quality_flags["empty"] = True
            if len(text_all) < 10:
                quality_flags["too_short"] = True
            
            document = {
                "doc_id": doc_id,
                "item_id": item["item_id"],
                "doc_timestamp": doc_timestamp,
                "lang": lang,
                "text_title": text_title,
                "text_caption": text_caption,
                "text_body": text_body,
                "text_all": text_all,
                "quality_flags": quality_flags,
                "hash_sim": hash_sim,
            }
            
            documents.append(document)
            
        except Exception as e:
            logger.error(f"Failed to normalize document from item {item.get('item_id', 'unknown')}: {e}")
            continue
    
    logger.info(f"Normalized {len(documents)} documents from {len(source_items)} source items")
    return documents
