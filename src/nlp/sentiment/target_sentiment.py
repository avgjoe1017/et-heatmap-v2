"""
Targeted sentiment analysis (optional).
Uses cardiffnlp/twitter-roberta-base-topic-sentiment-latest.
"""

def analyze_target_sentiment(text: str, entity: str) -> dict:
    """
    Analyze sentiment targeted at a specific entity.
    Returns {pos: float, neg: float, neu: float}.
    """
    # TODO: Implement
    # - Load model: cardiffnlp/twitter-roberta-base-topic-sentiment-latest
    # - Run inference with entity context
    # - Return normalized scores
    pass
