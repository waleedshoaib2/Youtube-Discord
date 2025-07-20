# Complete Guide: YouTube Monitoring Discord Bot with API Key Rotation

> **Quick Setup**: Add multiple YouTube API keys in `.env` as:
> ```env
> YOUTUBE_API_KEYS=AIzaSy..._key1,AIzaSy..._key2,AIzaSy..._key3,AIzaSy..._key4
> ```
> This gives you 4x daily quota (40,000 units) automatically!

## 🔄 New Feature: Automatic API Key Rotation

This enhanced version includes automatic rotation between multiple YouTube API keys to maximize your daily quota:

- **4x More Quota**: Use 4 Gmail accounts = 40,000 daily quota
- **Automatic Switching**: Rotates keys when approaching limits
- **Error Recovery**: Switches keys on quota/auth errors
- **Smart Tracking**: Database tracks usage per key
- **Daily Reset**: Automatic quota reset at midnight UTC

**Bot Capacity**: With 4 API keys and hourly checks, you can monitor up to 555 channels!

## Table of Contents
1. [Project Setup & Prerequisites](#project-setup--prerequisites)
2. [YouTube API Setup](#youtube-api-setup)
3. [Discord Bot Setup](#discord-bot-setup)
4. [Database Design](#database-design)
5. [Core Implementation](#core-implementation)
6. [Monitoring System](#monitoring-system)
7. [View Analytics & Thresholds](#view-analytics--thresholds)
8. [Transcript Extraction](#transcript-extraction)
9. [Complete Working Bot](#complete-working-bot)
10. [Deployment & Maintenance](#deployment--maintenance)

## Project Setup & Prerequisites

### Required Libraries
```bash
pip install discord.py google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip install sqlalchemy asyncio python-dotenv youtube-transcript-api
pip install aiohttp numpy pandas schedule
```

### Project Structure
```
youtube-discord-bot/
├── .env
├── config.py
├── database.py
├── youtube_monitor.py
├── discord_bot.py
├── analytics.py
├── transcript_handler.py
├── main.py
└── requirements.txt
```

## YouTube API Setup

### 1. Enable YouTube Data API v3
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. For production, also create OAuth 2.0 credentials

### 2. Configuration File (.env)
```env
# YouTube API Keys (comma-separated for rotation)
YOUTUBE_API_KEYS=key1_from_account1,key2_from_account2,key3_from_account3,key4_from_account4

# Discord
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here

# Database
DATABASE_URL=sqlite:///youtube_monitor.db

# Monitoring Settings
CHECK_INTERVAL_MINUTES=60  # Check every hour (more efficient)
VIEW_THRESHOLD_PERCENTILE=75

# API Quota Settings
QUOTA_WARNING_THRESHOLD=8000  # Switch keys at 80% usage
QUOTA_EMERGENCY_THRESHOLD=9500  # Emergency switch at 95%
```

### 3. Config Module (config.py)
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # YouTube API Keys (multiple for rotation)
    YOUTUBE_API_KEYS = os.getenv('YOUTUBE_API_KEYS', '').split(',')
    
    # Discord
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///youtube_monitor.db')
    
    # Monitoring Settings
    CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', 60))
    VIEW_THRESHOLD_PERCENTILE = int(os.getenv('VIEW_THRESHOLD_PERCENTILE', 75))
    
    # API Quotas
    MAX_RESULTS_PER_REQUEST = 50
    QUOTA_COST_PER_LIST = 1
    DAILY_QUOTA_LIMIT = 10000
    QUOTA_WARNING_THRESHOLD = int(os.getenv('QUOTA_WARNING_THRESHOLD', 8000))
    QUOTA_EMERGENCY_THRESHOLD = int(os.getenv('QUOTA_EMERGENCY_THRESHOLD', 9500))
```

## Discord Bot Setup

### 1. Create Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application
3. Go to Bot section
4. Create a Bot and copy the token
5. Enable necessary intents (especially message content)
6. Generate invite link with bot permissions

### 2. Basic Discord Bot (discord_bot.py)
```python
import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime
from config import Config

class YouTubeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
    async def setup_hook(self):
        # Start background tasks when bot is ready
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        
    async def send_notification(self, channel_id, embed):
        """Send notification to specified channel"""
        channel = self.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)
            
    def create_video_embed(self, video_data, channel_data, stats):
        """Create rich embed for video notification"""
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
        
        embed.add_field(name="Views", value=f"{video_data['view_count']:,}", inline=True)
        embed.add_field(name="Likes", value=f"{video_data['like_count']:,}", inline=True)
        embed.add_field(name="Comments", value=f"{video_data['comment_count']:,}", inline=True)
        
        embed.add_field(
            name="Performance",
            value=f"**{stats['performance_ratio']:.1f}x** channel average\n"
                  f"Above {stats['percentile']}% of recent videos",
            inline=False
        )
        
        if video_data.get('transcript_preview'):
            embed.add_field(
                name="Transcript Preview",
                value=video_data['transcript_preview'][:500] + "...",
                inline=False
            )
        
        embed.set_footer(text="High-performing video detected!")
        return embed
```

## Database Design

### Database Models (database.py)
```python
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config

Base = declarative_base()
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class Channel(Base):
    __tablename__ = 'channels'
    
    channel_id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    subscriber_count = Column(Integer)
    video_count = Column(Integer)
    thumbnail_url = Column(String)
    upload_playlist_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime)
    is_active = Column(Boolean, default=True)

class Video(Base):
    __tablename__ = 'videos'
    
    video_id = Column(String, primary_key=True)
    channel_id = Column(String, index=True)
    title = Column(String)
    description = Column(Text)
    published_at = Column(DateTime)
    duration = Column(String)
    thumbnail_url = Column(String)
    
    # Statistics
    view_count = Column(Integer)
    like_count = Column(Integer)
    comment_count = Column(Integer)
    
    # Tracking
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)
    
class ViewSnapshot(Base):
    __tablename__ = 'view_snapshots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String, index=True)
    view_count = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    hours_since_upload = Column(Float)

class ChannelStats(Base):
    __tablename__ = 'channel_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, index=True)
    date = Column(DateTime)
    avg_views_24h = Column(Float)
    avg_views_7d = Column(Float)
    avg_views_30d = Column(Float)
    percentile_75 = Column(Float)
    percentile_90 = Column(Float)

class ApiKeyUsage(Base):
    __tablename__ = 'api_key_usage'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    api_key_index = Column(Integer)  # Index in the API keys list
    api_key_identifier = Column(String)  # Last 6 chars of key for identification
    quota_used = Column(Integer, default=0)
    last_reset = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    error_count = Column(Integer, default=0)
    last_error = Column(DateTime)

# Create tables
Base.metadata.create_all(engine)
```

## Core Implementation

### YouTube API Client (youtube_monitor.py)
```python
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import time
from config import Config
from database import SessionLocal, Channel, Video, ViewSnapshot, ApiKeyUsage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeMonitor:
    def __init__(self):
        self.api_keys = Config.YOUTUBE_API_KEYS
        self.current_key_index = 0
        self.youtube = None
        self.db = SessionLocal()
        
        # Initialize API key tracking
        self._initialize_api_keys()
        self._build_youtube_client()
        
    def _initialize_api_keys(self):
        """Initialize or update API key usage tracking"""
        for i, api_key in enumerate(self.api_keys):
            if api_key:
                # Use last 6 chars as identifier (for logging without exposing full key)
                identifier = api_key[-6:]
                
                # Check if key exists in database
                key_usage = self.db.query(ApiKeyUsage).filter_by(
                    api_key_index=i
                ).first()
                
                if not key_usage:
                    key_usage = ApiKeyUsage(
                        api_key_index=i,
                        api_key_identifier=identifier,
                        quota_used=0,
                        last_reset=datetime.utcnow().replace(hour=0, minute=0, second=0)
                    )
                    self.db.add(key_usage)
                    
                # Reset if new day
                self._check_quota_reset(key_usage)
                    
        self.db.commit()
        
    def _check_quota_reset(self, key_usage):
        """Check if quota should be reset for a key"""
        now = datetime.utcnow()
        if now.date() > key_usage.last_reset.date():
            key_usage.quota_used = 0
            key_usage.last_reset = now.replace(hour=0, minute=0, second=0)
            key_usage.error_count = 0
            logger.info(f"Reset quota for API key {key_usage.api_key_identifier}")
            
    def _build_youtube_client(self):
        """Build YouTube client with current API key"""
        if self.current_key_index < len(self.api_keys):
            self.youtube = build('youtube', 'v3', 
                               developerKey=self.api_keys[self.current_key_index])
            logger.info(f"Using API key index {self.current_key_index}")
        else:
            raise Exception("No valid API keys available")
            
    def _get_current_key_usage(self):
        """Get current API key usage record"""
        return self.db.query(ApiKeyUsage).filter_by(
            api_key_index=self.current_key_index
        ).first()
        
    def _should_rotate_key(self, key_usage):
        """Check if we should rotate to next API key"""
        # Check quota threshold
        if key_usage.quota_used >= Config.QUOTA_WARNING_THRESHOLD:
            return True
            
        # Check error count (rotate after 3 consecutive errors)
        if key_usage.error_count >= 3:
            return True
            
        return False
        
    def _rotate_api_key(self, force=False):
        """Rotate to next available API key"""
        original_index = self.current_key_index
        attempts = 0
        
        while attempts < len(self.api_keys):
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            
            key_usage = self._get_current_key_usage()
            self._check_quota_reset(key_usage)
            
            # Skip if key is disabled
            if not key_usage.is_active:
                attempts += 1
                continue
                
            # Skip if quota exceeded (unless forced or quota reset)
            if not force and key_usage.quota_used >= Config.QUOTA_EMERGENCY_THRESHOLD:
                attempts += 1
                continue
                
            # Found a usable key
            self._build_youtube_client()
            logger.info(f"Rotated from key {original_index} to {self.current_key_index} "
                       f"(quota: {key_usage.quota_used}/{Config.DAILY_QUOTA_LIMIT})")
            return True
            
        logger.error("No available API keys with remaining quota!")
        return False
        
    def _handle_api_error(self, error):
        """Handle API errors and rotate keys if necessary"""
        key_usage = self._get_current_key_usage()
        key_usage.error_count += 1
        key_usage.last_error = datetime.utcnow()
        
        if hasattr(error, 'resp') and error.resp.status == 403:
            # Quota exceeded error
            if 'quotaExceeded' in str(error):
                logger.warning(f"Quota exceeded for key {key_usage.api_key_identifier}")
                key_usage.quota_used = Config.DAILY_QUOTA_LIMIT
                self.db.commit()
                
                # Try to rotate to another key
                if self._rotate_api_key():
                    return True
                    
        elif hasattr(error, 'resp') and error.resp.status == 400:
            # Bad request - might be invalid API key
            if 'API key not valid' in str(error):
                logger.error(f"Invalid API key {key_usage.api_key_identifier}")
                key_usage.is_active = False
                self.db.commit()
                
                # Try to rotate to another key
                if self._rotate_api_key():
                    return True
                    
        self.db.commit()
        return False
        
    def add_quota_usage(self, units):
        """Track quota usage for current key"""
        key_usage = self._get_current_key_usage()
        self._check_quota_reset(key_usage)
        
        key_usage.quota_used += units
        key_usage.last_used = datetime.utcnow()
        key_usage.error_count = 0  # Reset error count on successful use
        
        remaining = Config.DAILY_QUOTA_LIMIT - key_usage.quota_used
        logger.info(f"Key {key_usage.api_key_identifier}: "
                   f"Used {units} units ({key_usage.quota_used}/{Config.DAILY_QUOTA_LIMIT})")
        
        # Check if we should preemptively rotate
        if self._should_rotate_key(key_usage):
            logger.info("Preemptively rotating API key due to quota threshold")
            self._rotate_api_key()
            
        self.db.commit()
        
    def get_quota_status(self):
        """Get quota status for all API keys"""
        status = []
        for i in range(len(self.api_keys)):
            key_usage = self.db.query(ApiKeyUsage).filter_by(api_key_index=i).first()
            if key_usage:
                self._check_quota_reset(key_usage)
                status.append({
                    'index': i,
                    'identifier': key_usage.api_key_identifier,
                    'quota_used': key_usage.quota_used,
                    'quota_remaining': Config.DAILY_QUOTA_LIMIT - key_usage.quota_used,
                    'is_active': key_usage.is_active,
                    'last_used': key_usage.last_used,
                    'error_count': key_usage.error_count
                })
        return status
        
    def _api_request_with_retry(self, request_func, *args, **kwargs):
        """Execute API request with retry and key rotation"""
        max_retries = len(self.api_keys) + 1
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Execute the request
                result = request_func(*args, **kwargs)
                return result
                
            except HttpError as e:
                last_error = e
                logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
                
                # Try to handle the error and rotate key
                if not self._handle_api_error(e):
                    # If we can't rotate, raise the error
                    raise
                    
            except Exception as e:
                # Non-API errors
                logger.error(f"Unexpected error: {e}")
                raise
                
        # If we get here, all retries failed
        raise last_error or Exception("All API keys exhausted")
        
    def get_channel_info(self, channel_id):
        """Fetch channel information with automatic key rotation"""
        def make_request():
            request = self.youtube.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id
            )
            response = request.execute()
            self.add_quota_usage(1)
            return response
            
        try:
            response = self._api_request_with_retry(make_request)
            
            if not response['items']:
                return None
                
            channel = response['items'][0]
            return {
                'channel_id': channel['id'],
                'title': channel['snippet']['title'],
                'description': channel['snippet']['description'],
                'subscriber_count': int(channel['statistics'].get('subscriberCount', 0)),
                'video_count': int(channel['statistics'].get('videoCount', 0)),
                'thumbnail_url': channel['snippet']['thumbnails']['high']['url'],
                'upload_playlist_id': channel['contentDetails']['relatedPlaylists']['uploads']
            }
        except Exception as e:
            logger.error(f"Error fetching channel {channel_id}: {e}")
            return None
            
    def get_playlist_videos(self, playlist_id, max_results=50):
        """Fetch videos from playlist with automatic key rotation"""
        videos = []
        next_page_token = None
        
        while len(videos) < max_results:
            def make_request():
                request = self.youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                )
                response = request.execute()
                self.add_quota_usage(1)
                return response
                
            try:
                response = self._api_request_with_retry(make_request)
                
                for item in response.get('items', []):
                    video_data = {
                        'video_id': item['contentDetails']['videoId'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'published_at': item['snippet']['publishedAt'],
                        'thumbnail_url': item['snippet']['thumbnails']['high']['url'],
                        'channel_id': item['snippet']['channelId']
                    }
                    videos.append(video_data)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching playlist videos: {e}")
                break
                
        return videos
        
    def get_video_statistics(self, video_ids):
        """Fetch detailed statistics for videos with automatic key rotation"""
        if not video_ids:
            return {}
            
        stats = {}
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            
            def make_request():
                request = self.youtube.videos().list(
                    part="statistics,contentDetails",
                    id=','.join(batch_ids)
                )
                response = request.execute()
                self.add_quota_usage(1)
                return response
                
            try:
                response = self._api_request_with_retry(make_request)
                
                for item in response.get('items', []):
                    stats[item['id']] = {
                        'view_count': int(item['statistics'].get('viewCount', 0)),
                        'like_count': int(item['statistics'].get('likeCount', 0)),
                        'comment_count': int(item['statistics'].get('commentCount', 0)),
                        'duration': item['contentDetails']['duration']
                    }
                    
            except Exception as e:
                logger.error(f"Error fetching video statistics: {e}")
                # Continue with partial results
                
        return stats
        
    def monitor_channel(self, channel_id):
        """Complete monitoring flow for a channel"""
        try:
            # Get or update channel info
            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                return
                
            # Update database
            channel = self.db.query(Channel).filter_by(channel_id=channel_id).first()
            if not channel:
                channel = Channel(**channel_info)
                self.db.add(channel)
            else:
                for key, value in channel_info.items():
                    setattr(channel, key, value)
            channel.last_checked = datetime.utcnow()
            
            # Get recent videos
            videos = self.get_playlist_videos(channel_info['upload_playlist_id'], max_results=50)
            
            # Get video statistics
            video_ids = [v['video_id'] for v in videos]
            stats = self.get_video_statistics(video_ids)
            
            # Process each video
            new_videos = []
            for video_data in videos:
                video_id = video_data['video_id']
                if video_id not in stats:
                    continue
                    
                # Merge stats into video data
                video_data.update(stats[video_id])
                
                # Check if video exists
                video = self.db.query(Video).filter_by(video_id=video_id).first()
                if not video:
                    video = Video(**video_data)
                    self.db.add(video)
                    new_videos.append(video_data)
                else:
                    # Update statistics
                    for key in ['view_count', 'like_count', 'comment_count']:
                        setattr(video, key, video_data[key])
                    video.last_updated = datetime.utcnow()
                    
                # Record view snapshot
                hours_since_upload = (datetime.utcnow() - datetime.fromisoformat(
                    video_data['published_at'].replace('Z', '+00:00')
                )).total_seconds() / 3600
                
                snapshot = ViewSnapshot(
                    video_id=video_id,
                    view_count=video_data['view_count'],
                    hours_since_upload=hours_since_upload
                )
                self.db.add(snapshot)
                
            self.db.commit()
            return new_videos
            
        except Exception as e:
            logger.error(f"Error monitoring channel {channel_id}: {e}")
            self.db.rollback()
            return []
            
    def close(self):
        """Clean up database connection"""
        self.db.close()
```

## View Analytics & Thresholds

### Analytics Module (analytics.py)
```python
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import func
from database import SessionLocal, Video, ViewSnapshot, ChannelStats
import logging

logger = logging.getLogger(__name__)

class VideoAnalytics:
    def __init__(self):
        self.db = SessionLocal()
        
    def calculate_channel_statistics(self, channel_id, days=30):
        """Calculate channel performance statistics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get recent videos
        recent_videos = self.db.query(Video).filter(
            Video.channel_id == channel_id,
            Video.published_at >= cutoff_date
        ).all()
        
        if not recent_videos:
            return None
            
        # Calculate normalized views (views per hour in first 24h)
        normalized_views = []
        for video in recent_videos:
            # Get first 24h snapshot or estimate
            first_snapshot = self.db.query(ViewSnapshot).filter(
                ViewSnapshot.video_id == video.video_id,
                ViewSnapshot.hours_since_upload <= 24
            ).order_by(ViewSnapshot.hours_since_upload.desc()).first()
            
            if first_snapshot:
                # Normalize to 24 hours
                views_per_hour = first_snapshot.view_count / max(first_snapshot.hours_since_upload, 1)
                normalized_24h_views = views_per_hour * 24
                normalized_views.append(normalized_24h_views)
            elif video.view_count > 0:
                # Fallback: use current views with age adjustment
                hours_old = (datetime.utcnow() - video.published_at).total_seconds() / 3600
                if hours_old < 24:
                    normalized_24h_views = (video.view_count / hours_old) * 24
                else:
                    # Apply decay factor for older videos
                    decay_factor = 24 / min(hours_old, 168)  # Cap at 1 week
                    normalized_24h_views = video.view_count * decay_factor
                normalized_views.append(normalized_24h_views)
                
        if not normalized_views:
            return None
            
        # Calculate statistics
        stats = {
            'channel_id': channel_id,
            'date': datetime.utcnow(),
            'avg_views_24h': np.mean(normalized_views),
            'avg_views_7d': self._calculate_period_average(channel_id, 7),
            'avg_views_30d': self._calculate_period_average(channel_id, 30),
            'percentile_75': np.percentile(normalized_views, 75),
            'percentile_90': np.percentile(normalized_views, 90),
            'median_views': np.median(normalized_views),
            'std_dev': np.std(normalized_views)
        }
        
        # Save to database
        channel_stat = ChannelStats(**{k: v for k, v in stats.items() 
                                     if k in ['channel_id', 'date', 'avg_views_24h', 
                                            'avg_views_7d', 'avg_views_30d', 
                                            'percentile_75', 'percentile_90']})
        self.db.add(channel_stat)
        self.db.commit()
        
        return stats
        
    def _calculate_period_average(self, channel_id, days):
        """Calculate average views for specific period"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        avg_views = self.db.query(func.avg(Video.view_count)).filter(
            Video.channel_id == channel_id,
            Video.published_at >= cutoff_date
        ).scalar()
        
        return float(avg_views) if avg_views else 0
        
    def is_video_above_threshold(self, video_id, percentile=75):
        """Check if video performs above threshold"""
        video = self.db.query(Video).filter_by(video_id=video_id).first()
        if not video:
            return False, {}
            
        # Get latest channel statistics
        channel_stats = self.db.query(ChannelStats).filter_by(
            channel_id=video.channel_id
        ).order_by(ChannelStats.date.desc()).first()
        
        if not channel_stats:
            # Calculate if not exists
            stats_dict = self.calculate_channel_statistics(video.channel_id)
            if not stats_dict:
                return False, {}
            channel_stats = self.db.query(ChannelStats).filter_by(
                channel_id=video.channel_id
            ).order_by(ChannelStats.date.desc()).first()
            
        # Get normalized view count for comparison
        hours_old = (datetime.utcnow() - video.published_at).total_seconds() / 3600
        
        if hours_old < 24:
            normalized_views = (video.view_count / hours_old) * 24
        else:
            normalized_views = video.view_count
            
        # Compare against thresholds
        threshold_value = getattr(channel_stats, f'percentile_{percentile}', 0)
        is_above = normalized_views > threshold_value
        
        performance_data = {
            'current_views': video.view_count,
            'normalized_views': normalized_views,
            'threshold': threshold_value,
            'percentile': percentile,
            'performance_ratio': normalized_views / channel_stats.avg_views_24h if channel_stats.avg_views_24h > 0 else 0,
            'hours_old': hours_old
        }
        
        return is_above, performance_data
        
    def get_trending_videos(self, channel_id=None, limit=10):
        """Get currently trending videos based on view velocity"""
        query = self.db.query(Video)
        if channel_id:
            query = query.filter(Video.channel_id == channel_id)
            
        recent_videos = query.filter(
            Video.published_at >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        trending = []
        for video in recent_videos:
            # Calculate view velocity
            snapshots = self.db.query(ViewSnapshot).filter(
                ViewSnapshot.video_id == video.video_id
            ).order_by(ViewSnapshot.timestamp).all()
            
            if len(snapshots) >= 2:
                # Calculate views per hour over last period
                latest = snapshots[-1]
                earlier = snapshots[max(0, len(snapshots)-5)]
                
                time_diff = (latest.timestamp - earlier.timestamp).total_seconds() / 3600
                view_diff = latest.view_count - earlier.view_count
                
                if time_diff > 0:
                    velocity = view_diff / time_diff
                    trending.append({
                        'video': video,
                        'velocity': velocity,
                        'current_views': latest.view_count,
                        'growth_rate': (view_diff / earlier.view_count * 100) if earlier.view_count > 0 else 0
                    })
                    
        # Sort by velocity
        trending.sort(key=lambda x: x['velocity'], reverse=True)
        return trending[:limit]
        
    def close(self):
        self.db.close()
```

## Transcript Extraction

### Transcript Handler (transcript_handler.py)
```python
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
import logging

logger = logging.getLogger(__name__)

class TranscriptHandler:
    def __init__(self):
        self.supported_languages = ['en', 'es', 'fr', 'de', 'ja', 'ko', 'pt', 'ru']
        
    def get_transcript(self, video_id, preferred_language='en'):
        """Fetch transcript for a video"""
        try:
            # Try to get manual transcript first
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Check for manual transcripts
            try:
                transcript = transcript_list.find_manually_created_transcript([preferred_language])
                return self._format_transcript(transcript.fetch())
            except:
                pass
                
            # Fall back to auto-generated
            try:
                transcript = transcript_list.find_generated_transcript([preferred_language])
                return self._format_transcript(transcript.fetch())
            except:
                # Try any available language
                for transcript in transcript_list:
                    if transcript.language_code in self.supported_languages:
                        return self._format_transcript(transcript.fetch())
                        
        except (NoTranscriptFound, TranscriptsDisabled) as e:
            logger.warning(f"No transcript available for video {video_id}: {e}")
        except Exception as e:
            logger.error(f"Error fetching transcript for {video_id}: {e}")
            
        return None
        
    def _format_transcript(self, transcript_data):
        """Format transcript data into readable text"""
        if not transcript_data:
            return None
            
        # Combine all text segments
        full_text = ' '.join([segment['text'] for segment in transcript_data])
        
        # Create time-stamped version
        timestamped = []
        for segment in transcript_data:
            time = self._seconds_to_time(segment['start'])
            timestamped.append(f"[{time}] {segment['text']}")
            
        return {
            'full_text': full_text,
            'timestamped': '\n'.join(timestamped),
            'segments': transcript_data,
            'duration': transcript_data[-1]['start'] + transcript_data[-1]['duration'] if transcript_data else 0
        }
        
    def _seconds_to_time(self, seconds):
        """Convert seconds to MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
        
    def extract_key_segments(self, transcript_data, max_segments=5):
        """Extract most important segments based on length and position"""
        if not transcript_data or not transcript_data.get('segments'):
            return []
            
        segments = transcript_data['segments']
        
        # Score segments based on length and position
        scored_segments = []
        total_duration = transcript_data['duration']
        
        for i, segment in enumerate(segments):
            # Favor longer segments
            length_score = len(segment['text'].split())
            
            # Favor segments from important parts (beginning, middle, end)
            position = segment['start'] / total_duration if total_duration > 0 else 0
            if position < 0.1:  # Beginning
                position_score = 1.5
            elif 0.4 < position < 0.6:  # Middle
                position_score = 1.2
            elif position > 0.9:  # End
                position_score = 1.3
            else:
                position_score = 1.0
                
            total_score = length_score * position_score
            scored_segments.append((segment, total_score))
            
        # Sort by score and return top segments
        scored_segments.sort(key=lambda x: x[1], reverse=True)
        return [seg[0] for seg in scored_segments[:max_segments]]
        
    def create_summary_preview(self, transcript_data, max_length=500):
        """Create a preview summary from transcript"""
        if not transcript_data:
            return "No transcript available"
            
        # Use key segments for summary
        key_segments = self.extract_key_segments(transcript_data, max_segments=3)
        
        if key_segments:
            summary = ' '.join([seg['text'] for seg in key_segments])
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            return summary
        else:
            # Fallback to beginning of transcript
            full_text = transcript_data.get('full_text', '')
            if len(full_text) > max_length:
                return full_text[:max_length-3] + "..."
            return full_text
```

## Complete Working Bot

### Main Application (main.py)
```python
import asyncio
import schedule
import threading
import time
from datetime import datetime, timedelta
import logging
import discord
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
        
        # Add commands
        @self.discord_bot.command(name='add_channel')
        async def add_channel(ctx, channel_url: str):
            """Add a YouTube channel to monitor"""
            # Extract channel ID from URL
            channel_id = self._extract_channel_id(channel_url)
            if not channel_id:
                await ctx.send("Invalid YouTube channel URL!")
                return
                
            # Fetch channel info
            channel_info = self.youtube_monitor.get_channel_info(channel_id)
            if not channel_info:
                await ctx.send("Could not fetch channel information!")
                return
                
            # Add to database
            db = SessionLocal()
            channel = Channel(**channel_info)
            db.merge(channel)
            db.commit()
            db.close()
            
            await ctx.send(f"Added channel: **{channel_info['title']}** to monitoring list!")
            
        @self.discord_bot.command(name='list_channels')
        async def list_channels(ctx):
            """List all monitored channels"""
            db = SessionLocal()
            channels = db.query(Channel).filter_by(is_active=True).all()
            db.close()
            
            if not channels:
                await ctx.send("No channels being monitored!")
                return
                
            embed = discord.Embed(title="Monitored Channels", color=discord.Color.blue())
            for channel in channels:
                embed.add_field(
                    name=channel.title,
                    value=f"Subscribers: {channel.subscriber_count:,}\nVideos: {channel.video_count}",
                    inline=True
                )
            await ctx.send(embed=embed)
            
        @self.discord_bot.command(name='check_now')
        async def check_now(ctx):
            """Manually trigger channel check"""
            await ctx.send("Starting manual check of all channels...")
            await self.check_all_channels()
            await ctx.send("Manual check completed!")
            
        @self.discord_bot.command(name='rotate_key')
        async def rotate_key(ctx):
            """Manually rotate to next API key"""
            current_key = self.youtube_monitor.current_key_index
            if self.youtube_monitor._rotate_api_key(force=True):
                new_key = self.youtube_monitor.current_key_index
                await ctx.send(f"Rotated from API key {current_key} to key {new_key}")
            else:
                await ctx.send("Failed to rotate API key - all keys may be exhausted!")
                
        @self.discord_bot.command(name='quota_reset')
        async def quota_reset(ctx):
            """Show time until quota reset"""
            now = datetime.utcnow()
            reset_time = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
            time_until_reset = reset_time - now
            
            hours = int(time_until_reset.total_seconds() // 3600)
            minutes = int((time_until_reset.total_seconds() % 3600) // 60)
            
            await ctx.send(f"Quota resets in {hours}h {minutes}m (at midnight UTC)")
            
        @self.discord_bot.command(name='api_status')
        async def api_status(ctx):
            """Show detailed API key status"""
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
            
            await ctx.send(embed=embed)
            
        @self.discord_bot.command(name='stats')
        async def stats(ctx, channel_url: str = None):
            """Show channel statistics"""
            if channel_url:
                channel_id = self._extract_channel_id(channel_url)
                if not channel_id:
                    await ctx.send("Invalid YouTube channel URL!")
                    return
            else:
                # Show overall stats
                db = SessionLocal()
                total_channels = db.query(Channel).filter_by(is_active=True).count()
                db.close()
                
                # Get quota status for all keys
                quota_status = self.youtube_monitor.get_quota_status()
                
                embed = discord.Embed(title="Bot Statistics", color=discord.Color.green())
                embed.add_field(name="Monitored Channels", value=total_channels, inline=True)
                
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
                
                await ctx.send(embed=embed)
                return
                
            # Show channel-specific stats
            stats = self.analytics.calculate_channel_statistics(channel_id)
            if not stats:
                await ctx.send("No statistics available for this channel!")
                return
                
            embed = discord.Embed(title="Channel Statistics", color=discord.Color.purple())
            embed.add_field(name="Avg Views (24h)", value=f"{int(stats['avg_views_24h']):,}", inline=True)
            embed.add_field(name="75th Percentile", value=f"{int(stats['percentile_75']):,}", inline=True)
            embed.add_field(name="90th Percentile", value=f"{int(stats['percentile_90']):,}", inline=True)
            await ctx.send(embed=embed)
            
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
        """Check all monitored channels for new videos"""
        logger.info("Starting channel check cycle...")
        
        db = SessionLocal()
        channels = db.query(Channel).filter_by(is_active=True).all()
        db.close()
        
        for channel in channels:
            try:
                # Monitor channel for new videos
                new_videos = self.youtube_monitor.monitor_channel(channel.channel_id)
                
                # Check each video against threshold
                for video_data in new_videos:
                    await self.process_video(video_data, channel)
                    
                # Also check recent videos for threshold crossing
                await self.check_recent_videos(channel.channel_id)
                
            except Exception as e:
                logger.error(f"Error checking channel {channel.channel_id}: {e}")
                
            # Rate limiting between channels
            await asyncio.sleep(2)
            
        logger.info("Channel check cycle completed")
        
    async def check_recent_videos(self, channel_id):
        """Check recent videos for performance threshold"""
        db = SessionLocal()
        
        # Get videos from last 72 hours that haven't been notified
        # (Longer window since we check hourly now)
        cutoff = datetime.utcnow() - timedelta(hours=72)
        recent_videos = db.query(Video).filter(
            Video.channel_id == channel_id,
            Video.published_at >= cutoff,
            Video.notified == False
        ).all()
        
        channel = db.query(Channel).filter_by(channel_id=channel_id).first()
        
        for video in recent_videos:
            # Check if video meets threshold
            is_above, performance = self.analytics.is_video_above_threshold(
                video.video_id, 
                Config.VIEW_THRESHOLD_PERCENTILE
            )
            
            if is_above and performance.get('hours_old', 0) >= 4:  # Wait at least 4 hours
                # With hourly checks, this means a video is checked ~4 times
                # before potentially triggering a notification, ensuring accurate detection
                # Prepare video data
                video_data = {
                    'video_id': video.video_id,
                    'title': video.title,
                    'description': video.description,
                    'published_at': video.published_at.isoformat(),
                    'thumbnail_url': video.thumbnail_url,
                    'view_count': video.view_count,
                    'like_count': video.like_count,
                    'comment_count': video.comment_count
                }
                
                await self.send_notification(video_data, channel, performance)
                
                # Mark as notified
                video.notified = True
                db.commit()
                
        db.close()
        
    async def process_video(self, video_data, channel):
        """Process a new video"""
        # Wait a bit for initial views to accumulate
        logger.info(f"New video detected: {video_data['title']}")
        
        # With hourly checks, videos will naturally have time to accumulate views
        # before being evaluated for the threshold
        pass
        
    async def send_notification(self, video_data, channel, performance):
        """Send notification to Discord"""
        if not self.discord_bot:
            return
            
        try:
            # Get transcript
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
            
            # Create embed
            embed = self.discord_bot.create_video_embed(video_data, channel_data, performance)
            
            # Send notification
            await self.discord_bot.send_notification(Config.DISCORD_CHANNEL_ID, embed)
            
            logger.info(f"Notification sent for video: {video_data['title']}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            
    def run_schedule(self):
        """Run scheduled tasks in separate thread"""
        while self.monitoring_active:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    async def start(self):
        """Start the monitoring system"""
        logger.info("Starting YouTube Monitoring System...")
        
        # Initialize Discord bot
        await self.initialize_discord_bot()
        
        # Schedule regular checks
        schedule.every(Config.CHECK_INTERVAL_MINUTES).minutes.do(
            lambda: asyncio.create_task(self.check_all_channels())
        )
        
        logger.info(f"Scheduled checks every {Config.CHECK_INTERVAL_MINUTES} minutes")
        
        # Start schedule thread
        schedule_thread = threading.Thread(target=self.run_schedule)
        schedule_thread.daemon = True
        schedule_thread.start()
        
        # Run initial check
        await self.check_all_channels()
        
        # Start Discord bot
        await self.discord_bot.start(Config.DISCORD_BOT_TOKEN)
        
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
```

## Deployment & Maintenance

### Requirements File (requirements.txt)
```
discord.py>=2.3.0
google-api-python-client>=2.100.0
google-auth-httplib2>=0.1.1
google-auth-oauthlib>=1.0.0
sqlalchemy>=2.0.0
python-dotenv>=1.0.0
youtube-transcript-api>=0.6.0
aiohttp>=3.8.0
numpy>=1.24.0
pandas>=2.0.0
schedule>=1.2.0
```

### Docker Deployment (Dockerfile)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create volume for database
VOLUME ["/app/data"]

# Set environment variable for database location
ENV DATABASE_URL=sqlite:////app/data/youtube_monitor.db

# Run the bot
CMD ["python", "main.py"]
```

### Docker Compose (docker-compose.yml)
```yaml
version: '3.8'

services:
  youtube-bot:
    build: .
    container_name: youtube-discord-bot
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    environment:
      - TZ=UTC
```

### Deployment Steps

1. **VPS Setup (DigitalOcean/Linode)**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Clone repository
git clone https://github.com/yourusername/youtube-discord-bot.git
cd youtube-discord-bot

# Create .env file with your credentials
nano .env

# Build and run
docker-compose up -d
```

2. **Monitoring & Logs**
```bash
# View logs
docker-compose logs -f

# Check bot status
docker-compose ps

# Restart bot
docker-compose restart
```

3. **Backup Strategy**
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups/youtube-bot"
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec youtube-bot sqlite3 /app/data/youtube_monitor.db ".backup '$BACKUP_DIR/youtube_monitor_$(date +%Y%m%d).db'"

# Keep only last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
```

4. **Monitoring Script**
```python
# monitor_health.py
import requests
import smtplib
from email.mime.text import MIMEText

def check_bot_health():
    # Implement health check endpoint in your bot
    try:
        response = requests.get("http://localhost:8080/health")
        if response.status_code != 200:
            send_alert("Bot health check failed!")
    except:
        send_alert("Bot is not responding!")

def send_alert(message):
    # Send email alert
    msg = MIMEText(message)
    msg['Subject'] = 'YouTube Bot Alert'
    msg['From'] = 'bot@yourdomain.com'
    msg['To'] = 'admin@yourdomain.com'
    
    # Send email (configure SMTP)
    # smtp.send_message(msg)
```

## API Key Rotation System

### How It Works

The bot now supports automatic API key rotation across multiple Google accounts:

1. **Automatic Rotation Triggers**:
   - When a key reaches 80% quota usage (8,000 units)
   - When a key encounters quota exceeded errors
   - When a key has 3+ consecutive errors
   - When a key is invalid or disabled

2. **Smart Key Selection**:
   - Tracks quota usage per key in database
   - Resets quota counters daily at midnight UTC
   - Skips keys that are disabled or over quota
   - Preemptively rotates before hitting limits

3. **Error Recovery**:
   - Automatically retries failed requests with next key
   - Handles invalid key errors gracefully
   - Continues operation even if some keys fail

### Setting Up Multiple API Keys

1. **Create Multiple Google Cloud Projects**:
   ```bash
   # For each Gmail account:
   # 1. Go to https://console.cloud.google.com/
   # 2. Create new project
   # 3. Enable YouTube Data API v3
   # 4. Create API key with restrictions
   ```

2. **Configure Keys in .env**:
   ```env
   # Add all your API keys comma-separated
   YOUTUBE_API_KEYS=AIza...key1,AIza...key2,AIza...key3,AIza...key4
   ```

3. **Monitor Key Usage**:
   - Use `!stats` command to see all keys' quota status
   - Green ✅ = Healthy (>1000 units remaining)
   - Yellow ⚠️ = Warning (<1000 units remaining)
   - Red ❌ = Exhausted or disabled

### Maximizing Quota Efficiency

With 4 API keys, you get:
- **40,000 total daily quota** (4 × 10,000)
- **13,333 channel checks** per day (40,000 ÷ 3 units per check)
- **555 channels** checked every hour
- **1,111 channels** checked every 2 hours

**Monitoring Capacity Examples**:
- 100 channels @ 30-min intervals = 14,400 quota/day (needs 2 keys)
- 200 channels @ 1-hour intervals = 14,400 quota/day (needs 2 keys)
- 500 channels @ 1-hour intervals = 36,000 quota/day (needs 4 keys)
- 1000 channels @ 2-hour intervals = 36,000 quota/day (needs 4 keys)

**Quota Cost Breakdown**:
- Check channel info: 1 unit
- Get 50 recent videos: 1 unit
- Get stats for 50 videos: 1 unit
- **Total per channel check: ~3 units**

### Best Practices for Multiple Keys

1. **Stagger Key Creation**:
   - Create keys on different days
   - Helps avoid all keys being flagged simultaneously

2. **Use Key Restrictions**:
   - Restrict each key to YouTube Data API only
   - Add IP restrictions if using fixed server

3. **Monitor Key Health**:
   - Check `!stats` regularly
   - Watch for keys with high error counts
   - Replace disabled keys promptly

4. **Quota Management Strategy**:
   - High-priority channels: Check every hour
   - Medium-priority: Check every 2 hours  
   - Low-priority: Check every 4-6 hours
   - Adjust intervals based on available quota

## Best Practices & Tips

### 1. Quota Management
- Monitor quota usage carefully
- Implement caching to reduce API calls
- Use batch operations where possible
- Consider requesting quota increase for production

### 2. Error Handling
- Implement exponential backoff for rate limits
- Log all API errors for debugging
- Have fallback mechanisms for API failures
- Set up alerts for critical errors

### 3. Performance Optimization
- Use database indexes on frequently queried fields
- Implement connection pooling for database
- Cache channel statistics for 24 hours
- Use async operations where possible

### 4. Security
- Never commit API keys to version control
- Use environment variables for all secrets
- Implement rate limiting on Discord commands
- Regularly rotate API keys

### 5. Scaling Considerations
- Use PostgreSQL for production deployments
- Implement Redis for caching
- Consider message queue for video processing
- Use CDN for storing thumbnails if needed

### Troubleshooting API Key Issues

1. **"Invalid API Key" Errors**:
   - Verify key is correct in .env file
   - Check if YouTube Data API is enabled in Google Cloud Console
   - Ensure no extra spaces in API key string

2. **Rapid Quota Exhaustion**:
   - Reduce number of monitored channels
   - Increase check intervals
   - Check for infinite loops in error handling

3. **Keys Not Rotating**:
   - Check database for stuck quota values
   - Use `!rotate_key` to force rotation
   - Verify all keys are properly configured

4. **Database Reset Commands** (if needed):
   ```sql
   -- Reset all API key quotas
   UPDATE api_key_usage SET quota_used = 0, error_count = 0;
   
   -- Check current key status
   SELECT api_key_index, api_key_identifier, quota_used, error_count, last_used 
   FROM api_key_usage;
   
   -- Re-enable a disabled key
   UPDATE api_key_usage SET is_active = 1 WHERE api_key_index = 2;
   ```

## Why Hourly Checks Are Recommended

The bot now defaults to **1-hour check intervals** for several reasons:

1. **Optimal Quota Usage**:
   - Uses only 72 units per channel per day (vs 144 for 30-min checks)
   - Allows monitoring 2x more channels with same quota
   - With 4 keys: Monitor 555 channels instead of 277

2. **Better Performance Detection**:
   - Videos need 2-4 hours to show if they're truly above average
   - Reduces false positives from checking too early
   - Still catches trending videos while they're hot

3. **Practical for Most Channels**:
   - Most channels don't upload multiple times per hour
   - Hourly checks catch all new uploads effectively
   - Gives videos time to accumulate meaningful view data

**When to Use Different Intervals**:
- **30 minutes**: News channels, breaking content, time-sensitive niches
- **1 hour** (default): Most entertainment, education, gaming channels
- **2-4 hours**: Channels that upload weekly or less frequently

You can still adjust the interval in your `.env` file:
```env
CHECK_INTERVAL_MINUTES=60    # Default: 1 hour
# CHECK_INTERVAL_MINUTES=30  # For high-priority monitoring
# CHECK_INTERVAL_MINUTES=120 # For lower-priority channels
```

## Migration Guide (For Existing Bot Users)

If you're updating from a single API key setup:

1. **Update .env file**:
   ```env
   # Change from:
   YOUTUBE_API_KEY=single_key_here
   
   # To:
   YOUTUBE_API_KEYS=key1,key2,key3,key4
   ```

2. **Run Database Migration**:
   ```python
   # migration.py
   from database import engine, Base
   from sqlalchemy import text
   
   # Create new tables
   Base.metadata.create_all(engine)
   
   # Optional: Clear old quota tracking
   with engine.connect() as conn:
       conn.execute(text("DELETE FROM api_key_usage"))
       conn.commit()
   ```

3. **Restart Bot**:
   - The bot will automatically initialize API key tracking
   - Existing channels and videos remain intact
   - Quota tracking starts fresh

## Discord Bot Commands Summary

### Basic Commands
- `!add_channel <youtube_url>` - Add a channel to monitor
- `!list_channels` - Show all monitored channels
- `!check_now` - Manually trigger channel check

### API Management Commands
- `!stats [channel_url]` - Show bot statistics and quota overview
- `!api_status` - Detailed API key status and health
- `!rotate_key` - Manually rotate to next API key
- `!quota_reset` - Show time until daily quota reset

### Advanced Features
- Automatic API key rotation when quota is low
- Graceful handling of API errors and invalid keys
- Daily quota reset at midnight UTC
- Per-key error tracking and recovery

This complete implementation provides a robust YouTube monitoring system with Discord integration, view analytics, transcript extraction, and automatic API key rotation. The modular design allows for easy extension and maintenance while following best practices for production deployment.