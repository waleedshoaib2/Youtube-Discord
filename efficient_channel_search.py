#!/usr/bin/env python3
"""
Efficient Channel Search - Find channels with minimal API usage
"""

from youtube_monitor import YouTubeMonitor
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def efficient_channel_search():
    """Search for channels efficiently"""
    print("🔍 EFFICIENT CHANNEL SEARCH")
    print("=" * 50)
    
    monitor = YouTubeMonitor()
    
    # Try to get the channel ID directly from the handle
    print("🔍 Trying direct channel lookup...")
    
    # The real channel handle is @Requestedreads
    # Let's try to get it directly
    handle = "Requestedreads"
    
    try:
        # Try to search for the exact handle
        def make_request():
            return monitor.youtube.search().list(
                part='snippet',
                q=f"@{handle}",
                type='channel',
                maxResults=1  # Only get 1 result to save quota
            ).execute()
            
        result = monitor._api_request_with_retry(make_request)
        monitor.add_quota_usage(100)  # Search is expensive
        
        if result['items']:
            channel_id = result['items'][0]['snippet']['channelId']
            title = result['items'][0]['snippet']['title']
            
            print(f"✅ Found channel: {title}")
            print(f"Channel ID: {channel_id}")
            
            # Get full info
            full_info = monitor.get_channel_info(channel_id)
            if full_info:
                print(f"Subscribers: {full_info['subscriber_count']:,}")
                print(f"Videos: {full_info['video_count']:,}")
                
                if full_info['subscriber_count'] > 800000:
                    print("🎯 THIS IS THE REAL REQUESTEDREADS!")
                else:
                    print("❌ This is not the real channel (wrong subscriber count)")
        else:
            print(f"❌ No channel found for @{handle}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Alternative: Try to find the channel ID manually
    print(f"\n🔍 Manual channel ID approach")
    print("-" * 40)
    
    print("To find the real RequestedReads channel ID:")
    print("1. Go to: https://youtube.com/@Requestedreads")
    print("2. Look at the URL - it should show the channel ID")
    print("3. The channel ID will be in the format: UCxxxxxxxxxxxxxxxxxxxx")
    print("4. Add it directly with: /addchannel <channel_id>")
    
    print(f"\n🔍 Or try these known channel IDs:")
    print("-" * 40)
    
    # Try some common patterns for the channel ID
    # These are guesses based on the channel name
    possible_ids = [
        "UCRequestedreads",  # This won't work, but shows the pattern
        "UCxxxxxxxxxxxxxxxxxxxx"  # Placeholder
    ]
    
    print("The real channel ID should be 24 characters starting with 'UC'")
    print("You can find it by:")
    print("- Going to the channel page")
    print("- Looking at the URL")
    print("- Or checking the page source for 'channelId'")
    
    monitor.close()
    print("\n" + "=" * 50)
    print("✅ Efficient search complete!")

if __name__ == "__main__":
    efficient_channel_search() 