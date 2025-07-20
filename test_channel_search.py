#!/usr/bin/env python3
"""
Test Channel Search - Debug channel search functionality
"""

from youtube_monitor import YouTubeMonitor
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_channel_search():
    """Test channel search functionality"""
    print("🔍 TESTING CHANNEL SEARCH")
    print("=" * 50)
    
    monitor = YouTubeMonitor()
    
    # Test different search methods
    search_terms = [
        "RequestedReads",
        "Requested Reads", 
        "@Requestedreads",
        "Requestedreads"
    ]
    
    for search_term in search_terms:
        print(f"\n🔍 Searching for: '{search_term}'")
        print("-" * 30)
        
        try:
            # Test search by handle
            if search_term.startswith('@'):
                handle = search_term[1:]  # Remove @
                channel_info = monitor.search_channel_by_handle(handle)
            else:
                # Try direct search
                channel_info = monitor.search_channel_by_handle(search_term)
                
            if channel_info:
                print(f"✅ Found channel:")
                print(f"   Title: {channel_info['title']}")
                print(f"   ID: {channel_info['channel_id']}")
                print(f"   Subscribers: {channel_info['subscriber_count']:,}")
                print(f"   Videos: {channel_info['video_count']:,}")
                print(f"   Description: {channel_info['description'][:100]}...")
            else:
                print(f"❌ No channel found for '{search_term}'")
                
        except Exception as e:
            print(f"❌ Error searching '{search_term}': {e}")
    
    # Test direct channel ID lookup
    print(f"\n🔍 Testing direct channel lookup")
    print("-" * 30)
    
    # Try to find the real RequestedReads channel ID
    # We'll search for channels with similar names
    test_queries = [
        "RequestedReads",
        "Requested Reads",
        "Requestedreads"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching YouTube for: '{query}'")
        try:
            # Use search API to find channels
            def make_request():
                return monitor.youtube.search().list(
                    part='snippet',
                    q=query,
                    type='channel',
                    maxResults=5
                ).execute()
                
            result = monitor._api_request_with_retry(make_request)
            monitor.add_quota_usage(100)
            
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
                        print(f"     Subscribers: {full_info['subscriber_count']:,}")
                        print(f"     Videos: {full_info['video_count']:,}")
                        print()
            else:
                print(f"❌ No channels found for '{query}'")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    monitor.close()
    print("\n" + "=" * 50)
    print("✅ Channel search test complete!")

if __name__ == "__main__":
    test_channel_search() 