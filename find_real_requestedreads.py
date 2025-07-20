#!/usr/bin/env python3
"""
Find Real RequestedReads - Search for the actual channel with 842K subscribers
"""

from youtube_monitor import YouTubeMonitor
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_real_requestedreads():
    """Find the real RequestedReads channel with 842K subscribers"""
    print("🔍 FINDING REAL REQUESTEDREADS")
    print("=" * 50)
    
    monitor = YouTubeMonitor()
    
    # Try different search strategies with lower costs
    search_queries = [
        "RequestedReads",
        "Requested Reads", 
        "Requestedreads"
    ]
    
    for query in search_queries:
        print(f"\n🔍 Searching: '{query}'")
        print("-" * 40)
        
        try:
            # Search for channels with this query - use fewer results to save quota
            def make_request():
                return monitor.youtube.search().list(
                    part='snippet',
                    q=query,
                    type='channel',
                    maxResults=5,  # Reduced from 10 to save quota
                    order='relevance'
                ).execute()
                
            result = monitor._api_request_with_retry(make_request)
            monitor.add_quota_usage(100)  # Search is expensive, but we need it
            
            if result['items']:
                print(f"Found {len(result['items'])} channels:")
                for i, item in enumerate(result['items'], 1):
                    channel_id = item['snippet']['channelId']
                    title = item['snippet']['title']
                    description = item['snippet'].get('description', '')[:100]
                    
                    print(f"  {i}. {title}")
                    print(f"     ID: {channel_id}")
                    print(f"     Description: {description}...")
                    
                    # Get full channel info
                    full_info = monitor.get_channel_info(channel_id)
                    if full_info:
                        subscribers = full_info['subscriber_count']
                        videos = full_info['video_count']
                        print(f"     Subscribers: {subscribers:,}")
                        print(f"     Videos: {videos:,}")
                        
                        # Check if this is the real one
                        if subscribers > 800000:  # Close to 842K
                            print(f"     🎯 POTENTIAL MATCH! (Close to 842K)")
                        elif subscribers > 100000:  # Significant channel
                            print(f"     ⭐ Large channel ({subscribers:,} subs)")
                        print()
            else:
                print(f"❌ No channels found for '{query}'")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Try a different approach - search for channels with high subscriber counts
    print(f"\n🔍 Trying alternative search strategies")
    print("-" * 40)
    
    # Try searching for "stories" channels that might be the real one
    story_queries = [
        "RequestedReads stories",
        "RequestedReads reddit",
        "RequestedReads I tell stories"
    ]
    
    for query in story_queries:
        try:
            def make_request():
                return monitor.youtube.search().list(
                    part='snippet',
                    q=query,
                    type='channel',
                    maxResults=3,  # Even fewer results
                    order='relevance'
                ).execute()
                
            result = monitor._api_request_with_retry(make_request)
            monitor.add_quota_usage(100)
            
            if result['items']:
                print(f"\nResults for '{query}':")
                for i, item in enumerate(result['items'], 1):
                    channel_id = item['snippet']['channelId']
                    title = item['snippet']['title']
                    
                    # Get subscriber count
                    full_info = monitor.get_channel_info(channel_id)
                    if full_info:
                        subscribers = full_info['subscriber_count']
                        videos = full_info['video_count']
                        
                        print(f"  {i}. {title}")
                        print(f"     Subscribers: {subscribers:,}")
                        print(f"     Videos: {videos:,}")
                        
                        if subscribers > 800000:
                            print(f"     🎯 THIS IS LIKELY THE REAL ONE!")
                        elif subscribers > 100000:
                            print(f"     ⭐ Large channel")
                        print()
                        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Manual approach - try to find the channel ID directly
    print(f"\n🔍 Manual channel ID approach")
    print("-" * 40)
    
    # Based on the image, the real channel has handle @Requestedreads
    # Let's try to construct the channel URL and get the ID
    print("The real RequestedReads channel has:")
    print("- Handle: @Requestedreads")
    print("- 842K subscribers")
    print("- 2.6K videos")
    print("- Description: 'I tell stories :)'")
    
    print("\n💡 SUGGESTION:")
    print("Since the search API isn't finding the real channel, try:")
    print("1. Go to https://youtube.com/@Requestedreads")
    print("2. Copy the channel ID from the URL")
    print("3. Add it directly with: /addchannel <channel_id>")
    
    monitor.close()
    print("\n" + "=" * 50)
    print("✅ Search complete!")

if __name__ == "__main__":
    find_real_requestedreads() 