#!/usr/bin/env python3
"""
System Summary - Show current bot configuration and status
"""

from database import SessionLocal, Video, Channel
from datetime import datetime, timezone, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_system_summary():
    """Show current system configuration and status"""
    print("🤖 YOUTUBE SHORTS MONITORING SYSTEM")
    print("=" * 60)
    
    db = SessionLocal()
    
    # System Configuration
    print("\n📋 SYSTEM CONFIGURATION:")
    print("  • Monitoring: SHORTS only (under 3 minutes)")
    print("  • Notification Threshold: 700,000 views")
    print("  • Monitoring Window: 3 days (continuous re-monitoring)")
    print("  • Check Interval: Every 60 minutes")
    print("  • Stats Update: Hourly for videos under 3 days old")
    print("  • Database: SQLite (persistent)")
    
    # Channel Statistics
    total_channels = db.query(Channel).count()
    print(f"\n📺 CHANNEL STATISTICS:")
    print(f"  • Total Channels: {total_channels}")
    
    # Video Statistics
    total_videos = db.query(Video).count()
    short_videos = db.query(Video).filter(Video.is_short == True).count()
    notified_videos = db.query(Video).filter(Video.notified == True).count()
    
    print(f"\n📱 VIDEO STATISTICS:")
    print(f"  • Total Videos: {total_videos:,}")
    print(f"  • Short Videos: {short_videos:,}")
    print(f"  • Notified Videos: {notified_videos:,}")
    
    # Recent Activity (last 3 days)
    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    recent_videos = db.query(Video).filter(
        Video.published_at >= cutoff
    ).count()
    
    recent_shorts = db.query(Video).filter(
        Video.published_at >= cutoff,
        Video.is_short == True
    ).count()
    
    print(f"\n⏰ RECENT ACTIVITY (Last 3 days):")
    print(f"  • New Videos: {recent_videos:,}")
    print(f"  • New Shorts: {recent_shorts:,}")
    
    # High Performing Videos
    high_performing = db.query(Video).filter(
        Video.view_count >= 400000,
        Video.is_short == True
    ).count()
    
    print(f"\n🏆 HIGH PERFORMING VIDEOS:")
    print(f"  • Videos with 400k+ views: {high_performing:,}")
    
    # Top 5 Channels by Video Count
    print(f"\n🔥 TOP 5 CHANNELS BY VIDEO COUNT:")
    channel_stats = db.query(Channel).all()
    channel_video_counts = []
    
    for channel in channel_stats:
        video_count = db.query(Video).filter(Video.channel_id == channel.channel_id).count()
        short_count = db.query(Video).filter(
            Video.channel_id == channel.channel_id,
            Video.is_short == True
        ).count()
        channel_video_counts.append((channel.title, video_count, short_count))
    
    # Sort by total video count
    channel_video_counts.sort(key=lambda x: x[1], reverse=True)
    
    for i, (name, total, shorts) in enumerate(channel_video_counts[:5], 1):
        print(f"  {i}. {name}: {total} videos ({shorts} shorts)")
    
    # Recent Viral Videos
    print(f"\n🚀 RECENT VIRAL VIDEOS (400k+ views):")
    viral_videos = db.query(Video).filter(
        Video.view_count >= 400000,
        Video.is_short == True
    ).order_by(Video.published_at.desc()).limit(5).all()
    
    if viral_videos:
        for video in viral_videos:
            channel = db.query(Channel).filter_by(channel_id=video.channel_id).first()
            channel_name = channel.title if channel else "Unknown"
            print(f"  • {video.title[:50]}... ({video.view_count:,} views) - {channel_name}")
    else:
        print("  • No viral videos yet")
    
    db.close()
    
    print(f"\n" + "=" * 60)
    print("✅ System is running and monitoring for 400k+ view Shorts!")
    print("📊 Use /top all to see all-time best videos")
    print("📊 Use /topchannel [channel] all to see channel's best videos")

if __name__ == "__main__":
    show_system_summary() 