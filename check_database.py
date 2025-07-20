#!/usr/bin/env python3
"""
Database Checker - See what's stored in your database
"""

from database import SessionLocal, Channel, Video, ViewSnapshot, ApiKeyUsage
from datetime import datetime, timezone

def check_database():
    """Check what's stored in the database"""
    db = SessionLocal()
    
    print("🔍 DATABASE CONTENTS CHECK")
    print("=" * 50)
    
    # Check channels
    channels = db.query(Channel).all()
    print(f"\n📺 CHANNELS ({len(channels)} total):")
    for channel in channels:
        print(f"  • {channel.title} (ID: {channel.channel_id})")
        print(f"    - Subscribers: {channel.subscriber_count:,}")
        print(f"    - Videos: {channel.video_count}")
        print(f"    - Last checked: {channel.last_checked}")
        print()
    
    # Check videos (shorts only)
    shorts = db.query(Video).filter(Video.is_short == True).all()
    print(f"\n📱 SHORT VIDEOS ({len(shorts)} total):")
    
    # Group by channel
    channel_shorts = {}
    for video in shorts:
        channel = db.query(Channel).filter_by(channel_id=video.channel_id).first()
        channel_name = channel.title if channel else "Unknown"
        
        if channel_name not in channel_shorts:
            channel_shorts[channel_name] = []
        channel_shorts[channel_name].append(video)
    
    for channel_name, videos in channel_shorts.items():
        print(f"\n  📺 {channel_name} ({len(videos)} shorts):")
        for video in videos[:5]:  # Show first 5 per channel
            print(f"    • {video.title[:60]}... ({video.duration_seconds}s)")
            print(f"      Views: {video.view_count:,} | Published: {video.published_at.strftime('%Y-%m-%d %H:%M')}")
        if len(videos) > 5:
            print(f"    ... and {len(videos) - 5} more")
    
    # Check API usage
    api_usage = db.query(ApiKeyUsage).all()
    print(f"\n🔑 API KEY USAGE ({len(api_usage)} keys):")
    for usage in api_usage:
        print(f"  • Key {usage.api_key_index} (*{usage.api_key_identifier}): {usage.quota_used:,}/10,000")
        print(f"    Last used: {usage.last_used}")
        print(f"    Errors: {usage.error_count}")
        print()
    
    # Check view snapshots
    snapshots = db.query(ViewSnapshot).count()
    print(f"\n📊 VIEW SNAPSHOTS: {snapshots:,} total")
    
    # Recent activity
    recent_videos = db.query(Video).filter(
        Video.published_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    ).count()
    print(f"📅 VIDEOS ADDED TODAY: {recent_videos}")
    
    db.close()
    
    print("\n" + "=" * 50)
    print("✅ Database check complete!")

if __name__ == "__main__":
    check_database() 