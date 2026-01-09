"""
Configuration loading utilities.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration file."""
    file_path = Path(__file__).parent.parent.parent / config_path
    if not file_path.exists():
        return {}
    
    with open(file_path, "r") as f:
        return yaml.safe_load(f) or {}


def load_text_list(file_path: str) -> list:
    """Load text file as list of lines, skipping comments and empty lines."""
    full_path = Path(__file__).parent.parent.parent / file_path
    if not full_path.exists():
        return []
    
    lines = []
    with open(full_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    
    return lines


def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value from environment or config files."""
    # Try environment variable first
    value = os.getenv(key.upper())
    if value:
        return value
    
    # Try sources.yaml
    sources_config = load_yaml_config("config/sources.yaml")
    if key in sources_config.get("sources", {}):
        return sources_config["sources"][key]
    
    return default


def get_reddit_config() -> Dict[str, Any]:
    """Get Reddit configuration."""
    sources_config = load_yaml_config("config/sources.yaml")
    reddit_config = sources_config.get("sources", {}).get("reddit", {})
    
    return {
        "enabled": reddit_config.get("enabled", False),
        "subreddits_file": reddit_config.get("subreddits_file", "config/subreddits.txt"),
        "max_posts_per_subreddit": reddit_config.get("max_posts_per_subreddit", 100),
        "max_comments_per_post": reddit_config.get("max_comments_per_post", 50),
        "client_id": os.getenv("REDDIT_CLIENT_ID", ""),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET", ""),
        "username": os.getenv("REDDIT_USERNAME", ""),
        "password": os.getenv("REDDIT_PASSWORD", ""),
        "user_agent": os.getenv("REDDIT_USER_AGENT", "et-heatmap/0.1.0"),
    }
