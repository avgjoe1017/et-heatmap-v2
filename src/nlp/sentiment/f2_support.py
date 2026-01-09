"""
Support lexicon and pattern matching.
"""

import re

SUPPORT_LEXICON = [
    "iconic", "legend", "queen", "king", "goat", "no notes", "we love", "mother",
    "slayed", "ate", "served", "perfection", "flawless", "immaculate"
]

def compute_support_score(text: str) -> float:
    """
    Compute support score [0, 1] from lexicon matching.
    """
    if not text:
        return 0.0
    
    # Normalize text
    text_lower = text.lower()
    
    # Count matches
    matches = sum(1 for term in SUPPORT_LEXICON if term in text_lower)
    
    # Normalize to 0..1 (saturate at 3 matches)
    return min(1.0, matches / 3.0)
