#!/usr/bin/env python3
"""
Check All Channels for Recent Shorts Activity
"""

import asyncio
from datetime import datetime, timedelta, timezone
from database import SessionLocal, Channel
from youtube_monitor import YouTubeMonitor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_all_channels_for_recent_shorts():
    """Check which channels actually have recent shorts"""
    print("🔍 CHECKING ALL CHANNELS FOR RECENT SHORTS")
    print("=" * 70)
    
    monitor = YouTubeMonitor()
    db = SessionLocal()
    
    try:
        # Get all active channels
        channels = db.query(Channel).filter_by(is_active=True).all()
        print(f"📺 Checking {len(channels)} channels for recent shorts activity...")
        print()
        
        channels_with_recent_shorts = []
        channels_with_old_shorts = []
        channels_no_shorts = []
        
        cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        cutoff_72h = datetime.now(timezone.utc) - timedelta(hours=72)
        cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
        
        for i, channel in enumerate(channels):
            print(f"🔍 [{i+1}/{len(channels)}] {channel.title} (ID: {channel.channel_id})")
            
            try:
                # Get recent videos
                videos = monitor.get_playlist_videos(channel.upload_playlist_id, max_results=20)
                
                if not videos:
                    print("   ❌ No videos found")
                    continue
                    
                # Get stats
                video_ids = [v['video_id'] for v in videos]
                stats = monitor.get_video_statistics(video_ids)
                
                # Debug: Show video count and short count
                total_videos = len(videos)
                short_videos = sum(1 for v in videos if v['video_id'] in stats and stats[v['video_id']].get('is_short', False))
                print(f"      📊 Found {total_videos} videos, {short_videos} are shorts")
                
                shorts_24h = 0
                shorts_72h = 0
                shorts_7d = 0
                latest_short_age = None
                
                for video in videos:
                    video_id = video['video_id']
                    if video_id not in stats:
                        continue
                        
                    video_stats = stats[video_id]
                    
                    # Debug: Print video info for Zlimpy
                    if channel.channel_id == "UCDQvRuXYpvcYmLp-2uZ31Zw":  # Zlimpy's channel ID
                        print(f"      📹 {video['title'][:50]}...")
                        print(f"         Duration: {video_stats.get('duration_seconds', 0)}s")
                        print(f"         Is Short (Duration): {video_stats.get('is_short_duration', False)}")
                        print(f"         Has #Shorts hashtag: {video_stats.get('has_shorts_hashtag', False)}")
                        print(f"         Is Short Type: {video_stats.get('is_short_type', False)}")
                        print(f"         Final Is Short: {video_stats.get('is_short', False)}")
                        print(f"         Title: {video_stats.get('title', '')[:100]}...")
                        print(f"         Description: {video_stats.get('description', '')[:100]}...")
                    
                    if not video_stats.get('is_short', False):
                        continue
                        
                    # This is a short
                    published_at = video['published_at']
                    if isinstance(published_at, str):
                        published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    
                    hours_old = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
                    
                    if latest_short_age is None or hours_old < latest_short_age:
                        latest_short_age = hours_old
                    
                    if published_at >= cutoff_24h:
                        shorts_24h += 1
                    if published_at >= cutoff_72h:
                        shorts_72h += 1
                    if published_at >= cutoff_7d:
                        shorts_7d += 1
                
                # Categorize channel
                if shorts_24h > 0:
                    channels_with_recent_shorts.append({
                        'channel': channel,
                        'shorts_24h': shorts_24h,
                        'shorts_72h': shorts_72h,
                        'latest_age': latest_short_age
                    })
                    print(f"   🔥 {shorts_24h} shorts in 24h, {shorts_72h} in 72h")
                    
                elif shorts_72h > 0:
                    channels_with_recent_shorts.append({
                        'channel': channel,
                        'shorts_24h': 0,
                        'shorts_72h': shorts_72h,
                        'latest_age': latest_short_age
                    })
                    print(f"   ⏰ {shorts_72h} shorts in 72h (none in 24h)")
                    
                elif shorts_7d > 0:
                    channels_with_old_shorts.append({
                        'channel': channel,
                        'shorts_7d': shorts_7d,
                        'latest_age': latest_short_age
                    })
                    print(f"   📅 {shorts_7d} shorts in 7d (none in 72h) - latest {latest_short_age:.1f}h ago")
                    
                else:
                    channels_no_shorts.append(channel)
                    if latest_short_age:
                        print(f"   ❌ No shorts in 7d - latest {latest_short_age:.1f}h ago")
                    else:
                        print(f"   ❌ No shorts found at all")
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
        
        # Summary report
        print("\n" + "=" * 70)
        print("📊 SUMMARY REPORT")
        print("=" * 70)
        
        print(f"\n🔥 CHANNELS WITH RECENT SHORTS ({len(channels_with_recent_shorts)}):")
        if channels_with_recent_shorts:
            for item in channels_with_recent_shorts:
                channel = item['channel']
                print(f"   • {channel.title} (ID: {channel.channel_id}): {item['shorts_24h']} (24h), {item['shorts_72h']} (72h)")
        else:
            print("   ❌ NO CHANNELS HAVE RECENT SHORTS!")
            
        print(f"\n📅 CHANNELS WITH OLD SHORTS ({len(channels_with_old_shorts)}):")
        for item in channels_with_old_shorts[:10]:  # Show first 10
            channel = item['channel']
            print(f"   • {channel.title} (ID: {channel.channel_id}): latest short {item['latest_age']:.1f}h ago")
            
        print(f"\n❌ CHANNELS WITH NO SHORTS ({len(channels_no_shorts)}):")
        for channel in channels_no_shorts[:10]:  # Show first 10
            print(f"   • {channel.title} (ID: {channel.channel_id})")
            
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        if len(channels_with_recent_shorts) == 0:
            print("   🚨 CRITICAL: No channels are posting recent shorts!")
            print("   💡 Solutions:")
            print("      1. Add more active channels that post shorts daily")
            print("      2. Extend monitoring window to 7 days (not recommended)")
            print("      3. Check if these channels moved to posting longer videos")
        elif len(channels_with_recent_shorts) < 5:
            print("   ⚠️  Very few channels posting recent shorts")
            print("   💡 Consider adding more active short-form channels")
        else:
            print("   ✅ Good activity level - system should be working")
            
        total_potential_shorts = sum(item['shorts_72h'] for item in channels_with_recent_shorts)
        print(f"\n📈 EXPECTED ACTIVITY:")
        print(f"   • Shorts available in last 72h: {total_potential_shorts}")
        print(f"   • Expected notifications (if >400k views): {max(1, total_potential_shorts // 10)}-{max(2, total_potential_shorts // 5)} per day")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        monitor.close()

if __name__ == "__main__":
    asyncio.run(check_all_channels_for_recent_shorts())