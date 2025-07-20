import numpy as np
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from database import SessionLocal, Video, ViewSnapshot, ChannelStats
import logging

logger = logging.getLogger(__name__)

class VideoAnalytics:
    def __init__(self):
        self.db = SessionLocal()
        
    def calculate_channel_statistics(self, channel_id, days=30):
        """Calculate channel performance statistics"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
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
                # Handle timezone-aware vs naive datetime
                if video.published_at.tzinfo is None:
                    published_at = video.published_at.replace(tzinfo=timezone.utc)
                else:
                    published_at = video.published_at
                    
                hours_old = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
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
            'date': datetime.now(timezone.utc),
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
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
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
        # Handle timezone-aware vs naive datetime
        if video.published_at.tzinfo is None:
            published_at = video.published_at.replace(tzinfo=timezone.utc)
        else:
            published_at = video.published_at
            
        hours_old = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
        
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