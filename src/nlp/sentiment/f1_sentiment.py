"""
Sentiment analysis model wrapper.
Uses cardiffnlp/twitter-roberta-base-sentiment-latest.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_model = None
_tokenizer = None

def _load_model():
    """Load sentiment model on first use."""
    global _model, _tokenizer
    
    if _model is not None:
        return _model, _tokenizer
    
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from transformers import pipeline
        
        model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        logger.info(f"Loading sentiment model: {model_name}")
        
        # Use pipeline for easier inference
        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=model_name,
            tokenizer=model_name,
            return_all_scores=True
        )
        
        logger.info("Sentiment model loaded successfully")
        return _sentiment_pipeline, None
        
    except ImportError:
        logger.warning("transformers not available, falling back to lexicon-based sentiment")
        return None, None
    except Exception as e:
        logger.warning(f"Failed to load sentiment model: {e}, falling back to lexicon-based sentiment")
        return None, None


# Simple sentiment lexicons for fallback
POSITIVE_WORDS = [
    "love", "amazing", "incredible", "great", "perfect", "best", "awesome",
    "fantastic", "brilliant", "excellent", "wonderful", "beautiful", "stunning"
]

NEGATIVE_WORDS = [
    "hate", "awful", "terrible", "worst", "cringe", "disgusting", "bad",
    "horrible", "disappointing", "boring", "stupid", "ridiculous"
]


def analyze_sentiment(text: str, use_ml: bool = True) -> dict:
    """
    Analyze sentiment for a text snippet.
    Returns {pos: float, neg: float, neu: float} in [0, 1].
    
    Uses ML model if available (cardiffnlp/twitter-roberta-base-sentiment-latest),
    falls back to lexicon-based sentiment if model not available.
    """
    if not text:
        return {"pos": 0.0, "neg": 0.0, "neu": 1.0}
    
    # Try ML model first
    if use_ml:
        pipeline_model, _ = _load_model()
        if pipeline_model is not None:
            try:
                # Truncate text if too long (model max length is 512)
                text_truncated = text[:500]
                
                # Run inference
                results = pipeline_model(text_truncated)
                
                # Results format: [{"label": "POSITIVE", "score": 0.95}, ...]
                # Map to our format
                pos_score = 0.0
                neg_score = 0.0
                neu_score = 0.0
                
                for result in results[0]:  # results is list of lists
                    label = result["label"].upper()
                    score = result["score"]
                    
                    if "POSITIVE" in label or "POS" in label:
                        pos_score = score
                    elif "NEGATIVE" in label or "NEG" in label:
                        neg_score = score
                    elif "NEUTRAL" in label or "NEU" in label:
                        neu_score = score
                
                # Normalize to ensure sum to 1.0
                total = pos_score + neg_score + neu_score
                if total > 0:
                    pos_score /= total
                    neg_score /= total
                    neu_score /= total
                
                return {
                    "pos": float(pos_score),
                    "neg": float(neg_score),
                    "neu": float(neu_score)
                }
                
            except Exception as e:
                logger.warning(f"ML sentiment analysis failed: {e}, falling back to lexicon")
                # Fall through to lexicon-based
    
    # Fallback to lexicon-based sentiment
    text_lower = text.lower()
    
    # Count positive and negative words
    pos_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
    neg_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)
    
    # Normalize scores
    total = pos_count + neg_count
    if total == 0:
        return {"pos": 0.0, "neg": 0.0, "neu": 1.0}
    
    pos_score = min(1.0, pos_count / 2.0)  # Saturate at 2 matches
    neg_score = min(1.0, neg_count / 2.0)  # Saturate at 2 matches
    
    # Neutral is inverse of sum of pos+neg
    neu_score = max(0.0, 1.0 - (pos_score + neg_score))
    
    # Normalize to sum to 1.0
    total = pos_score + neg_score + neu_score
    if total > 0:
        pos_score /= total
        neg_score /= total
        neu_score /= total
    
    return {
        "pos": pos_score,
        "neg": neg_score,
        "neu": neu_score
    }
