#!/usr/bin/env python3
"""
Flask Web Application for YouTube Notification Bot
"""

from flask import Flask, jsonify, request
import threading
import time
import logging
from main import YouTubeNotificationBot
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global bot instance
bot = None
bot_thread = None
bot_running = False

def run_bot():
    """Run the bot in a separate thread"""
    global bot, bot_running
    try:
        bot = YouTubeNotificationBot()
        bot_running = True
        logger.info("🤖 Bot started successfully!")
        bot.run()
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        bot_running = False

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'bot_running': bot_running,
        'service': 'YouTube Notification Bot',
        'endpoints': {
            'health': '/health',
            'status': '/status',
            'channels': '/channels',
            'videos': '/videos',
            'test_notification': '/test_notification'
        }
    })

@app.route('/health')
def health():
    """Health check for deployment platforms"""
    return jsonify({
        'status': 'healthy',
        'bot_running': bot_running,
        'timestamp': time.time()
    })

@app.route('/status')
def status():
    """Get bot status"""
    if not bot:
        return jsonify({
            'status': 'not_started',
            'message': 'Bot not initialized'
        })
    
    return jsonify({
        'status': 'running' if bot_running else 'stopped',
        'monitoring_active': bot.monitoring_active if bot else False,
        'discord_connected': bot.discord_bot.is_ready() if bot and bot.discord_bot else False
    })

@app.route('/channels')
def get_channels():
    """Get list of monitored channels"""
    if not bot:
        return jsonify({'error': 'Bot not started'})
    
    try:
        from database import SessionLocal, Channel
        db = SessionLocal()
        channels = db.query(Channel).all()
        
        channel_list = []
        for channel in channels:
            channel_list.append({
                'channel_id': channel.channel_id,
                'title': channel.title,
                'subscriber_count': channel.subscriber_count,
                'video_count': channel.video_count
            })
        
        db.close()
        return jsonify({
            'channels': channel_list,
            'count': len(channel_list)
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/videos')
def get_videos():
    """Get recent videos"""
    if not bot:
        return jsonify({'error': 'Bot not started'})
    
    try:
        from database import SessionLocal, Video
        from datetime import datetime, timezone, timedelta
        
        db = SessionLocal()
        
        # Get videos from last 24 hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        videos = db.query(Video).filter(
            Video.published_at >= cutoff
        ).order_by(Video.published_at.desc()).limit(20).all()
        
        video_list = []
        for video in videos:
            video_list.append({
                'video_id': video.video_id,
                'title': video.title,
                'view_count': video.view_count,
                'published_at': video.published_at.isoformat(),
                'is_short': video.is_short,
                'notified': video.notified
            })
        
        db.close()
        return jsonify({
            'videos': video_list,
            'count': len(video_list)
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/test_notification', methods=['POST'])
def test_notification():
    """Test notification endpoint"""
    if not bot or not bot.discord_bot:
        return jsonify({'error': 'Bot or Discord bot not available'})
    
    try:
        # Create a test notification
        test_data = {
            'video_id': 'test123',
            'title': 'Test Notification',
            'description': 'This is a test notification from the web interface',
            'published_at': time.time(),
            'thumbnail_url': 'https://via.placeholder.com/120x90',
            'view_count': 1000,
            'like_count': 50,
            'comment_count': 10,
            'duration_seconds': 45,
            'is_short': True
        }
        
        test_channel = {
            'channel_id': 'test_channel',
            'title': 'Test Channel',
            'thumbnail_url': 'https://via.placeholder.com/88x88'
        }
        
        test_performance = {
            'above_average': True,
            'percentile': 85,
            'hours_old': 3
        }
        
        # Send test notification
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.send_notification(test_data, test_channel, test_performance))
        loop.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Test notification sent'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/start_bot', methods=['POST'])
def start_bot():
    """Start the bot"""
    global bot_thread, bot_running
    
    if bot_running:
        return jsonify({'status': 'already_running'})
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Wait a moment for bot to start
    time.sleep(2)
    
    return jsonify({
        'status': 'started',
        'bot_running': bot_running
    })

if __name__ == '__main__':
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 