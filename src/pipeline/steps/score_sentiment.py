"""
Score sentiment and features for mentions.
"""

from typing import List, Dict, Any
import logging

from src.nlp.sentiment.f1_sentiment import analyze_sentiment
from src.nlp.sentiment.f2_support import compute_support_score
from src.nlp.sentiment.f3_desire import compute_desire_score
from src.storage.dao.documents import DocumentDAO

logger = logging.getLogger(__name__)


def score_sentiment(mentions: List[dict]) -> List[dict]:
    """
    Score sentiment (pos/neg), support, and desire for each mention.
    Uses lexicon-based sentiment for v1 (can upgrade to ML model later).
    
    Returns mentions with features added.
    """
    scored_mentions = []
    
    # Load documents for context
    doc_ids = list(set(m.get("doc_id") for m in mentions))
    documents = {}
    
    with DocumentDAO() as doc_dao:
        for doc_id in doc_ids:
            doc = doc_dao.get_document(doc_id)
            if doc:
                documents[doc_id] = doc
    
    for mention in mentions:
        doc_id = mention.get("doc_id")
        doc = documents.get(doc_id)
        
        if not doc:
            # No document context, use surface text
            text = mention.get("surface", "") or mention.get("sentence", "")
        else:
            # Use sentence from document
            sent_idx = mention.get("sent_idx", 0)
            sentences = doc.get("text_all", "").split(".")
            if sent_idx < len(sentences):
                text = sentences[sent_idx]
            else:
                text = mention.get("sentence", "") or mention.get("surface", "")
        
        if not text:
            # No text, default to neutral
            mention["features"] = {
                "sentiment_pos": 0.0,
                "sentiment_neg": 0.0,
                "sentiment_neu": 1.0,
                "support_score": 0.0,
                "desire_score": 0.0,
            }
            scored_mentions.append(mention)
            continue
        
        # Analyze sentiment
        sentiment = analyze_sentiment(text)
        
        # Compute support and desire
        support = compute_support_score(text)
        desire = compute_desire_score(text)
        
        # Add features to mention
        mention["features"] = {
            "sentiment_pos": sentiment["pos"],
            "sentiment_neg": sentiment["neg"],
            "sentiment_neu": sentiment["neu"],
            "support_score": support,
            "desire_score": desire,
        }
        
        scored_mentions.append(mention)
    
    logger.info(f"Scored sentiment for {len(scored_mentions)} mentions")
    return scored_mentions
