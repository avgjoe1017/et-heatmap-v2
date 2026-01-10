#!/usr/bin/env python3
"""Test YouTube ingestion with Entertainment Tonight channel."""

import os
import sys
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline.steps.ingest_et_youtube import ingest_et_youtube

def main():
    print("Testing YouTube ingestion for Entertainment Tonight...")
    print(f"API Key present: {'YOUTUBE_API_KEY' in os.environ}")
    
    # Test with last 7 days
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=7)
    window_end = now
    
    print(f"\nFetching videos from {window_start.date()} to {window_end.date()}...")
    
    try:
        items = ingest_et_youtube(window_start, window_end)
        print(f"\n[OK] Found {len(items)} YouTube videos")
        
        if items:
            # Separate videos and comments
            videos = [i for i in items if i.get("raw_payload", {}).get("item_type", "video") != "comment"]
            comments = [i for i in items if i.get("raw_payload", {}).get("item_type") == "comment"]
            
            print(f"\nBreakdown:")
            print(f"  Videos: {len(videos)}")
            print(f"  Comments: {len(comments)}")
            
            print("\nFirst 3 videos with analytics:")
            for i, item in enumerate(videos[:3], 1):
                engagement = item.get("engagement", {})
                print(f"  {i}. {item['title'][:60]}")
                print(f"     URL: {item['url']}")
                print(f"     Published: {item['published_at']}")
                print(f"     Analytics:")
                print(f"       Views: {engagement.get('view_count', 0):,}")
                print(f"       Likes: {engagement.get('like_count', 0):,}")
                print(f"       Comments: {engagement.get('comment_count', 0):,}")
                print(f"     Has transcript: {item['raw_payload'].get('has_transcript', False)}")
                print()
            
            if comments:
                print("\nFirst 3 comments with engagement:")
                for i, item in enumerate(comments[:3], 1):
                    engagement = item.get("engagement", {})
                    print(f"  {i}. {item['title'][:60]}")
                    print(f"     Author: {item.get('author', 'Unknown')}")
                    print(f"     Text: {item.get('description', '')[:80]}...")
                    print(f"     Engagement:")
                    print(f"       Likes: {engagement.get('like_count', 0):,}")
                    print(f"       Replies: {engagement.get('reply_count', 0):,}")
                    print(f"     Published: {item['published_at']}")
                    print()
        else:
            print("\n[WARN] No videos found. This could mean:")
            print("  - No videos published in the time window")
            print("  - API key is invalid")
            print("  - Channel ID is incorrect")
            print("  - API quota exceeded")
        
    except Exception as e:
        print(f"\n[ERROR] YouTube ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
