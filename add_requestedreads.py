#!/usr/bin/env python3
"""
Add Real RequestedReads Channel - Quick script to add the real RequestedReads
"""

from youtube_monitor import YouTubeMonitor
from database import SessionLocal, Channel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_real_requestedreads():
    """Add the real RequestedReads channel (842K subscribers)"""
    print("🎯 ADDING REAL REQUESTEDREADS")
    print("=" * 50)
    
    monitor = YouTubeMonitor()
    db = SessionLocal()
    
    # The real RequestedReads channel ID (842K subscribers)
    channel_id = "UCc0nOJerxC8JHf7sg3CK3Vg"
    
    print(f"🔍 Processing: RequestedReads")
    print(f"   Channel ID: {channel_id}")
    
    # Check if channel already exists
    existing_channel = db.query(Channel).filter_by(channel_id=channel_id).first()
    if existing_channel:
        print(f"   ⏭️  SKIPPED: Channel already exists ({existing_channel.subscriber_count:,} subscribers)")
        db.close()
        monitor.close()
        return
    
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
            print(f"      Description: {channel_info['description'][:100]}...")
            
        else:
            print(f"   ❌ ERROR: Could not fetch channel info")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        db.rollback()
    
    db.close()
    monitor.close()
    
    print("\n" + "=" * 50)
    print("✅ RequestedReads add complete!")

if __name__ == "__main__":
    add_real_requestedreads() 