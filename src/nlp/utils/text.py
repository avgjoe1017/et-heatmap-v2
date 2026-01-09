"""
Text processing utilities: cleaning, sentence splitting, language detection.
"""

import re
from typing import List

def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters (but keep newlines for now)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # Normalize unicode quotes and dashes
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u2013', '-').replace('\u2014', '--')
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    Simple regex-based sentence splitter.
    For production, consider using spaCy or nltk.
    """
    if not text:
        return []
    
    # Simple sentence splitting on period, exclamation, question mark
    # Followed by space or newline and capital letter
    pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    sentences = re.split(pattern, text)
    
    # Clean up sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences

def detect_language(text: str) -> str:
    """
    Detect language (default: 'en').
    For now, simple heuristic - assume English.
    In production, use langdetect or similar.
    """
    if not text:
        return "en"
    
    # Simple heuristic: check for common English words
    # For production, use langdetect library
    text_lower = text.lower()
    common_en_words = ['the', 'and', 'is', 'are', 'was', 'were', 'a', 'an']
    
    if any(word in text_lower for word in common_en_words):
        return "en"
    
    # Default to English for now
    return "en"
