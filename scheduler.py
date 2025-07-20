#!/usr/bin/env python3
"""
Scheduler for YouTube Notification Bot
Runs periodic tasks to update channels and check notifications
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timezone
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the base URL from environment or default to localhost
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

async def make_request(endpoint: str, method: str = "GET", data: dict = None):
    """Make HTTP request to the FastAPI server"""
    url = f"{BASE_URL}{endpoint}"
    
    async with aiohttp.ClientSession() as session:
        if method == "GET":
            async with session.get(url) as response:
                return await response.json()
        elif method == "POST":
            async with session.post(url, json=data) as response:
                return await response.json()

async def update_channels():
    """Update all channels"""
    try:
        logger.info("🔄 Updating all channels...")
        result = await make_request("/monitor/update-all", "POST")
        logger.info(f"✅ Channel update result: {result}")
    except Exception as e:
        logger.error(f"❌ Error updating channels: {e}")

async def check_notifications():
    """Check for notifications"""
    try:
        logger.info("🔔 Checking notifications...")
        result = await make_request("/notifications/check", "POST")
        logger.info(f"✅ Notification check result: {result}")
    except Exception as e:
        logger.error(f"❌ Error checking notifications: {e}")

async def health_check():
    """Check if the server is healthy"""
    try:
        result = await make_request("/health")
        logger.info(f"🏥 Health check: {result}")
        return result.get("status") == "healthy"
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return False

async def main():
    """Main scheduler loop"""
    logger.info("🚀 Starting YouTube Notification Scheduler")
    logger.info(f"📡 Connecting to: {BASE_URL}")
    
    while True:
        try:
            # Check if server is healthy
            if not await health_check():
                logger.warning("⚠️ Server not healthy, waiting...")
                await asyncio.sleep(60)
                continue
            
            # Update channels every 30 minutes
            await update_channels()
            await asyncio.sleep(30 * 60)  # 30 minutes
            
            # Check notifications every 15 minutes
            await check_notifications()
            await asyncio.sleep(15 * 60)  # 15 minutes
            
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    asyncio.run(main()) 