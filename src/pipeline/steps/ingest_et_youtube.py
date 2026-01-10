"""
Ingest ET YouTube channel videos and transcripts.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

from src.common.config import load_yaml_config, get_config
from src.common.youtube_quota import get_quota_tracker, track_youtube_api_call

logger = logging.getLogger(__name__)


def ingest_et_youtube(window_start: datetime, window_end: datetime) -> List[dict]:
    """
    Fetch ET YouTube channel videos published in window.
    Extract transcripts using youtube-transcript-api.
    
    Returns list of source_items (raw).
    """
    sources_config = load_yaml_config("config/sources.yaml")
    yt_config = sources_config.get("sources", {}).get("et_youtube", {})
    
    if not yt_config.get("enabled", False):
        logger.info("ET YouTube ingestion is disabled in config")
        return []
    
    channel_id = yt_config.get("channel_id") or os.getenv("YOUTUBE_CHANNEL_ID", "")
    if not channel_id:
        logger.warning("YouTube channel ID not configured (YOUTUBE_CHANNEL_ID or config/sources.yaml). Skipping ET YouTube ingestion.")
        return []
    
    fetch_transcripts = yt_config.get("fetch_transcripts", True)
    
    source_items = []
    
    # Try to use YouTube Data API v3 if available
    api_key = os.getenv("YOUTUBE_API_KEY", "")
    
    if api_key:
        try:
            source_items = _fetch_via_api(channel_id, window_start, window_end, api_key, fetch_transcripts, yt_config)
            if source_items:
                video_count = len([i for i in source_items if i.get("raw_payload", {}).get("item_type", "video") != "comment"])
                comment_count = len([i for i in source_items if i.get("raw_payload", {}).get("item_type") == "comment"])
                logger.info(f"Ingested {video_count} YouTube videos and {comment_count} comments via API")
                return source_items
        except Exception as e:
            logger.warning(f"YouTube Data API failed: {e}. Falling back to manual video IDs.")
    
    # Fallback: use manual video IDs from config (if provided)
    video_ids = yt_config.get("video_ids", [])
    if video_ids:
        try:
            source_items = _fetch_manual_videos(video_ids, window_start, window_end, fetch_transcripts)
            logger.info(f"Ingested {len(source_items)} YouTube videos from manual list")
            return source_items
        except Exception as e:
            logger.error(f"Failed to fetch manual YouTube videos: {e}")
            return []
    
    logger.warning("No YouTube API key or manual video IDs configured. Skipping ET YouTube ingestion.")
    return []


def _fetch_via_api(channel_id: str, window_start: datetime, window_end: datetime,
                   api_key: str, fetch_transcripts: bool, yt_config: dict = None) -> List[dict]:
    """Fetch videos using YouTube Data API v3."""
    import requests

    source_items = []
    if yt_config is None:
        yt_config = {}

    # Get quota tracker
    quota_tracker = get_quota_tracker()

    # Log initial quota status
    status = quota_tracker.get_status()
    logger.info(f"YouTube API quota: {status['usage']}/{status['limit']} units ({status['percentage']:.1%})")
    
    # Convert channel ID to uploads playlist ID
    # YouTube channel uploads playlist ID is: UU{channel_id[2:]}
    uploads_playlist_id = None
    
    if channel_id.startswith("UC"):
        # Direct channel ID: convert to uploads playlist
        uploads_playlist_id = "UU" + channel_id[2:]
    elif channel_id.startswith("@") or not channel_id.startswith("UC"):
        # Handle channel username/handle
        # First, get channel ID from username
        search_url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            "part": "contentDetails",
            "forUsername": channel_id.lstrip("@") if channel_id.startswith("@") else channel_id,
            "key": api_key
        }
        response = requests.get(search_url, params=params, timeout=10)
        track_youtube_api_call("channel")  # Track channel lookup
        if response.status_code != 200:
            # Try with channel ID directly
            params = {
                "part": "contentDetails",
                "id": channel_id,
                "key": api_key
            }
            response = requests.get(search_url, params=params, timeout=10)
            track_youtube_api_call("channel")  # Track retry
        
        if response.status_code != 200:
            # Try with channel ID directly instead
            params = {
                "part": "contentDetails",
                "id": channel_id,
                "key": api_key
            }
            response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"YouTube API error: {response.status_code} - {response.text}")
        
        data = response.json()
        if not data.get("items"):
            raise Exception(f"Channel not found: {channel_id}")
        
        uploads_playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    if not uploads_playlist_id:
        raise Exception(f"Could not determine uploads playlist for channel: {channel_id}")
    
    # Fetch videos from uploads playlist
    playlist_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    page_token = None
    
    while True:
        params = {
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,
            "key": api_key
        }
        
        if page_token:
            params["pageToken"] = page_token
        
        response = requests.get(playlist_url, params=params, timeout=10)
        track_youtube_api_call("playlist_items")  # Track playlist fetch

        if response.status_code != 200:
            raise Exception(f"YouTube API error: {response.status_code} - {response.text}")

        data = response.json()
        
        for item in data.get("items", []):
            snippet = item["snippet"]
            video_id = snippet["resourceId"]["videoId"]
            published_at_str = snippet["publishedAt"]
            
            # Parse published time (ISO 8601 format)
            published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
            
            # Skip if outside window
            if published_at < window_start or published_at >= window_end:
                continue
            
            # Get video details
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            title = snippet.get("title", "")
            description = snippet.get("description", "")[:500]  # First 500 chars
            
            # Get video statistics (separate API call)
            view_count = 0
            like_count = 0
            comment_count = 0
            try:
                stats_url = "https://www.googleapis.com/youtube/v3/videos"
                stats_params = {
                    "part": "statistics",
                    "id": video_id,
                    "key": api_key
                }
                stats_response = requests.get(stats_url, params=stats_params, timeout=10)
                track_youtube_api_call("video")  # Track video stats fetch

                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    if stats_data.get("items"):
                        stats = stats_data["items"][0]["statistics"]
                        view_count = int(stats.get("viewCount", 0))
                        like_count = int(stats.get("likeCount", 0))
                        comment_count = int(stats.get("commentCount", 0))
            except Exception as e:
                logger.debug(f"Failed to fetch stats for video {video_id}: {e}")
            
            # Fetch transcript if enabled
            transcript_text = ""
            if fetch_transcripts:
                transcript_text = _fetch_transcript(video_id)
            
            # Combine description and transcript
            full_text = description
            if transcript_text:
                full_text = f"{description}\n\n{transcript_text}" if description else transcript_text
            
            source_item = {
                "item_id": f"youtube_{video_id}",
                "source": "YOUTUBE",
                "url": video_url,
                "published_at": published_at,
                "title": title,
                "description": full_text[:1000],  # Limit to 1000 chars
                "author": snippet.get("channelTitle", ""),
                "engagement": {
                    "view_count": view_count,
                    "like_count": like_count,
                    "comment_count": comment_count,
                },
                "raw_payload": {
                    "channel_id": channel_id,
                    "video_id": video_id,
                    "playlist_id": uploads_playlist_id,
                    "has_transcript": bool(transcript_text),
                }
            }
            source_items.append(source_item)
            
            # Fetch comments if enabled (pass title for comment items)
            if yt_config.get("fetch_comments", False):
                try:
                    max_comments_per_video = yt_config.get("max_comments_per_video", 50)
                    comments = _fetch_video_comments(video_id, api_key, window_start, window_end, max_comments=max_comments_per_video, title=title)
                    source_items.extend(comments)
                except Exception as e:
                    logger.debug(f"Failed to fetch comments for video {video_id}: {e}")
        
        # Check for next page
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    
    return source_items


def _fetch_manual_videos(video_ids: List[str], window_start: datetime, window_end: datetime, 
                         fetch_transcripts: bool) -> List[dict]:
    """Fetch videos using manual video ID list."""
    source_items = []
    
    for video_id in video_ids:
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Fetch transcript
            transcript_text = ""
            if fetch_transcripts:
                transcript_text = _fetch_transcript(video_id)
            
            # Without API, we can't get published date or title
            # Use current time as fallback (or skip if outside window check)
            # For now, create item with minimal data
            source_item = {
                "item_id": f"youtube_{video_id}",
                "source": "YOUTUBE",
                "url": video_url,
                "published_at": datetime.now(timezone.utc),  # Fallback
                "title": f"YouTube Video {video_id}",
                "description": transcript_text[:1000] if transcript_text else "",
                "author": "ET YouTube",
                "engagement": {},
                "raw_payload": {
                    "video_id": video_id,
                    "has_transcript": bool(transcript_text),
                    "manual_fetch": True,
                }
            }
            source_items.append(source_item)
        except Exception as e:
            logger.warning(f"Failed to fetch video {video_id}: {e}")
            continue
    
    return source_items


def _fetch_video_comments(video_id: str, api_key: str, window_start: datetime, window_end: datetime, 
                          max_comments: int = 50, title: str = "") -> List[dict]:
    """Fetch top-level comments for a YouTube video."""
    import requests
    import time
    
    comments = []
    page_token = None
    
    try:
        while len(comments) < max_comments:
            # Fetch comment threads
            comments_url = "https://www.googleapis.com/youtube/v3/commentThreads"
            params = {
                "part": "snippet,replies",
                "videoId": video_id,
                "maxResults": min(100, max_comments - len(comments)),  # YouTube max is 100
                "order": "relevance",  # Top comments first
                "key": api_key
            }
            
            if page_token:
                params["pageToken"] = page_token
            
            response = requests.get(comments_url, params=params, timeout=10)
            track_youtube_api_call("comment_threads")  # Track comments fetch

            if response.status_code != 200:
                logger.debug(f"YouTube comments API error for {video_id}: {response.status_code}")
                break
            
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                break
            
            for item in items:
                if len(comments) >= max_comments:
                    break
                
                top_level_comment = item["snippet"]["topLevelComment"]["snippet"]
                comment_id = item["snippet"]["topLevelComment"]["id"]
                comment_text = top_level_comment.get("textDisplay", "") or top_level_comment.get("textOriginal", "")
                
                # Parse published date
                published_str = top_level_comment.get("publishedAt", "")
                try:
                    published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                except:
                    published_at = datetime.now(timezone.utc)
                
                # Skip if outside window
                if published_at < window_start or published_at >= window_end:
                    continue
                
                # Skip deleted/removed comments
                if not comment_text or comment_text.strip() == "":
                    continue
                
                comment_item = {
                    "item_id": f"youtube_comment_{comment_id}",
                    "source": "YOUTUBE",
                    "url": f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}",
                    "published_at": published_at,
                    "title": f"Comment on: {title[:100]}" if title else f"Comment on video {video_id}",
                    "description": comment_text[:500],  # First 500 chars
                    "author": top_level_comment.get("authorDisplayName", "[deleted]"),
                    "engagement": {
                        "like_count": int(top_level_comment.get("likeCount", 0)),
                        "reply_count": int(item["snippet"].get("totalReplyCount", 0)),
                    },
                    "raw_payload": {
                        "video_id": video_id,
                        "comment_id": comment_id,
                        "item_type": "comment",
                        "parent_type": "video",
                    }
                }
                comments.append(comment_item)
            
            # Check for next page
            page_token = data.get("nextPageToken")
            if not page_token:
                break
            
            # Rate limiting (YouTube allows 10000 units/day, each commentThreads call is ~1 unit)
            time.sleep(0.1)  # 100ms delay between pages
        
        return comments
        
    except Exception as e:
        logger.warning(f"Error fetching comments for video {video_id}: {e}")
        return []


def _fetch_transcript(video_id: str) -> str:
    """Fetch transcript for a YouTube video using youtube-transcript-api."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Try to get transcript (prefer English, but accept any language)
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        except:
            # If English not available, try any available language
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=None)
        
        # Combine all transcript segments
        transcript_text = " ".join([item["text"] for item in transcript_list])
        return transcript_text
    except Exception as e:
        logger.debug(f"Failed to fetch transcript for {video_id}: {e}")
        return ""
