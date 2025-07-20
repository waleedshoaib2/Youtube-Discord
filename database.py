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
    duration_seconds = Column(Integer)  # Duration in seconds
    is_short = Column(Boolean, default=False)  # Whether this is a short video
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