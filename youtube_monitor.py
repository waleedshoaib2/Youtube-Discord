from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta, timezone
import time
import re
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
                        last_reset=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
                    )
                    self.db.add(key_usage)
                    
                # Reset if new day
                self._check_quota_reset(key_usage)
                    
        self.db.commit()
        
    def _check_quota_reset(self, key_usage):
        """Check if quota should be reset for a key"""
        now = datetime.now(timezone.utc)
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
        key_usage.last_error = datetime.now(timezone.utc)
        
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
        key_usage.last_used = datetime.now(timezone.utc)
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
        
    def _parse_duration(self, duration_str):
        """Parse ISO 8601 duration string to seconds"""
        # Parse duration like "PT1M30S" to seconds
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        return 0
        
    def _is_short_video(self, duration_str):
        """Check if video is a short (under 60 seconds)"""
        duration_seconds = self._parse_duration(duration_str)
        return duration_seconds <= 60
        
    def get_channel_info(self, channel_id):
        """Get channel information"""
        def make_request():
            return self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=channel_id
            ).execute()
            
        try:
            result = self._api_request_with_retry(make_request)
            self.add_quota_usage(1)
            
            if result['items']:
                channel_data = result['items'][0]
                return {
                    'channel_id': channel_data['id'],
                    'title': channel_data['snippet']['title'],
                    'description': channel_data['snippet'].get('description', ''),
                    'thumbnail_url': channel_data['snippet']['thumbnails']['default']['url'],
                    'subscriber_count': int(channel_data['statistics'].get('subscriberCount', 0)),
                    'video_count': int(channel_data['statistics'].get('videoCount', 0)),
                    'upload_playlist_id': channel_data['contentDetails']['relatedPlaylists']['uploads'],
                    'is_active': True,
                    'last_checked': datetime.now(timezone.utc)
                }
        except Exception as e:
            logger.error(f"Error getting channel info for {channel_id}: {e}")
            return None
            
    def search_channel_by_handle(self, handle):
        """Search for channel by handle using YouTube API"""
        def make_request():
            return self.youtube.search().list(
                part='snippet',
                q=handle,
                type='channel',
                maxResults=1
            ).execute()
            
        try:
            result = self._api_request_with_retry(make_request)
            self.add_quota_usage(100)  # Search costs more quota
            
            if result['items']:
                channel_id = result['items'][0]['snippet']['channelId']
                # Now get full channel info
                return self.get_channel_info(channel_id)
            else:
                logger.warning(f"No channel found for handle: {handle}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for channel handle {handle}: {e}")
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
                    duration_str = item['contentDetails']['duration']
                    is_short = self._is_short_video(duration_str)
                    
                    stats[item['id']] = {
                        'view_count': int(item['statistics'].get('viewCount', 0)),
                        'like_count': int(item['statistics'].get('likeCount', 0)),
                        'comment_count': int(item['statistics'].get('commentCount', 0)),
                        'duration': duration_str,
                        'duration_seconds': self._parse_duration(duration_str),
                        'is_short': is_short
                    }
                    
            except Exception as e:
                logger.error(f"Error fetching video statistics: {e}")
                # Continue with partial results
                
        return stats
        
    def monitor_channel(self, channel_id):
        """Complete monitoring flow for a channel - SHORTS ONLY"""
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
            channel.last_checked = datetime.now(timezone.utc)
            
            # Get recent videos
            videos = self.get_playlist_videos(channel_info['upload_playlist_id'], max_results=50)
            
            # Get video statistics
            video_ids = [v['video_id'] for v in videos]
            stats = self.get_video_statistics(video_ids)
            
            # Process each video - FILTER FOR SHORTS ONLY
            new_videos = []
            short_videos_count = 0
            total_videos_count = 0
            
            for video_data in videos:
                video_id = video_data['video_id']
                if video_id not in stats:
                    continue
                    
                total_videos_count += 1
                video_stats = stats[video_id]
                
                # Only process SHORT videos (60 seconds or less)
                if not video_stats.get('is_short', False):
                    logger.debug(f"Skipping non-short video: {video_data['title']} ({video_stats.get('duration_seconds', 0)}s)")
                    continue
                    
                short_videos_count += 1
                
                # Merge stats into video data
                video_data.update(video_stats)
                
                # Check if video exists
                video = self.db.query(Video).filter_by(video_id=video_id).first()
                if not video:
                    # Convert published_at to timezone-aware datetime
                    published_at = datetime.fromisoformat(
                        video_data['published_at'].replace('Z', '+00:00')
                    )
                    video_data['published_at'] = published_at
                    
                    video = Video(**video_data)
                    self.db.add(video)
                    new_videos.append(video_data)
                    logger.info(f"New short video detected: {video_data['title']} ({video_stats.get('duration_seconds', 0)}s)")
                else:
                    # Update statistics
                    for key in ['view_count', 'like_count', 'comment_count']:
                        setattr(video, key, video_data[key])
                    video.last_updated = datetime.now(timezone.utc)
                    
                # Record view snapshot
                # Use the published_at from video_data if it exists, otherwise from the video object
                if 'published_at' in video_data:
                    published_at = video_data['published_at']
                else:
                    published_at = video.published_at
                    
                # Ensure published_at is a datetime object
                if isinstance(published_at, str):
                    published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    
                hours_since_upload = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
                
                snapshot = ViewSnapshot(
                    video_id=video_id,
                    view_count=video_data['view_count'],
                    hours_since_upload=hours_since_upload
                )
                self.db.add(snapshot)
                
            logger.info(f"Channel {channel_info['title']}: {short_videos_count}/{total_videos_count} videos are shorts")
            self.db.commit()
            return new_videos
            
        except Exception as e:
            logger.error(f"Error monitoring channel {channel_id}: {e}")
            self.db.rollback()
            return []
            
    def close(self):
        """Clean up database connection"""
        self.db.close() 