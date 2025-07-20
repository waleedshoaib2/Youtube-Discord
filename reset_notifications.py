#!/usr/bin/env python3
"""
Reset Notifications - Reset notification status for testing new average-based system
"""

from database import SessionLocal, Video
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_notifications():
    """Reset notification status for all videos"""
    print("🔄 RESETTING NOTIFICATION STATUS")
    print("=" * 50)
    
    db = SessionLocal()
    
    # Get all videos
    all_videos = db.query(Video).all()
    print(f"📋 Found {len(all_videos)} total videos")
    
    # Reset notification status
    updated_count = 0
    for video in all_videos:
        if video.notified:
            video.notified = False
            updated_count += 1
    
    db.commit()
    db.close()
    
    print(f"✅ Reset notification status for {updated_count} videos")
    print("📝 All videos will now be eligible for notifications")
    print("🎯 New system will check if videos are above channel average")
    
    print("\n" + "=" * 50)
    print("✅ Reset complete!")

def check_notification_status():
    """Check current notification status"""
    print("📊 CHECKING NOTIFICATION STATUS")
    print("=" * 50)
    
    db = SessionLocal()
    
    # Count videos by notification status
    notified_videos = db.query(Video).filter(Video.notified == True).count()
    unnotified_videos = db.query(Video).filter(Video.notified == False).count()
    total_videos = db.query(Video).count()
    
    print(f"📋 Total videos: {total_videos}")
    print(f"✅ Already notified: {notified_videos}")
    print(f"⏳ Pending notification: {unnotified_videos}")
    
    # Show recent unnotified videos
    recent_unnotified = db.query(Video).filter(
        Video.notified == False
    ).order_by(Video.published_at.desc()).limit(10).all()
    
    if recent_unnotified:
        print(f"\n📱 Recent unnotified videos:")
        for video in recent_unnotified:
            print(f"  • {video.title[:50]}... ({video.view_count:,} views)")
    
    db.close()
    
    print("\n" + "=" * 50)
    print("✅ Status check complete!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_notifications()
    else:
        check_notification_status() 