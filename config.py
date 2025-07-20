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