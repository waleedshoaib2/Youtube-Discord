import discord
from discord import app_commands
import asyncio
from datetime import datetime
from config import Config

class YouTubeBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        
    async def setup_hook(self):
        # Commands will be synced in on_ready
        pass
        
    async def on_ready(self):
        print(f"✅ Bot is online!")
        print(f"🤖 Logged in as: {self.user} (ID: {self.user.id})")
        print(f"📊 Connected to {len(self.guilds)} servers")
        
        # Sync slash commands now that bot is ready
        try:
            await self.tree.sync()
            print(f"✅ Synced {len(self.tree.get_commands())} command(s)")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")
        
    async def send_notification(self, channel_id, embed):
        """Send notification to specified channel"""
        channel = self.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)
            
    def create_video_embed(self, video_data, channel_data, stats):
        """Create rich embed for video notification - optimized for shorts"""
        embed = discord.Embed(
            title=video_data['title'],
            url=f"https://youtube.com/watch?v={video_data['video_id']}",
            description=video_data['description'][:200] + "...",
            color=discord.Color.red(),
            timestamp=datetime.fromisoformat(video_data['published_at'])
        )
        
        embed.set_thumbnail(url=video_data['thumbnail_url'])
        embed.set_author(
            name=channel_data['title'],
            icon_url=channel_data['thumbnail_url'],
            url=f"https://youtube.com/channel/{channel_data['channel_id']}"
        )
        
        # Add short video indicator
        if video_data.get('is_short', False):
            embed.add_field(name="📱 Video Type", value="YouTube Short", inline=True)
            embed.add_field(name="⏱️ Duration", value=f"{video_data.get('duration_seconds', 0)}s", inline=True)
        else:
            embed.add_field(name="📺 Video Type", value="Regular Video", inline=True)
            embed.add_field(name="⏱️ Duration", value=f"{video_data.get('duration_seconds', 0)}s", inline=True)
        
        embed.add_field(name="👁️ Views", value=f"{video_data['view_count']:,}", inline=True)
        embed.add_field(name="👍 Likes", value=f"{video_data['like_count']:,}", inline=True)
        embed.add_field(name="💬 Comments", value=f"{video_data['comment_count']:,}", inline=True)
        
        embed.add_field(
            name="📊 Performance",
            value=f"**{stats['performance_ratio']:.1f}x** channel average\n"
                  f"Above {stats['percentile']}% of recent videos",
            inline=False
        )
        
        if video_data.get('transcript_preview'):
            embed.add_field(
                name="📝 Transcript Preview",
                value=video_data['transcript_preview'][:500] + "...",
                inline=False
            )
        
        # Custom footer for shorts
        if video_data.get('is_short', False):
            embed.set_footer(text="🔥 High-performing SHORT video detected!")
        else:
            embed.set_footer(text="High-performing video detected!")
            
        return embed 