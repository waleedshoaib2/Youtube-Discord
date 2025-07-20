#!/usr/bin/env python3
"""
Utility script to add multiple YouTube channels to the monitoring system.
This script helps convert channel names to YouTube URLs and adds them to the database.
"""

import asyncio
import re
from config import Config
from database import SessionLocal, Channel
from youtube_monitor import YouTubeMonitor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChannelAdder:
    def __init__(self):
        self.youtube_monitor = YouTubeMonitor()
        self.db = SessionLocal()
        
    def extract_channel_id_from_url(self, url):
        """Extract channel ID from various YouTube URL formats"""
        patterns = [
            r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
            r'youtube\.com/c/([a-zA-Z0-9_-]+)',
            r'youtube\.com/user/([a-zA-Z0-9_-]+)',
            r'youtube\.com/@([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                identifier = match.group(1)
                if identifier.startswith('UC'):
                    return identifier
                # For non-direct channel IDs, we'd need to search
                # For now, return None and handle manually
                return None
                
        # Try if it's just the channel ID
        if url.startswith('UC') and len(url) == 24:
            return url
            
        return None
        
    def search_channel_by_name(self, channel_name):
        """Search for a channel by name using YouTube API"""
        try:
            # Search for the channel
            request = self.youtube_monitor.youtube.search().list(
                part="snippet",
                q=channel_name,
                type="channel",
                maxResults=1
            )
            response = request.execute()
            self.youtube_monitor.add_quota_usage(100)  # Search costs 100 units
            
            if response.get('items'):
                channel_id = response['items'][0]['snippet']['channelId']
                logger.info(f"Found channel '{channel_name}' with ID: {channel_id}")
                return channel_id
            else:
                logger.warning(f"No channel found for '{channel_name}'")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for channel '{channel_name}': {e}")
            return None
            
    def add_channel_by_name(self, channel_name):
        """Add a channel to monitoring by name"""
        logger.info(f"Processing channel: {channel_name}")
        
        # First try to search for the channel
        channel_id = self.search_channel_by_name(channel_name)
        
        if not channel_id:
            logger.warning(f"Could not find channel ID for '{channel_name}'. You'll need to add it manually.")
            return False
            
        # Get channel info
        channel_info = self.youtube_monitor.get_channel_info(channel_id)
        if not channel_info:
            logger.error(f"Could not fetch channel info for '{channel_name}'")
            return False
            
        # Check if channel already exists
        existing = self.db.query(Channel).filter_by(channel_id=channel_id).first()
        if existing:
            logger.info(f"Channel '{channel_name}' already exists in database")
            return True
            
        # Add to database
        channel = Channel(**channel_info)
        self.db.add(channel)
        self.db.commit()
        
        logger.info(f"Successfully added channel: {channel_info['title']} ({channel_info['subscriber_count']:,} subscribers)")
        return True
        
    def add_channels_from_list(self, channel_names):
        """Add multiple channels from a list of names"""
        success_count = 0
        total_count = len(channel_names)
        
        logger.info(f"Starting to add {total_count} channels...")
        
        for i, channel_name in enumerate(channel_names, 1):
            logger.info(f"Progress: {i}/{total_count}")
            
            if self.add_channel_by_name(channel_name.strip()):
                success_count += 1
                
            # Rate limiting to avoid API quota issues
            if i % 5 == 0:  # Every 5 channels
                logger.info("Taking a short break to avoid rate limits...")
                import time
                time.sleep(2)
                
        logger.info(f"Completed! Successfully added {success_count}/{total_count} channels.")
        return success_count, total_count
        
    def close(self):
        """Clean up resources"""
        self.youtube_monitor.close()
        self.db.close()

def main():
    # Your list of channel names
    channel_names = [
        "taletrailz",
        "SaneRedditor", 
        "burnystories",
        "redditcackle",
        "everreddit",
        "eternalreddit",
        "WinsyTheStory",
        "TheRedditReader475",
        "jxlasjournal",
        "marlstories",
        "redditreads_0",
        "zlimpy",
        "EK_stories",
        "talesyapper",
        "1talesfactory",
        "borostories",
        "pulsesttories",
        "EchoSttoriess",
        "turt_stories",
        "redditpanther",
        "storiesclock",
        "requestedreads",
        "istoryum",
        "boofstories",
        "lomustories",
        "storieslucid",
        "reddit_report",
        "talereader_0",
        "taxyclips",
        "thecoralstories",
        "unlimited.stories",
        "delilahtales",
        "pupptalez",
        "reddityapps",
        "SA_storybook",
        "redditrewind_02",
        "SA_reads",
        "ytminifablefever",
        "thumbsupstories",
        "thefloam",
        "jukotexts",
        "sultan-hakeem",
        "reddit_gossipz",
        "cloud9txt",
        "secretdiariessx",
        "crystallreads",
        "koalareadss",
        "randyreads1",
        "creeky_updates",
        "Zorgowroteit",
        "ytzexla",
        "auratext",
        "creekystoriess",
        "euphraat",
        "jawerlydiaries",
        "bjstoriez",
        "regrethaunts",
        "truthtide7",
        "redditbiker",
        "RycoStories",
        "redditcackle"
    ]
    
    adder = ChannelAdder()
    
    try:
        success, total = adder.add_channels_from_list(channel_names)
        print(f"\n🎉 Successfully added {success}/{total} channels to monitoring!")
        
        if success < total:
            print("\n⚠️  Some channels couldn't be found automatically.")
            print("You may need to add them manually using Discord commands:")
            print("!add_channel <youtube_channel_url>")
            
    except KeyboardInterrupt:
        print("\n⏹️  Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        adder.close()

if __name__ == "__main__":
    main() 