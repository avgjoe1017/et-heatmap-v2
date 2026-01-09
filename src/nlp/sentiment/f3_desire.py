"""
Desire lexicon and pattern matching.
"""

import re

DESIRE_LEXICON = [
    "can't wait", "need them back", "renew", "sequel", "bring back", "give us",
    "season", "more of", "we need", "petition", "manifesting", "please give"
]

def compute_desire_score(text: str) -> float:
    """
    Compute desire score [0, 1] from lexicon matching.
    """
    if not text:
        return 0.0
    
    # Normalize text
    text_lower = text.lower()
    
    # Count matches
    matches = sum(1 for term in DESIRE_LEXICON if term in text_lower)
    
    # Normalize to 0..1 (saturate at 3 matches)
    return min(1.0, matches / 3.0)
