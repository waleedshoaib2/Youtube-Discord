#!/usr/bin/env python3
"""
Database Checker - See what's stored in your database
"""

from database import SessionLocal, Channel, Video, ViewSnapshot, ApiKeyUsage
from datetime import datetime, timezone, timedelta

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

def check_top_24h_shorts():
    """Check top performing shorts from last 24 hours"""
    db = SessionLocal()
    
    print("🏆 TOP 24 HOUR SHORTS")
    print("=" * 50)
    
    # Get cutoff time (24 hours ago)
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
    
    # Get shorts from last 24 hours, ordered by views
    recent_shorts = db.query(Video).filter(
        Video.is_short == True,
        Video.published_at >= cutoff_time
    ).order_by(Video.view_count.desc()).limit(20).all()
    
    if not recent_shorts:
        print("❌ No shorts found in the last 24 hours!")
        db.close()
        return
    
    print(f"\n📱 Found {len(recent_shorts)} shorts in the last 24 hours:")
    print()
    
    for i, video in enumerate(recent_shorts, 1):
        # Get channel info
        channel = db.query(Channel).filter_by(channel_id=video.channel_id).first()
        channel_name = channel.title if channel else "Unknown Channel"
        
        # Calculate hours old (handle timezone-aware and naive datetimes)
        if video.published_at.tzinfo is None:
            published_at = video.published_at.replace(tzinfo=timezone.utc)
        else:
            published_at = video.published_at
        
        hours_old = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
        
        # Calculate views per hour
        views_per_hour = video.view_count / max(hours_old, 1)
        
        print(f"#{i:2d} 🏆 {video.title[:50]}...")
        print(f"    📺 Channel: {channel_name}")
        print(f"    👁️  Views: {video.view_count:,}")
        print(f"    ⏱️  Duration: {video.duration_seconds}s")
        print(f"    🕐 Age: {hours_old:.1f}h ago")
        print(f"    📈 Views/Hour: {views_per_hour:,.0f}")
        print(f"    👍 Likes: {video.like_count:,}")
        print(f"    💬 Comments: {video.comment_count:,}")
        print()
    
    # Summary statistics
    total_views = sum(video.view_count for video in recent_shorts)
    avg_views = total_views / len(recent_shorts) if recent_shorts else 0
    max_views = max(video.view_count for video in recent_shorts) if recent_shorts else 0
    
    print("📊 SUMMARY:")
    print(f"   • Total shorts: {len(recent_shorts)}")
    print(f"   • Total views: {total_views:,}")
    print(f"   • Average views: {avg_views:,.0f}")
    print(f"   • Highest views: {max_views:,}")
    print(f"   • Time range: Last 24 hours")
    
    db.close()
    
    print("\n" + "=" * 50)
    print("✅ Top 24h shorts check complete!")

def check_recent_shorts_activity():
    """Check recent shorts activity and posting frequency"""
    db = SessionLocal()
    
    print("📅 RECENT SHORTS ACTIVITY")
    print("=" * 50)
    
    # Get all shorts ordered by publish date
    all_shorts = db.query(Video).filter(
        Video.is_short == True
    ).order_by(Video.published_at.desc()).limit(50).all()
    
    if not all_shorts:
        print("❌ No shorts found in database!")
        db.close()
        return
    
    print(f"\n📱 Most recent {len(all_shorts)} shorts:")
    print()
    
    # Group by channel
    channel_activity = {}
    for video in all_shorts:
        channel = db.query(Channel).filter_by(channel_id=video.channel_id).first()
        channel_name = channel.title if channel else "Unknown"
        
        if channel_name not in channel_activity:
            channel_activity[channel_name] = []
        channel_activity[channel_name].append(video)
    
    for channel_name, videos in channel_activity.items():
        print(f"📺 {channel_name}:")
        for video in videos[:3]:  # Show 3 most recent per channel
            # Handle timezone-aware vs naive datetime
            if video.published_at.tzinfo is None:
                published_at = video.published_at.replace(tzinfo=timezone.utc)
            else:
                published_at = video.published_at
                
            hours_old = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
            days_old = hours_old / 24
            
            if days_old < 1:
                time_str = f"{hours_old:.1f}h ago"
            else:
                time_str = f"{days_old:.1f} days ago"
                
            print(f"  • {video.title[:50]}... ({video.duration_seconds}s)")
            print(f"    Views: {video.view_count:,} | Published: {time_str}")
        print()
    
    # Check posting frequency
    print("📊 POSTING FREQUENCY ANALYSIS:")
    
    # Last 7 days
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    week_shorts = db.query(Video).filter(
        Video.is_short == True,
        Video.published_at >= week_ago
    ).count()
    
    # Last 30 days
    month_ago = datetime.now(timezone.utc) - timedelta(days=30)
    month_shorts = db.query(Video).filter(
        Video.is_short == True,
        Video.published_at >= month_ago
    ).count()
    
    # Count videos from last 24 hours (handle timezone properly)
    day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    recent_24h = len([v for v in all_shorts if 
        (v.published_at.replace(tzinfo=timezone.utc) if v.published_at.tzinfo is None else v.published_at) >= day_ago
    ])
    
    print(f"  • Last 24 hours: {recent_24h}")
    print(f"  • Last 7 days: {week_shorts}")
    print(f"  • Last 30 days: {month_shorts}")
    print(f"  • Total shorts: {db.query(Video).filter(Video.is_short == True).count()}")
    
    # Channels with recent activity
    recent_channels = db.query(Video.channel_id).filter(
        Video.is_short == True,
        Video.published_at >= week_ago
    ).distinct().count()
    
    print(f"  • Channels with shorts in last 7 days: {recent_channels}/49")
    
    db.close()
    
    print("\n" + "=" * 50)
    print("✅ Recent activity check complete!")

if __name__ == "__main__":
    check_database()
    print("\n" + "=" * 50)
    check_top_24h_shorts()
    print("\n" + "=" * 50)
    check_recent_shorts_activity() 