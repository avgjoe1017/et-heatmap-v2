"""
Ingest news articles from GDELT.
"""

import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import logging
import time

from src.common.config import load_yaml_config, load_text_list

logger = logging.getLogger(__name__)


def ingest_gdelt_news(window_start: datetime, window_end: datetime) -> List[dict]:
    """
    Fetch news articles from GDELT API for entertainment-related queries.
    Filters by news_domains.txt allowlist.
    
    Returns list of source_items (raw).
    """
    sources_config = load_yaml_config("config/sources.yaml")
    gdelt_config = sources_config.get("sources", {}).get("gdelt_news", {})
    
    if not gdelt_config.get("enabled", False):
        logger.info("GDELT news ingestion is disabled in config")
        return []
    
    max_items = gdelt_config.get("max_items_per_day", 10000)
    domains_file = gdelt_config.get("domains_allowlist_file", "config/news_domains.txt")
    
    # Load allowed domains (normalize: lowercase, remove paths, keep base domain)
    allowed_domains_raw = load_text_list(domains_file)
    allowed_domains = set()
    for domain in allowed_domains_raw:
        # Remove paths, keep base domain
        base_domain = domain.split("/")[0].lower().strip()
        if base_domain:
            allowed_domains.add(base_domain)
    
    if not allowed_domains:
        logger.warning(f"No allowed domains found in {domains_file}. Skipping GDELT ingestion.")
        return []
    
    logger.debug(f"Filtering GDELT articles by {len(allowed_domains)} allowed domains")
    
    source_items = []
    
    # GDELT 2.1 API endpoint
    # Query format: https://api.gdeltproject.org/api/v2/doc/doc?query=QUERY&mode=artlist&format=json
    # For entertainment news, use keywords
    entertainment_keywords = [
        "celebrity", "movie", "film", "TV show", "television", "streaming",
        "entertainment", "Hollywood", "actor", "actress", "director",
        "Netflix", "Disney", "Marvel", "DC", "Star Wars", "film premiere"
    ]
    
    # Build query
    query = " OR ".join([f'"{kw}"' for kw in entertainment_keywords[:5]])  # Limit to 5 keywords
    
    try:
        articles = _fetch_gdelt_articles(query, window_start, window_end, max_items)
        
        # Filter by allowed domains and extract text
        for article in articles:
            domain_raw = article.get("domain", "").lower().strip()
            # Extract base domain (remove www. prefix, keep only domain.com)
            base_domain = domain_raw.replace("www.", "").split("/")[0] if domain_raw else ""
            
            if base_domain not in allowed_domains:
                continue
            
            url = article.get("url", "")
            if not url:
                continue
            
            # Extract article text using trafilatura
            try:
                article_text = _extract_article_text(url)
            except Exception as e:
                logger.debug(f"Failed to extract text from {url}: {e}")
                article_text = article.get("snippet", "") or ""
            
            if not article_text:
                continue
            
            # Parse published date
            published_str = article.get("seendate", "")
            try:
                    # GDELT format: YYYYMMDDHHMMSS or YYYYMMDD
                if len(published_str) >= 8:
                    try:
                        year = int(published_str[0:4])
                        month = int(published_str[4:6])
                        day = int(published_str[6:8])
                        hour = int(published_str[8:10]) if len(published_str) >= 10 else 0
                        minute = int(published_str[10:12]) if len(published_str) >= 12 else 0
                        second = int(published_str[12:14]) if len(published_str) >= 14 else 0
                        published_at = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Failed to parse date {published_str}: {e}")
                        published_at = datetime.now(timezone.utc)
                else:
                    published_at = datetime.now(timezone.utc)
            except Exception as e:
                logger.debug(f"Failed to parse published date: {e}")
                published_at = datetime.now(timezone.utc)
            
            # Skip if outside window
            if published_at < window_start or published_at >= window_end:
                continue
            
            source_item = {
                "item_id": f"gdelt_{uuid.uuid4().hex[:16]}",
                "source": "GDELT",
                "url": url,
                "published_at": published_at,
                "title": article.get("title", "")[:500] or "Untitled",
                "description": article_text[:1000],  # First 1000 chars
                "author": article.get("domain", ""),
                "engagement": {
                    "tone": article.get("tone", 0),
                    "positive_score": article.get("positive", 0),
                    "negative_score": article.get("negative", 0),
                },
                "raw_payload": {
                    "domain": domain,
                    "language": article.get("language", "en"),
                    "source_country": article.get("sourcecountry", ""),
                }
            }
            source_items.append(source_item)
            
            if len(source_items) >= max_items:
                break
            
            # Rate limiting
            time.sleep(0.1)  # 100ms delay between requests
        
        logger.info(f"Ingested {len(source_items)} GDELT news articles")
        return source_items
        
    except Exception as e:
        logger.error(f"Failed to fetch GDELT articles: {e}")
        return []


def _fetch_gdelt_articles(query: str, window_start: datetime, window_end: datetime, 
                          max_results: int = 250) -> List[dict]:
    """Fetch articles from GDELT 2.1 API."""
    import requests
    
    # Format dates for GDELT (YYYYMMDDHHMMSS)
    start_date = window_start.strftime("%Y%m%d%H%M%S")
    end_date = window_end.strftime("%Y%m%d%H%M%S")
    
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "startdatetime": start_date,
        "enddatetime": end_date,
        "maxrecords": min(max_results, 250),  # GDELT limit
    }
    
    headers = {
        "User-Agent": "et-heatmap/0.1.0 (Entertainment Feelings Heatmap)"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        # GDELT API may return JSON or HTML error page
        content_type = response.headers.get("content-type", "").lower()
        if "application/json" not in content_type:
            logger.debug(f"GDELT API returned non-JSON response (content-type: {content_type})")
            # Try to parse anyway
            try:
                data = response.json()
            except:
                logger.warning(f"GDELT API returned non-JSON content. Response preview: {response.text[:200]}")
                return []
        
        data = response.json()
        
        # GDELT returns articles in "articles" key, or sometimes directly as array
        articles = []
        if isinstance(data, dict):
            articles = data.get("articles", [])
        elif isinstance(data, list):
            articles = data
        
        if not articles:
            logger.debug(f"No articles returned from GDELT for query: {query}")
            return []
        
        return articles
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"GDELT API request failed: {e}")
        return []
    except ValueError as e:
        # JSON decode error
        logger.warning(f"GDELT API returned invalid JSON: {e}. Response preview: {response.text[:200] if 'response' in locals() else 'N/A'}")
        return []
    except Exception as e:
        logger.error(f"Failed to parse GDELT response: {e}")
        return []


def _extract_article_text(url: str) -> str:
    """Extract article text using trafilatura."""
    try:
        import trafilatura
        
        downloaded = trafilatura.fetch_url(url, timeout=10)
        if not downloaded:
            return ""
        
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        return text or ""
    except ImportError:
        logger.debug("trafilatura not available, skipping text extraction")
        return ""
    except Exception as e:
        logger.debug(f"trafilatura extraction failed for {url}: {e}")
        return ""
