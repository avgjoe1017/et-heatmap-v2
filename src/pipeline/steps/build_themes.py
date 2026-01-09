"""
Build theme clusters for entity drilldowns using BERTopic and KeyBERT.
"""

import logging
from typing import List, Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)

# Global models (lazy loaded)
_topic_model = None
_keybert_model = None


def _load_topic_models():
    """Load BERTopic and KeyBERT models on first use."""
    global _topic_model, _keybert_model
    
    if _topic_model is not None:
        return _topic_model, _keybert_model
    
    try:
        from bertopic import BERTopic
        from keybert import KeyBERT
        
        logger.info("Loading BERTopic and KeyBERT models...")
        
        # Initialize models
        # BERTopic uses sentence-transformers internally
        _topic_model = BERTopic(
            top_n_words=10,
            min_topic_size=2,  # Minimum mentions per theme
            calculate_probabilities=True,
            verbose=False
        )
        
        # KeyBERT for keyword extraction
        _keybert_model = KeyBERT()
        
        logger.info("Topic models loaded successfully")
        return _topic_model, _keybert_model
        
    except ImportError:
        logger.warning("BERTopic/KeyBERT not available, using simple clustering")
        return None, None
    except Exception as e:
        logger.warning(f"Failed to load topic models: {e}, using simple clustering")
        return None, None


def build_themes(
    mentions: List[dict],
    documents: List[dict],
    entity_metrics: List[dict],
    limit: int = 5
) -> List[dict]:
    """
    Cluster mentions into themes using BERTopic.
    Returns entity_daily_themes records grouped by entity_id.
    """
    if not mentions or not documents:
        return []
    
    # Build lookup maps
    documents_map = {doc["doc_id"]: doc for doc in documents}
    entity_map = {m["entity_id"]: m for m in entity_metrics}
    
    # Group mentions by entity_id
    entity_mentions: Dict[str, List[dict]] = {}
    for mention in mentions:
        entity_id = mention.get("entity_id")
        if not entity_id:
            continue
        entity_mentions.setdefault(entity_id, []).append(mention)
    
    all_themes = []
    
    # Process each entity
    for entity_id, entity_mention_list in entity_mentions.items():
        if entity_id not in entity_map:
            continue
        
        if len(entity_mention_list) < 2:  # Need at least 2 mentions for clustering
            continue
        
        # Extract text snippets from mentions
        texts = []
        mention_sentiments = []
        
        for mention in entity_mention_list:
            doc_id = mention.get("doc_id")
            doc = documents_map.get(doc_id)
            
            if not doc:
                continue
            
            # Get sentence or context
            sent_idx = mention.get("sent_idx", 0)
            text_all = doc.get("text_all", "")
            sentences = text_all.split(".")
            
            if sent_idx < len(sentences):
                text = sentences[sent_idx].strip()
            else:
                text = mention.get("sentence", "") or mention.get("surface", "")
            
            if text and len(text) > 20:  # Minimum length
                texts.append(text)
                
                # Get sentiment for this mention
                features = mention.get("features", {})
                mention_sentiments.append({
                    "pos": features.get("sentiment_pos", 0.0),
                    "neg": features.get("sentiment_neg", 0.0),
                    "neu": features.get("sentiment_neu", 0.0),
                })
        
        if len(texts) < 2:
            continue
        
        # Cluster texts
        themes = _cluster_texts(texts, mention_sentiments, limit)
        
        # Create theme records
        for theme in themes:
            all_themes.append({
                "entity_id": entity_id,
                "theme_id": theme["theme_id"],
                "label": theme["label"],
                "keywords": theme["keywords"],
                "volume": theme["volume"],
                "sentiment_mix": theme["sentiment_mix"],
            })
    
    logger.info(f"Built {len(all_themes)} themes for {len(entity_mentions)} entities")
    return all_themes


