#!/usr/bin/env python3
"""
Test Channel ID - Check if the provided channel ID is the real RequestedReads
"""

from youtube_monitor import YouTubeMonitor
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_channel_id():
    """Test the provided channel ID"""
    print("🔍 TESTING CHANNEL ID")
    print("=" * 50)
    
    monitor = YouTubeMonitor()
    
    # Test the provided channel ID
    channel_id = "UCc0nOJerxC8JHf7sg3CK3Vg"
    
    print(f"🔍 Testing channel ID: {channel_id}")
    print("-" * 40)
    
    try:
        # Get channel info directly
        channel_info = monitor.get_channel_info(channel_id)
        
        if channel_info:
            print(f"✅ Channel found!")
            print(f"Title: {channel_info['title']}")
            print(f"Channel ID: {channel_info['channel_id']}")
            print(f"Subscribers: {channel_info['subscriber_count']:,}")
            print(f"Videos: {channel_info['video_count']:,}")
            print(f"Description: {channel_info['description'][:100]}...")
            
            # Check if this is the real RequestedReads
            if channel_info['subscriber_count'] > 800000:
                print("🎯 THIS IS THE REAL REQUESTEDREADS! (842K+ subscribers)")
            elif channel_info['subscriber_count'] > 100000:
                print("⭐ Large channel, but not the real one")
            else:
                print("❌ Small channel, not the real RequestedReads")
                
            print(f"\n📊 Channel Details:")
            print(f"   - Subscriber count: {channel_info['subscriber_count']:,}")
            print(f"   - Video count: {channel_info['video_count']:,}")
            print(f"   - Thumbnail: {channel_info['thumbnail_url']}")
            print(f"   - Upload playlist: {channel_info['upload_playlist_id']}")
            
        else:
            print(f"❌ Channel not found or error occurred")
            
    except Exception as e:
        print(f"❌ Error testing channel ID: {e}")
    
    monitor.close()
    print("\n" + "=" * 50)
    print("✅ Channel ID test complete!")

if __name__ == "__main__":
    test_channel_id() 