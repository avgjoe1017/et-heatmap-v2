"""
Ingest Reddit posts and comments.
"""

import praw
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
import logging

from src.common.config import get_reddit_config, load_text_list

logger = logging.getLogger(__name__)


def ingest_reddit(window_start: datetime, window_end: datetime) -> List[dict]:
    """
    Fetch posts and comments from configured subreddits in window.
    
    Returns list of source_items (raw).
    """
    config = get_reddit_config()
    
    if not config.get("enabled"):
        logger.info("Reddit ingestion is disabled in config")
        return []
    
    # Check for credentials
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    username = config.get("username")
    password = config.get("password")
    user_agent = config.get("user_agent", "et-heatmap/0.1.0")
    
    if not client_id or not client_secret:
        logger.warning("Reddit credentials not found (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET). Skipping Reddit ingestion.")
        return []
    
    # Initialize Reddit API
    # Use script app authentication if username/password provided, otherwise use read-only
    try:
        if username and password:
            # Script app authentication (personal script)
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                username=username,
                password=password,
                user_agent=user_agent
            )
            logger.info(f"Reddit authenticated as user: {username}")
        else:
            # Read-only authentication (no login required)
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            logger.info("Reddit initialized in read-only mode")
        
        # Verify connection
        try:
            user = reddit.user.me()
            logger.info(f"Reddit API connection verified. Authenticated as: {user}")
        except Exception:
            logger.info("Reddit API connection verified (read-only mode)")
            
    except Exception as e:
        logger.error(f"Failed to initialize Reddit API: {e}")
        return []
    
    # Load subreddits
    subreddits_file = config.get("subreddits_file", "config/subreddits.txt")
    subreddits = load_text_list(subreddits_file)
    
    if not subreddits:
        logger.warning(f"No subreddits found in {subreddits_file}")
        return []
    
    max_posts = config.get("max_posts_per_subreddit", 100)
    max_comments = config.get("max_comments_per_post", 50)
    
    source_items = []
    
    # Convert datetime to Unix timestamp for Reddit API
    window_start_ts = int(window_start.timestamp())
    window_end_ts = int(window_end.timestamp())
    
    logger.info(f"Ingesting Reddit posts from {len(subreddits)} subreddits between {window_start} and {window_end}")
    
    for subreddit_name in subreddits:
        try:
            subreddit = reddit.subreddit(subreddit_name)
            
            # Fetch new posts in window
            posts = list(subreddit.new(limit=max_posts))
            
            for post in posts:
                # Reddit timestamps are UTC but naive
                post_created = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                
                # Skip if outside window (both are timezone-aware)
                if post_created < window_start or post_created >= window_end:
                    continue
                
                # Create source_item for post
                post_item = {
                    "item_id": f"reddit_post_{post.id}",
                    "source": "REDDIT",
                    "url": f"https://reddit.com{post.permalink}",
                    "published_at": post_created,
                    "title": post.title,
                    "description": post.selftext[:500] if post.selftext else "",  # First 500 chars
                    "author": str(post.author) if post.author else "[deleted]",
                    "engagement": {
                        "score": post.score,
                        "num_comments": post.num_comments,
                        "upvote_ratio": post.upvote_ratio,
                    },
                    "raw_payload": {
                        "subreddit": subreddit_name,
                        "post_id": post.id,
                        "post_type": "post",
                    }
                }
                source_items.append(post_item)
                
                # Fetch top comments for this post
                try:
                    post.comments.replace_more(limit=0)  # Remove "more comments" placeholders
                    comments = post.comments.list()[:max_comments]
                    
                    for comment in comments:
                        if hasattr(comment, "created_utc") and comment.created_utc:
                            # Reddit timestamps are UTC but naive
                            comment_created = datetime.fromtimestamp(comment.created_utc, tz=timezone.utc)
                            
                            # Only include comments in window (both are timezone-aware)
                            if comment_created < window_start or comment_created >= window_end:
                                continue
                            
                            # Skip deleted/removed comments
                            if comment.body in ["[deleted]", "[removed]"]:
                                continue
                            
                            # Create source_item for comment
                            comment_item = {
                                "item_id": f"reddit_comment_{comment.id}",
                                "source": "REDDIT",
                                "url": f"https://reddit.com{comment.permalink}",
                                "published_at": comment_created,
                                "title": f"Comment on: {post.title[:100]}",
                                "description": comment.body[:500] if hasattr(comment, "body") else "",
                                "author": str(comment.author) if hasattr(comment, "author") and comment.author else "[deleted]",
                                "engagement": {
                                    "score": comment.score if hasattr(comment, "score") else 0,
                                },
                                "raw_payload": {
                                    "subreddit": subreddit_name,
                                    "post_id": post.id,
                                    "comment_id": comment.id,
                                    "post_type": "comment",
                                }
                            }
                            source_items.append(comment_item)
                except Exception as e:
                    logger.warning(f"Failed to fetch comments for post {post.id}: {e}")
                    continue
            
            logger.info(f"Ingested {len([i for i in source_items if i['raw_payload']['subreddit'] == subreddit_name])} items from r/{subreddit_name}")
            
        except Exception as e:
            logger.error(f"Failed to ingest from r/{subreddit_name}: {e}")
            continue
    
    logger.info(f"Reddit ingestion complete: {len(source_items)} total items")
    return source_items
