import numpy as np
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from database import SessionLocal, Video, ViewSnapshot, ChannelStats
import logging

logger = logging.getLogger(__name__)

class VideoAnalytics:
    def __init__(self):
        self.db = SessionLocal()
        
    def calculate_channel_average_views(self, channel_id, recent_videos_count=25):
        """Calculate average views from the last N videos of a channel"""
        # Get the last N videos from the channel
        recent_videos = self.db.query(Video).filter(
            Video.channel_id == channel_id
        ).order_by(Video.published_at.desc()).limit(recent_videos_count).all()
        
        if not recent_videos:
            logger.warning(f"No videos found for channel {channel_id}")
            return 0
            
        # Calculate average views
        total_views = sum(video.view_count for video in recent_videos)
        average_views = total_views / len(recent_videos)
        
        logger.info(f"Channel {channel_id}: Average views from last {len(recent_videos)} videos = {average_views:,.0f}")
        
        return average_views
        
    def is_video_above_average(self, video_id, recent_videos_count=25):
        """Check if video performs above the channel's recent average"""
        video = self.db.query(Video).filter_by(video_id=video_id).first()
        if not video:
            logger.warning(f"Video {video_id} not found in database")
            return False, {}
            
        # Calculate the channel's average from recent videos
        channel_average = self.calculate_channel_average_views(video.channel_id, recent_videos_count)
        
        if channel_average == 0:
            logger.warning(f"No average calculated for channel {video.channel_id}")
            return False, {}
            
        # Check if current video is above average
        is_above = video.view_count > channel_average
        
        # Calculate performance metrics
        performance_ratio = video.view_count / channel_average if channel_average > 0 else 0
        
        # Handle timezone-aware vs naive datetime
        if video.published_at.tzinfo is None:
            published_at = video.published_at.replace(tzinfo=timezone.utc)
        else:
            published_at = video.published_at
            
        hours_old = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
        
        performance_data = {
            'current_views': video.view_count,
            'channel_average': channel_average,
            'performance_ratio': performance_ratio,
            'is_above_average': is_above,
            'hours_old': hours_old,
            'recent_videos_count': recent_videos_count
        }
        
        logger.info(f"Video {video_id}: {video.view_count:,} views vs {channel_average:,.0f} average ({performance_ratio:.2f}x)")
        
        return is_above, performance_data
        
    def get_channel_performance_summary(self, channel_id, recent_videos_count=25):
        """Get a summary of channel performance based on recent videos"""
        recent_videos = self.db.query(Video).filter(
            Video.channel_id == channel_id
        ).order_by(Video.published_at.desc()).limit(recent_videos_count).all()
        
        if not recent_videos:
            return None
            
        views = [video.view_count for video in recent_videos]
        
        summary = {
            'channel_id': channel_id,
            'recent_videos_count': len(recent_videos),
            'average_views': np.mean(views),
            'median_views': np.median(views),
            'max_views': max(views),
            'min_views': min(views),
            'std_dev': np.std(views),
            'total_views': sum(views)
        }
        
        return summary
        
    def get_trending_videos(self, channel_id=None, limit=10):
        """Get currently trending videos based on view velocity"""
        query = self.db.query(Video)
        if channel_id:
            query = query.filter(Video.channel_id == channel_id)
            
        recent_videos = query.filter(
            Video.published_at >= datetime.now(timezone.utc) - timedelta(days=7)
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