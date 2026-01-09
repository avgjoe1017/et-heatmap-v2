"""
Quick test script to verify Reddit API credentials and connection.
"""

import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def test_reddit_connection():
    """Test Reddit API connection and credentials."""
    print("Testing Reddit API connection...\n")
    
    # Check environment variables
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    username = os.getenv("REDDIT_USERNAME")
    password = os.getenv("REDDIT_PASSWORD")
    user_agent = os.getenv("REDDIT_USER_AGENT", "et-heatmap/0.1.0")
    
    print(f"Client ID: {'[OK] Set' if client_id else '[X] Missing'}")
    print(f"Client Secret: {'[OK] Set' if client_secret else '[X] Missing'}")
    print(f"Username: {'[OK] Set' if username else '[X] Missing (optional for read-only)'}")
    print(f"Password: {'[OK] Set' if password else '[X] Missing (optional for read-only)'}")
    print(f"User Agent: {user_agent}\n")
    
    if not client_id or not client_secret:
        print("[ERROR] Missing required credentials (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)")
        print("   See SETUP_REDDIT.md for setup instructions")
        return False
    
    # Test PRAW connection
    try:
        import praw
        
        if username and password:
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                username=username,
                password=password,
                user_agent=user_agent
            )
            print("[OK] Reddit API initialized with script app authentication")
        else:
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            print("[OK] Reddit API initialized in read-only mode")
        
        # Verify connection by getting user info
        try:
            user = reddit.user.me()
            print(f"[OK] Authenticated as: {user}")
        except Exception:
            print("[OK] Connected (read-only mode, no user authentication)")
        
        # Test fetching from a subreddit
        print("\nTesting subreddit access...")
        test_subreddit = reddit.subreddit("python")
        post = next(test_subreddit.new(limit=1))
        print(f"[OK] Successfully fetched post from r/python: '{post.title[:50]}...'")
        
        print("\n[SUCCESS] Reddit API connection successful!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Reddit API connection failed: {e}")
        print("\nTroubleshooting:")
        print("- Check your credentials in .env file")
        print("- Verify your Reddit app is configured as 'script' type")
        print("- See SETUP_REDDIT.md for detailed setup instructions")
        return False

if __name__ == "__main__":
    success = test_reddit_connection()
    exit(0 if success else 1)
