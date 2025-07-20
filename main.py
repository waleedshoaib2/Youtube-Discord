import asyncio
import schedule
import threading
import time
from datetime import datetime, timedelta, timezone
import logging
import discord
from discord import app_commands
from config import Config
from database import SessionLocal, Channel, Video
from youtube_monitor import YouTubeMonitor
from analytics import VideoAnalytics
from transcript_handler import TranscriptHandler
from discord_bot import YouTubeBot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YouTubeMonitoringSystem:
    def __init__(self):
        self.youtube_monitor = YouTubeMonitor()
        self.analytics = VideoAnalytics()
        self.transcript_handler = TranscriptHandler()
        self.discord_bot = None
        self.monitoring_active = True
        
    async def initialize_discord_bot(self):
        """Initialize and start Discord bot"""
        self.discord_bot = YouTubeBot()
        
        # Add slash commands
        @self.discord_bot.tree.command(name="listchannels", description="List all monitored channels")
        async def listchannels(interaction: discord.Interaction):
            """List all monitored channels"""
            await interaction.response.defer()
            
            db = SessionLocal()
            channels = db.query(Channel).filter_by(is_active=True).all()
            db.close()
            
            if not channels:
                await interaction.followup.send("No channels being monitored!")
                return
                
            embed = discord.Embed(title="Monitored Channels", color=discord.Color.blue())
            
            # Limit to first 20 channels to avoid Discord's 25 field limit
            for i, channel in enumerate(channels[:20]):
                embed.add_field(
                    name=f"{i+1}. {channel.title}",
                    value=f"Subscribers: {channel.subscriber_count:,}\nVideos: {channel.video_count}",
                    inline=True
                )
            
            # Add summary if there are more channels
            if len(channels) > 20:
                embed.add_field(
                    name="📊 Summary",
                    value=f"Showing 20 of {len(channels)} channels\nUse `/listshorts` to see recent shorts",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        @self.discord_bot.tree.command(name="listshorts", description="List recent short videos")
        async def listshorts(interaction: discord.Interaction, channel_name: str = None):
            """List recent short videos from monitored channels"""
            await interaction.response.defer()
            
            db = SessionLocal()
            
            if channel_name:
                # List shorts from specific channel
                channel = db.query(Channel).filter(
                    Channel.title.ilike(f"%{channel_name}%")
                ).first()
                if not channel:
                    await interaction.followup.send(f"Channel '{channel_name}' not found!")
                    return
                    
                videos = db.query(Video).filter(
                    Video.channel_id == channel.channel_id,
                    Video.is_short == True
                ).order_by(Video.published_at.desc()).limit(10).all()
                
                embed = discord.Embed(
                    title=f"Recent Shorts from {channel.title}",
                    color=discord.Color.green()
                )
            else:
                # List shorts from all channels
                videos = db.query(Video).filter(
                    Video.is_short == True
                ).order_by(Video.published_at.desc()).limit(15).all()
                
                embed = discord.Embed(
                    title="Recent Shorts from All Channels",
                    color=discord.Color.green()
                )
            
            db.close()
            
            if not videos:
                await interaction.followup.send("No short videos found!")
                return
                
            # Limit to first 15 videos to avoid Discord's 25 field limit
            for i, video in enumerate(videos[:15]):
                # Get channel info
                channel = db.query(Channel).filter_by(channel_id=video.channel_id).first()
                channel_name = channel.title if channel else "Unknown Channel"
                
                embed.add_field(
                    name=f"📱 {i+1}. {video.title[:40]}...",
                    value=f"**Channel**: {channel_name}\n"
                          f"**Duration**: {video.duration_seconds}s\n"
                          f"**Views**: {video.view_count:,}\n"
                          f"**Published**: {video.published_at.strftime('%Y-%m-%d %H:%M')}",
                    inline=False
                )
            
            # Add summary if there are more videos
            if len(videos) > 15:
                embed.add_field(
                    name="📊 Summary",
                    value=f"Showing 15 of {len(videos)} recent shorts",
                    inline=False
                )
                
            await interaction.followup.send(embed=embed)
            
        @self.discord_bot.tree.command(name="stats", description="Show bot statistics")
        async def stats(interaction: discord.Interaction):
            """Show bot statistics"""
            await interaction.response.defer()
            
            # Show overall stats
            db = SessionLocal()
            total_channels = db.query(Channel).filter_by(is_active=True).count()
            total_shorts = db.query(Video).filter(Video.is_short == True).count()
            total_videos = db.query(Video).count()
            db.close()
            
            # Get quota status for all keys
            quota_status = self.youtube_monitor.get_quota_status()
            
            embed = discord.Embed(title="Bot Statistics", color=discord.Color.green())
            embed.add_field(name="Monitored Channels", value=total_channels, inline=True)
            embed.add_field(name="Total Videos", value=total_videos, inline=True)
            embed.add_field(name="Short Videos", value=total_shorts, inline=True)
            
            # Show quota for each API key
            total_used = sum(key['quota_used'] for key in quota_status)
            total_available = len(quota_status) * Config.DAILY_QUOTA_LIMIT
            
            embed.add_field(
                name="Total Quota", 
                value=f"{total_used:,} / {total_available:,} ({(total_used/total_available*100):.1f}%)", 
                inline=True
            )
            
            # Individual key status
            key_status_text = []
            for key in quota_status:
                status = "✅" if key['is_active'] and key['quota_remaining'] > 1000 else "⚠️" if key['quota_remaining'] > 0 else "❌"
                key_status_text.append(
                    f"{status} Key {key['index']} (*{key['identifier']}): "
                    f"{key['quota_used']:,}/{Config.DAILY_QUOTA_LIMIT:,}"
                )
            
            embed.add_field(
                name="API Keys Status", 
                value="\n".join(key_status_text), 
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        @self.discord_bot.tree.command(name="apistatus", description="Show detailed API key status")
        async def apistatus(interaction: discord.Interaction):
            """Show detailed API key status"""
            await interaction.response.defer()
            
            quota_status = self.youtube_monitor.get_quota_status()
            
            embed = discord.Embed(title="API Key Detailed Status", color=discord.Color.blue())
            
            for key in quota_status:
                # Determine health color
                if not key['is_active']:
                    color = "🔴"
                elif key['quota_remaining'] < 500:
                    color = "🟡"  
                else:
                    color = "🟢"
                    
                # Format last used time
                last_used = "Never" if not key['last_used'] else key['last_used'].strftime("%H:%M UTC")
                
                embed.add_field(
                    name=f"{color} API Key {key['index']} (*{key['identifier']})",
                    value=f"**Quota**: {key['quota_used']:,} / 10,000\n"
                          f"**Remaining**: {key['quota_remaining']:,}\n"
                          f"**Last Used**: {last_used}\n"
                          f"**Errors**: {key['error_count']}",
                    inline=True
                )
                
            # Add current active key
            embed.add_field(
                name="Currently Active",
                value=f"Using API Key {self.youtube_monitor.current_key_index}",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        @self.discord_bot.tree.command(name="checknow", description="Manually trigger channel check")
        async def checknow(interaction: discord.Interaction):
            """Manually trigger channel check"""
            await interaction.response.defer()
            
            await interaction.followup.send("Starting manual check of all channels for SHORTS...")
            await self.check_all_channels()
            await interaction.followup.send("Manual check completed!")
            
        @self.discord_bot.tree.command(name="topchannel", description="Show top performing videos for a specific channel")
        async def topchannel(interaction: discord.Interaction, channel_handle: str, timeframe: int = 24):
            """Show top performing videos for a specific channel"""
            await interaction.response.defer()
            
            db = SessionLocal()
            
            # Find channel by handle or name
            channel = db.query(Channel).filter(
                (Channel.title.ilike(f"%{channel_handle}%")) |
                (Channel.channel_id.ilike(f"%{channel_handle}%"))
            ).first()
            
            if not channel:
                await interaction.followup.send(f"Channel '{channel_handle}' not found!")
                return
                
            # Get videos from the specified timeframe (in hours)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=timeframe)
            
            videos = db.query(Video).filter(
                Video.channel_id == channel.channel_id,
                Video.published_at >= cutoff_time,
                Video.is_short == True
            ).order_by(Video.view_count.desc()).limit(10).all()
            
            db.close()
            
            if not videos:
                embed = discord.Embed(
                    title=f"No Shorts Found for {channel.title}",
                    description=f"No shorts found in the last {timeframe} hours",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return
                
            embed = discord.Embed(
                title=f"🔥 Top Shorts - {channel.title}",
                description=f"Last {timeframe} hours | {len(videos)} shorts found",
                color=discord.Color.red()
            )
            
            for i, video in enumerate(videos):
                # Ensure published_at is timezone-aware
                if video.published_at.tzinfo is None:
                    published_at = video.published_at.replace(tzinfo=timezone.utc)
                else:
                    published_at = video.published_at
                
                hours_old = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
                
                embed.add_field(
                    name=f"#{i+1} 📱 {video.title[:50]}...",
                    value=f"**Views**: {video.view_count:,}\n"
                          f"**Duration**: {video.duration_seconds}s\n"
                          f"**Age**: {hours_old:.1f}h ago\n"
                          f"**Published**: {video.published_at.strftime('%Y-%m-%d %H:%M')}",
                    inline=False
                )
                
            await interaction.followup.send(embed=embed)
            
        @self.discord_bot.tree.command(name="top", description="Show top performing videos across all channels")
        async def top(interaction: discord.Interaction, timeframe: int = 24):
            """Show top performing videos across all channels"""
            await interaction.response.defer()
            
            db = SessionLocal()
            
            # Get videos from the specified timeframe (in hours)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=timeframe)
            
            videos = db.query(Video).filter(
                Video.published_at >= cutoff_time,
                Video.is_short == True
            ).order_by(Video.view_count.desc()).limit(15).all()
            
            if not videos:
                embed = discord.Embed(
                    title="No Shorts Found",
                    description=f"No shorts found in the last {timeframe} hours",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return
                
            embed = discord.Embed(
                title=f"🏆 Top Performing Shorts",
                description=f"Last {timeframe} hours | {len(videos)} shorts found",
                color=discord.Color.gold()
            )
            
            for i, video in enumerate(videos):
                # Get channel info
                channel = db.query(Channel).filter_by(channel_id=video.channel_id).first()
                channel_name = channel.title if channel else "Unknown Channel"
                
                # Ensure published_at is timezone-aware
                if video.published_at.tzinfo is None:
                    published_at = video.published_at.replace(tzinfo=timezone.utc)
                else:
                    published_at = video.published_at
                
                hours_old = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
                
                embed.add_field(
                    name=f"#{i+1} 📱 {video.title[:40]}...",
                    value=f"**Channel**: {channel_name}\n"
                          f"**Views**: {video.view_count:,}\n"
                          f"**Duration**: {video.duration_seconds}s\n"
                          f"**Age**: {hours_old:.1f}h ago",
                    inline=False
                )
                
            db.close()
            await interaction.followup.send(embed=embed)
            
        @self.discord_bot.tree.command(name="addchannel", description="Add a channel to monitor")
        async def addchannel(interaction: discord.Interaction, handle: str):
            """Add a channel to monitor"""
            await interaction.response.defer()
            
            # Extract channel ID from handle
            channel_id = self._extract_channel_id(handle)
            if not channel_id:
                await interaction.followup.send("Invalid channel handle! Please provide a YouTube channel URL or handle.")
                return
                
            # Fetch channel info
            channel_info = self.youtube_monitor.get_channel_info(channel_id)
            if not channel_info:
                await interaction.followup.send("Could not fetch channel information!")
                return
                
            # Add to database
            db = SessionLocal()
            channel = Channel(**channel_info)
            db.merge(channel)
            db.commit()
            db.close()
            
            embed = discord.Embed(
                title="✅ Channel Added",
                description=f"**{channel_info['title']}** has been added to monitoring!",
                color=discord.Color.green()
            )
            embed.add_field(name="Subscribers", value=f"{channel_info['subscriber_count']:,}", inline=True)
            embed.add_field(name="Videos", value=f"{channel_info['video_count']}", inline=True)
            
            await interaction.followup.send(embed=embed)
            
        @self.discord_bot.tree.command(name="removechannel", description="Remove a channel from monitoring")
        async def removechannel(interaction: discord.Interaction, handle: str):
            """Remove a channel from monitoring"""
            await interaction.response.defer()
            
            db = SessionLocal()
            
            # Find channel by handle or name
            channel = db.query(Channel).filter(
                (Channel.title.ilike(f"%{handle}%")) |
                (Channel.channel_id.ilike(f"%{handle}%"))
            ).first()
            
            if not channel:
                await interaction.followup.send(f"Channel '{handle}' not found!")
                return
                
            channel_name = channel.title
            db.delete(channel)
            db.commit()
            db.close()
            
            embed = discord.Embed(
                title="❌ Channel Removed",
                description=f"**{channel_name}** has been removed from monitoring!",
                color=discord.Color.red()
            )
            
            await interaction.followup.send(embed=embed)
            
        # Add prefix commands using message events
        @self.discord_bot.event
        async def on_message(message):
            if message.author == self.discord_bot.user:
                return
                
            if message.content.startswith('!add_channel'):
                # Extract channel URL from message
                parts = message.content.split()
                if len(parts) < 2:
                    await message.channel.send("Usage: !add_channel <youtube_url>")
                    return
                    
                channel_url = parts[1]
                channel_id = self._extract_channel_id(channel_url)
                if not channel_id:
                    await message.channel.send("Invalid YouTube channel URL!")
                    return
                    
                # Fetch channel info
                channel_info = self.youtube_monitor.get_channel_info(channel_id)
                if not channel_info:
                    await message.channel.send("Could not fetch channel information!")
                    return
                    
                # Add to database
                db = SessionLocal()
                channel = Channel(**channel_info)
                db.merge(channel)
                db.commit()
                db.close()
                
                await message.channel.send(f"Added channel: **{channel_info['title']}** to monitoring list!")
                
            elif message.content.startswith('!list_channels'):
                db = SessionLocal()
                channels = db.query(Channel).filter_by(is_active=True).all()
                db.close()
                
                if not channels:
                    await message.channel.send("No channels being monitored!")
                    return
                    
                embed = discord.Embed(title="Monitored Channels", color=discord.Color.blue())
                for channel in channels:
                    embed.add_field(
                        name=channel.title,
                        value=f"Subscribers: {channel.subscriber_count:,}\nVideos: {channel.video_count}",
                        inline=True
                    )
                await message.channel.send(embed=embed)
                
            elif message.content.startswith('!list_shorts'):
                # Extract channel name if provided
                parts = message.content.split()
                channel_name = parts[1] if len(parts) > 1 else None
                
                db = SessionLocal()
                
                if channel_name:
                    # List shorts from specific channel
                    channel = db.query(Channel).filter(
                        Channel.title.ilike(f"%{channel_name}%")
                    ).first()
                    if not channel:
                        await message.channel.send(f"Channel '{channel_name}' not found!")
                        return
                        
                    videos = db.query(Video).filter(
                        Video.channel_id == channel.channel_id,
                        Video.is_short == True
                    ).order_by(Video.published_at.desc()).limit(10).all()
                    
                    embed = discord.Embed(
                        title=f"Recent Shorts from {channel.title}",
                        color=discord.Color.green()
                    )
                else:
                    # List shorts from all channels
                    videos = db.query(Video).filter(
                        Video.is_short == True
                    ).order_by(Video.published_at.desc()).limit(15).all()
                    
                    embed = discord.Embed(
                        title="Recent Shorts from All Channels",
                        color=discord.Color.green()
                    )
                
                db.close()
                
                if not videos:
                    await message.channel.send("No short videos found!")
                    return
                    
                for video in videos:
                    # Get channel info
                    channel = db.query(Channel).filter_by(channel_id=video.channel_id).first()
                    channel_name = channel.title if channel else "Unknown Channel"
                    
                    embed.add_field(
                        name=f"📱 {video.title[:50]}...",
                        value=f"**Channel**: {channel_name}\n"
                              f"**Duration**: {video.duration_seconds}s\n"
                              f"**Views**: {video.view_count:,}\n"
                              f"**Published**: {video.published_at.strftime('%Y-%m-%d %H:%M')}",
                        inline=False
                    )
                    
                await message.channel.send(embed=embed)
                
            elif message.content.startswith('!check_now'):
                await message.channel.send("Starting manual check of all channels for SHORTS...")
                await self.check_all_channels()
                await message.channel.send("Manual check completed!")
                
            elif message.content.startswith('!rotate_key'):
                current_key = self.youtube_monitor.current_key_index
                if self.youtube_monitor._rotate_api_key(force=True):
                    new_key = self.youtube_monitor.current_key_index
                    await message.channel.send(f"Rotated from API key {current_key} to key {new_key}")
                else:
                    await message.channel.send("Failed to rotate API key - all keys may be exhausted!")
                    
            elif message.content.startswith('!quota_reset'):
                now = datetime.now(timezone.utc)
                reset_time = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
                time_until_reset = reset_time - now
                
                hours = int(time_until_reset.total_seconds() // 3600)
                minutes = int((time_until_reset.total_seconds() % 3600) // 60)
                
                await message.channel.send(f"Quota resets in {hours}h {minutes}m (at midnight UTC)")
                
            elif message.content.startswith('!api_status'):
                quota_status = self.youtube_monitor.get_quota_status()
                
                embed = discord.Embed(title="API Key Detailed Status", color=discord.Color.blue())
                
                for key in quota_status:
                    # Determine health color
                    if not key['is_active']:
                        color = "🔴"
                    elif key['quota_remaining'] < 500:
                        color = "🟡"  
                    else:
                        color = "🟢"
                        
                    # Format last used time
                    last_used = "Never" if not key['last_used'] else key['last_used'].strftime("%H:%M UTC")
                    
                    embed.add_field(
                        name=f"{color} API Key {key['index']} (*{key['identifier']})",
                        value=f"**Quota**: {key['quota_used']:,} / 10,000\n"
                              f"**Remaining**: {key['quota_remaining']:,}\n"
                              f"**Last Used**: {last_used}\n"
                              f"**Errors**: {key['error_count']}",
                        inline=True
                    )
                    
                # Add current active key
                embed.add_field(
                    name="Currently Active",
                    value=f"Using API Key {self.youtube_monitor.current_key_index}",
                    inline=False
                )
                
                await message.channel.send(embed=embed)
                
            elif message.content.startswith('!stats'):
                # Show overall stats
                db = SessionLocal()
                total_channels = db.query(Channel).filter_by(is_active=True).count()
                total_shorts = db.query(Video).filter(Video.is_short == True).count()
                total_videos = db.query(Video).count()
                db.close()
                
                # Get quota status for all keys
                quota_status = self.youtube_monitor.get_quota_status()
                
                embed = discord.Embed(title="Bot Statistics", color=discord.Color.green())
                embed.add_field(name="Monitored Channels", value=total_channels, inline=True)
                embed.add_field(name="Total Videos", value=total_videos, inline=True)
                embed.add_field(name="Short Videos", value=total_shorts, inline=True)
                
                # Show quota for each API key
                total_used = sum(key['quota_used'] for key in quota_status)
                total_available = len(quota_status) * Config.DAILY_QUOTA_LIMIT
                
                embed.add_field(
                    name="Total Quota", 
                    value=f"{total_used:,} / {total_available:,} ({(total_used/total_available*100):.1f}%)", 
                    inline=True
                )
                
                # Individual key status
                key_status_text = []
                for key in quota_status:
                    status = "✅" if key['is_active'] and key['quota_remaining'] > 1000 else "⚠️" if key['quota_remaining'] > 0 else "❌"
                    key_status_text.append(
                        f"{status} Key {key['index']} (*{key['identifier']}): "
                        f"{key['quota_used']:,}/{Config.DAILY_QUOTA_LIMIT:,}"
                    )
                
                embed.add_field(
                    name="API Keys Status", 
                    value="\n".join(key_status_text), 
                    inline=False
                )
                
                await message.channel.send(embed=embed)
                
    def _extract_channel_id(self, url):
        """Extract channel ID from various YouTube URL formats"""
        import re
        
        # Handle different URL patterns
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
                
                # If it's already a channel ID (starts with UC)
                if identifier.startswith('UC'):
                    return identifier
                    
                # Otherwise, need to resolve it
                # This would require an additional API call to search
                # For now, return None for non-direct channel IDs
                return None
                
        # Try if it's just the channel ID
        if url.startswith('UC') and len(url) == 24:
            return url
            
        return None
        
    async def check_all_channels(self):
        """Check all monitored channels for new SHORT videos"""
        logger.info("Starting channel check cycle for SHORTS...")
        
        db = SessionLocal()
        channels = db.query(Channel).filter_by(is_active=True).all()
        db.close()
        
        for channel in channels:
            try:
                # Monitor channel for new SHORT videos
                new_videos = self.youtube_monitor.monitor_channel(channel.channel_id)
                
                # Check each SHORT video against threshold
                for video_data in new_videos:
                    await self.process_video(video_data, channel)
                    
                # Also check recent SHORT videos for threshold crossing
                await self.check_recent_videos(channel.channel_id)
                
            except Exception as e:
                logger.error(f"Error checking channel {channel.channel_id}: {e}")
                
            # Rate limiting between channels
            await asyncio.sleep(2)
            
        logger.info("Channel check cycle completed")
        
    async def check_recent_videos(self, channel_id):
        """Check recent SHORT videos for performance threshold"""
        db = SessionLocal()
        
        # Get SHORT videos from last 72 hours that haven't been notified
        cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
        recent_videos = db.query(Video).filter(
            Video.channel_id == channel_id,
            Video.published_at >= cutoff,
            Video.notified == False,
            Video.is_short == True  # Only check SHORT videos
        ).all()
        
        channel = db.query(Channel).filter_by(channel_id=channel_id).first()
        
        for video in recent_videos:
            # Check if SHORT video meets threshold
            is_above, performance = self.analytics.is_video_above_threshold(
                video.video_id, 
                Config.VIEW_THRESHOLD_PERCENTILE
            )
            
            if is_above and performance.get('hours_old', 0) >= 4:  # Wait at least 4 hours
                # Prepare video data
                video_data = {
                    'video_id': video.video_id,
                    'title': video.title,
                    'description': video.description,
                    'published_at': video.published_at.isoformat(),
                    'thumbnail_url': video.thumbnail_url,
                    'view_count': video.view_count,
                    'like_count': video.like_count,
                    'comment_count': video.comment_count,
                    'duration_seconds': video.duration_seconds,
                    'is_short': video.is_short
                }
                
                await self.send_notification(video_data, channel, performance)
                
                # Mark as notified
                video.notified = True
                db.commit()
                
        db.close()
        
    async def process_video(self, video_data, channel):
        """Process a new SHORT video"""
        # Wait a bit for initial views to accumulate
        logger.info(f"New SHORT video detected: {video_data['title']} ({video_data.get('duration_seconds', 0)}s)")
        
        # With hourly checks, videos will naturally have time to accumulate views
        # before being evaluated for the threshold
        pass
        
    async def send_notification(self, video_data, channel, performance):
        """Send notification to Discord for SHORT videos"""
        if not self.discord_bot:
            return
            
        try:
            # Get transcript for SHORT videos (often important for Reddit stories)
            transcript = self.transcript_handler.get_transcript(video_data['video_id'])
            if transcript:
                video_data['transcript_preview'] = self.transcript_handler.create_summary_preview(transcript)
            else:
                video_data['transcript_preview'] = "Transcript not available"
                
            # Create channel data dict
            channel_data = {
                'channel_id': channel.channel_id,
                'title': channel.title,
                'thumbnail_url': channel.thumbnail_url
            }
            
            # Create embed optimized for SHORTS
            embed = self.discord_bot.create_video_embed(video_data, channel_data, performance)
            
            # Send notification
            await self.discord_bot.send_notification(Config.DISCORD_CHANNEL_ID, embed)
            
            logger.info(f"SHORT video notification sent: {video_data['title']}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            
    def run_schedule(self):
        """Run scheduled tasks in separate thread"""
        while self.monitoring_active:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    async def start(self):
        """Start the monitoring system for SHORTS"""
        logger.info("Starting YouTube SHORTS Monitoring System...")
        
        # Initialize Discord bot
        await self.initialize_discord_bot()
        
        # Start Discord bot FIRST
        logger.info("Starting Discord bot...")
        
        # Create a task for the Discord bot
        bot_task = asyncio.create_task(self.discord_bot.start(Config.DISCORD_BOT_TOKEN))
        
        # Wait a moment for bot to connect
        await asyncio.sleep(2)
        
        # Schedule regular checks
        schedule.every(Config.CHECK_INTERVAL_MINUTES).minutes.do(
            lambda: asyncio.create_task(self.check_all_channels())
        )
        
        logger.info(f"Scheduled SHORTS checks every {Config.CHECK_INTERVAL_MINUTES} minutes")
        
        # Start schedule thread
        schedule_thread = threading.Thread(target=self.run_schedule)
        schedule_thread.daemon = True
        schedule_thread.start()
        
        # Run initial check
        await self.check_all_channels()
        
        # Keep the bot running
        await bot_task
        
    def stop(self):
        """Stop the monitoring system"""
        self.monitoring_active = False
        if self.discord_bot:
            asyncio.create_task(self.discord_bot.close())
        if self.youtube_monitor:
            self.youtube_monitor.close()
        if self.analytics:
            self.analytics.close()

# Main entry point
if __name__ == "__main__":
    system = YouTubeMonitoringSystem()
    
    try:
        asyncio.run(system.start())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        system.stop() 