def _cluster_texts(texts: List[str], sentiments: List[dict], limit: int = 5) -> List[dict]:
    """Cluster texts into themes using BERTopic or simple grouping."""
    topic_model, keybert_model = _load_topic_models()
    
    if topic_model is None or keybert_model is None:
        # Fallback: simple keyword-based grouping
        return _simple_theme_clustering(texts, sentiments, limit)
    
    try:
        # Fit BERTopic model
        topics, probs = topic_model.fit_transform(texts)
        
        # Get topic info
        topic_info = topic_model.get_topic_info()
        
        themes = []
        
        # Process each topic (excluding outlier topic -1)
        for _, row in topic_info.iterrows():
            topic_id = int(row["Topic"])
            if topic_id == -1:  # Outlier topic
                continue
            
            count = int(row["Count"])
            
            # Get words for this topic
            topic_words = topic_model.get_topic(topic_id)
            if not topic_words:
                continue
            
            # Extract keywords using KeyBERT
            # Combine texts in this topic
            topic_texts = [texts[i] for i, t in enumerate(topics) if t == topic_id]
            if not topic_texts:
                continue
            
            combined_text = " ".join(topic_texts)
            
            # Extract keywords
            try:
                keywords = keybert_model.extract_keywords(
                    combined_text,
                    keyphrase_ngram_range=(1, 2),
                    top_n=5
                )
                keywords_list = [kw[0] for kw in keywords]
            except:
                # Fallback to topic words
                keywords_list = [word[0] for word in topic_words[:5]]
            
            # Compute sentiment mix for this theme
            theme_sentiments = [sentiments[i] for i, t in enumerate(topics) if t == topic_id]
            
            sentiment_pos = sum(s["pos"] for s in theme_sentiments) / max(1, len(theme_sentiments))
            sentiment_neg = sum(s["neg"] for s in theme_sentiments) / max(1, len(theme_sentiments))
            sentiment_neu = sum(s["neu"] for s in theme_sentiments) / max(1, len(theme_sentiments))
            
            # Generate label from keywords
            label = keywords_list[0] if keywords_list else f"Theme {topic_id}"
            
            themes.append({
                "theme_id": f"theme_{topic_id}_{uuid.uuid4().hex[:8]}",
                "label": label[:100],
                "keywords": keywords_list[:10],
                "volume": count,
                "sentiment_mix": {
                    "pos": float(sentiment_pos),
                    "neg": float(sentiment_neg),
                    "neu": float(sentiment_neu),
                }
            })
        
        # Sort by volume and take top N
        themes.sort(key=lambda x: x["volume"], reverse=True)
        return themes[:limit]
        
    except Exception as e:
        logger.warning(f"BERTopic clustering failed: {e}, falling back to simple clustering")
        return _simple_theme_clustering(texts, sentiments, limit)


def _simple_theme_clustering(texts: List[str], sentiments: List[dict], limit: int = 5) -> List[dict]:
    """Simple keyword-based theme clustering fallback."""
    import re
    from collections import Counter
    
    # Extract common words/phrases
    all_words = []
    for text in texts:
        # Simple word extraction
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter stop words (basic list)
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = [w for w in words if len(w) > 3 and w not in stop_words]
        all_words.extend(words)
    
    # Count word frequencies
    word_counts = Counter(all_words)
    common_words = [word for word, count in word_counts.most_common(10) if count >= 2]
    
    if not common_words:
        return []
    
    # Create a single theme from common words
    sentiment_pos = sum(s["pos"] for s in sentiments) / max(1, len(sentiments))
    sentiment_neg = sum(s["neg"] for s in sentiments) / max(1, len(sentiments))
    sentiment_neu = sum(s["neu"] for s in sentiments) / max(1, len(sentiments))
    
    return [{
        "theme_id": f"theme_simple_{uuid.uuid4().hex[:8]}",
        "label": common_words[0].title(),
        "keywords": common_words[:5],
        "volume": len(texts),
        "sentiment_mix": {
            "pos": float(sentiment_pos),
            "neg": float(sentiment_neg),
            "neu": float(sentiment_neu),
        }
    }]
