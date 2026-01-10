#!/usr/bin/env python3
"""Test YouTube transcript fetching."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_transcript_api import YouTubeTranscriptApi

video_id = "o_-51c4p-r8"  # First video from test

print(f"Testing transcript fetch for video: {video_id}")
print(f"URL: https://www.youtube.com/watch?v={video_id}")
print()

try:
    # Try English first
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    transcript_text = " ".join([item["text"] for item in transcript_list])
    print(f"[OK] Transcript found!")
    print(f"  Segments: {len(transcript_list)}")
    print(f"  Total length: {len(transcript_text)} characters")
    print(f"  Preview: {transcript_text[:200]}...")
except Exception as e:
    print(f"[ERROR] Failed to fetch transcript: {e}")
    print()
    print("Trying any available language...")
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=None)
        transcript_text = " ".join([item["text"] for item in transcript_list])
        print(f"[OK] Transcript found (non-English)!")
        print(f"  Segments: {len(transcript_list)}")
        print(f"  Total length: {len(transcript_text)} characters")
        print(f"  Preview: {transcript_text[:200]}...")
    except Exception as e2:
        print(f"[ERROR] No transcript available: {e2}")
