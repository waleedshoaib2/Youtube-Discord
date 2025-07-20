#!/usr/bin/env python3
"""
FastAPI Web Server for YouTube Notification Bot
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime, timezone, timedelta
import uvicorn
from contextlib import asynccontextmanager

from config import Config
from database import SessionLocal, Channel, Video
from youtube_monitor import YouTubeMonitor
from analytics import VideoAnalytics
from discord_bot import YouTubeBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
youtube_monitor = YouTubeMonitor()
analytics = VideoAnalytics()
discord_bot = None

# Pydantic models for API
class ChannelAddRequest(BaseModel):
    channel_id: str
    channel_handle: Optional[str] = None

class ChannelResponse(BaseModel):
    channel_id: str
    title: str
    subscriber_count: int
    video_count: int
    thumbnail_url: str
    is_active: bool

class VideoResponse(BaseModel):
    video_id: str
    title: str
    view_count: int
    like_count: int
    published_at: str
    duration_seconds: int
    is_short: bool
    notified: bool

class NotificationResponse(BaseModel):
    success: bool
    message: str
    video_count: int

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup and shutdown events"""
    global discord_bot
    
    # Startup
    try:
        # Check if Discord token is available
        if hasattr(Config, 'DISCORD_BOT_TOKEN') and Config.DISCORD_BOT_TOKEN:
            discord_bot = YouTubeBot()
            await discord_bot.start(Config.DISCORD_BOT_TOKEN)
            logger.info("✅ Discord bot initialized successfully")
        else:
            logger.warning("⚠️ Discord token not found, running without Discord bot")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Discord bot: {e}")
        logger.info("🔄 Continuing without Discord bot")
    
    yield
    
    # Shutdown
    if discord_bot:
        try:
            await discord_bot.close()
            logger.info("🔌 Discord bot disconnected")
        except Exception as e:
            logger.error(f"❌ Error disconnecting Discord bot: {e}")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="YouTube Notification Bot API",
    description="API for monitoring YouTube channels and sending notifications",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "YouTube Notification Bot API",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    db = SessionLocal()
    try:
        channel_count = db.query(Channel).count()
        video_count = db.query(Video).count()
        
        return {
            "status": "healthy",
            "database": "connected",
            "channels": channel_count,
            "videos": video_count,
            "discord_bot": "connected" if discord_bot else "disconnected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    finally:
        db.close()

@app.post("/channels/add", response_model=Dict[str, Any])
async def add_channel(request: ChannelAddRequest):
    """Add a new channel to monitor"""
    try:
        db = SessionLocal()
        
        # Check if channel already exists
        existing = db.query(Channel).filter_by(channel_id=request.channel_id).first()
        if existing:
            db.close()
            return {
                "success": False,
                "message": f"Channel {request.channel_id} already exists",
                "channel_id": request.channel_id
            }
        
        # Add channel using YouTube monitor
        success = youtube_monitor.add_channel(request.channel_id)
        
        if success:
            db.commit()
            db.close()
            return {
                "success": True,
                "message": f"Channel {request.channel_id} added successfully",
                "channel_id": request.channel_id
            }
        else:
            db.close()
            return {
                "success": False,
                "message": f"Failed to add channel {request.channel_id}",
                "channel_id": request.channel_id
            }
            
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "channel_id": request.channel_id
        }

@app.post("/channels/add-batch")
async def add_channels_batch(channel_ids: List[str]):
    """Add multiple channels at once"""
    results = []
    
    for channel_id in channel_ids:
        try:
            result = await add_channel(ChannelAddRequest(channel_id=channel_id))
            results.append({
                "channel_id": channel_id,
                "success": result["success"],
                "message": result["message"]
            })
        except Exception as e:
            results.append({
                "channel_id": channel_id,
                "success": False,
                "message": f"Error: {str(e)}"
            })
    
    return {
        "success": True,
        "results": results,
        "total": len(channel_ids),
        "successful": len([r for r in results if r["success"]])
    }

@app.get("/channels", response_model=List[ChannelResponse])
async def list_channels():
    """List all monitored channels"""
    db = SessionLocal()
    try:
        channels = db.query(Channel).all()
        return [
            ChannelResponse(
                channel_id=channel.channel_id,
                title=channel.title,
                subscriber_count=channel.subscriber_count,
                video_count=channel.video_count,
                thumbnail_url=channel.thumbnail_url,
                is_active=channel.is_active
            )
            for channel in channels
        ]
    finally:
        db.close()

