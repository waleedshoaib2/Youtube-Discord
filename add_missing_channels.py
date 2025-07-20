#!/usr/bin/env python3
"""
Add Missing Channels - Add channels that are missing from your monitoring
"""

from youtube_monitor import YouTubeMonitor
from database import SessionLocal, Channel
from config import Config
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_missing_channels():
    """Add missing channels efficiently"""
    print("🔍 ADDING MISSING CHANNELS")
    print("=" * 50)
    
    monitor = YouTubeMonitor()
    db = SessionLocal()
    
    # List of channels to add (channel_id, name)
    # These are channels that might be missing from your monitoring
    channels_to_add = [
        ("UCc0nOJerxC8JHf7sg3CK3Vg", "RequestedReads"),  # The real one with 842K subs
        
        # Add more channels here as needed
        # ("UCxxxxxxxxxxxxxxxxxxxx", "Channel Name"),
    ]
    
    print(f"📋 Found {len(channels_to_add)} channels to process")
    print()
    
    added_count = 0
    skipped_count = 0
    error_count = 0
    
    for i, (channel_id, channel_name) in enumerate(channels_to_add, 1):
        print(f"🔍 Processing {i}/{len(channels_to_add)}: {channel_name}")
        print(f"   Channel ID: {channel_id}")
        
        # Check if channel already exists
        existing_channel = db.query(Channel).filter_by(channel_id=channel_id).first()
        if existing_channel:
            print(f"   ⏭️  SKIPPED: Channel already exists ({existing_channel.subscriber_count:,} subscribers)")
            skipped_count += 1
            continue
        
        try:
            # Get channel info
            channel_info = monitor.get_channel_info(channel_id)
            
            if channel_info:
                # Create new channel
                channel = Channel(**channel_info)
                db.add(channel)
                db.commit()
                
                print(f"   ✅ ADDED: {channel_info['title']}")
                print(f"      Subscribers: {channel_info['subscriber_count']:,}")
                print(f"      Videos: {channel_info['video_count']:,}")
                added_count += 1
                
            else:
                print(f"   ❌ ERROR: Could not fetch channel info")
                error_count += 1
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            error_count += 1
            db.rollback()
        
        # Rate limiting between requests
        time.sleep(1)
        print()
    
    db.close()
    monitor.close()
    
    print("📊 BATCH SUMMARY:")
    print(f"   ✅ Added: {added_count}")
    print(f"   ⏭️  Skipped: {skipped_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📋 Total processed: {len(channels_to_add)}")
    
    print("\n" + "=" * 50)
    print("✅ Missing channels add complete!")

def check_existing_channels():
    """Check what channels you already have"""
    print("📊 CHECKING EXISTING CHANNELS")
    print("=" * 50)
    
    db = SessionLocal()
    
    # Get all existing channels
    existing_channels = db.query(Channel).all()
    
    print(f"📋 You currently have {len(existing_channels)} channels:")
    print()
    
    for i, channel in enumerate(existing_channels, 1):
        print(f"{i:2d}. {channel.title}")
        print(f"     ID: {channel.channel_id}")
        print(f"     Subscribers: {channel.subscriber_count:,}")
        print(f"     Videos: {channel.video_count}")
        print()
    
    db.close()
    
    print("=" * 50)
    print("✅ Channel check complete!")

if __name__ == "__main__":
    # First check what you have
    check_existing_channels()
    print("\n" + "=" * 50)
    
    # Then add missing channels
    add_missing_channels() 