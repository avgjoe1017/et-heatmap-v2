"""
Shared data models and types.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

# Entity types
ENTITY_TYPES = [
    "PERSON", "SHOW", "FILM", "FRANCHISE", 
    "NETWORK_STREAMER", "COUPLE", "BRAND", "CHARACTER"
]

# Source types
SOURCE_TYPES = [
    "ET_YT", "GDELT_NEWS", "REDDIT", "YT",
    "GOOGLE_TRENDS", "WIKIPEDIA_PAGEVIEWS",
    "TWITTER", "TIKTOK", "INSTAGRAM"
]

# Run statuses
RUN_STATUS = ["SUCCESS", "FAILED", "PARTIAL", "RUNNING"]

@dataclass
class Entity:
    entity_id: str
    entity_key: str
    canonical_name: str
    entity_type: str
    is_pinned: bool = False
    is_active: bool = True
    external_ids: Dict[str, str] = None
    context_hints: List[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class SourceItem:
    item_id: str
    source: str
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None
    engagement: Dict[str, float] = None