@app.get("/videos/recent")
async def get_recent_videos(hours: int = 24, limit: int = 50):
    """Get recent videos from all channels"""
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        videos = db.query(Video).filter(
            Video.published_at >= cutoff
        ).order_by(Video.published_at.desc()).limit(limit).all()
        
        return [
            VideoResponse(
                video_id=video.video_id,
                title=video.title,
                view_count=video.view_count,
                like_count=video.like_count,
                published_at=video.published_at.isoformat(),
                duration_seconds=video.duration_seconds,
                is_short=video.is_short,
                notified=video.notified
            )
            for video in videos
        ]
    finally:
        db.close()

@app.get("/videos/shorts")
async def get_recent_shorts(hours: int = 24, limit: int = 50):
    """Get recent short videos only"""
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        videos = db.query(Video).filter(
            Video.published_at >= cutoff,
            Video.is_short == True
        ).order_by(Video.published_at.desc()).limit(limit).all()
        
        return [
            VideoResponse(
                video_id=video.video_id,
                title=video.title,
                view_count=video.view_count,
                like_count=video.like_count,
                published_at=video.published_at.isoformat(),
                duration_seconds=video.duration_seconds,
                is_short=video.is_short,
                notified=video.notified
            )
            for video in videos
        ]
    finally:
        db.close()

@app.post("/monitor/update-all")
async def update_all_channels(background_tasks: BackgroundTasks):
    """Update all channels and check for new videos"""
    background_tasks.add_task(youtube_monitor.update_all_channels)
    return {
        "success": True,
        "message": "Channel update started in background",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/notifications/check")
async def check_notifications(background_tasks: BackgroundTasks):
    """Check for videos that meet notification criteria"""
    background_tasks.add_task(check_all_notifications)
    return {
        "success": True,
        "message": "Notification check started in background",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/analytics/channel/{channel_id}/average")
async def get_channel_average(channel_id: str):
    """Get average views for a channel's last 25 videos"""
    try:
        is_above, performance = analytics.is_video_above_average(
            "dummy_video_id",  # We just want the average calculation
            channel_id=channel_id,
            recent_videos_count=25
        )
        
        return {
            "channel_id": channel_id,
            "average_views": performance.get("average_views", 0),
            "recent_videos_count": performance.get("recent_videos_count", 0),
            "threshold": performance.get("threshold", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def check_all_notifications():
    """Check notifications for all channels"""
    db = SessionLocal()
    try:
        channels = db.query(Channel).filter_by(is_active=True).all()
        
        for channel in channels:
            await check_channel_notifications(channel.channel_id)
            
    except Exception as e:
        logger.error(f"Error checking notifications: {e}")
    finally:
        db.close()

async def check_channel_notifications(channel_id: str):
    """Check notifications for a specific channel"""
    db = SessionLocal()
    
    try:
        # Get SHORT videos from last 24 hours that haven't been notified
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_videos = db.query(Video).filter(
            Video.channel_id == channel_id,
            Video.published_at >= cutoff,
            Video.notified == False,
            Video.is_short == True
        ).all()
        
        if not recent_videos:
            return
            
        channel = db.query(Channel).filter_by(channel_id=channel_id).first()
        
        for video in recent_videos:
            # Check if video meets threshold
            is_above, performance = analytics.is_video_above_average(
                video.video_id, 
                recent_videos_count=25
            )
            
            if is_above and performance.get('hours_old', 0) >= 2:
                # Send notification
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
                
                channel_data = {
                    'channel_id': channel.channel_id,
                    'title': channel.title,
                    'thumbnail_url': channel.thumbnail_url
                }
                
                if discord_bot:
                    try:
                        embed = discord_bot.create_video_embed(video_data, channel_data, performance)
                        await discord_bot.send_notification(str(Config.DISCORD_CHANNEL_ID), embed)
                        logger.info(f"✅ Notification sent for video: {video.title}")
                    except Exception as e:
                        logger.error(f"❌ Failed to send Discord notification: {e}")
                else:
                    logger.warning("⚠️ Discord bot not available, skipping notification")
                
                # Mark as notified
                video.notified = True
                db.commit()
                
    except Exception as e:
        logger.error(f"Error checking notifications for channel {channel_id}: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 