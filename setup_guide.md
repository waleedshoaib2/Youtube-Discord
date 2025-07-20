# YouTube Monitoring Discord Bot Setup Guide

## 🚀 Quick Start

This bot monitors YouTube channels and sends Discord notifications when videos perform above average. It features automatic API key rotation to maximize your daily quota.

## Prerequisites

1. **Python 3.11+** installed
2. **Discord Bot Token** (see Discord setup below)
3. **YouTube API Keys** (see YouTube setup below)

## Step 1: YouTube API Setup

### 1.1 Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable YouTube Data API v3:
   - Go to "APIs & Services" > "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"

### 1.2 Create API Keys (Multiple for Rotation)
For each Gmail account you want to use:

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API Key"
3. Copy the API key
4. (Optional) Click "Edit" to add restrictions:
   - Restrict to YouTube Data API v3
   - Add IP restrictions if using fixed server

### 1.3 Recommended: Create 4 API Keys
- Use 4 different Gmail accounts
- Each gives you 10,000 daily quota
- Total: 40,000 daily quota (4x capacity!)

## Step 2: Discord Bot Setup

### 2.1 Create Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Give it a name (e.g., "YouTube Monitor")

### 2.2 Create Bot
1. Go to "Bot" section
2. Click "Add Bot"
3. Copy the bot token (you'll need this)
4. Enable these intents:
   - Message Content Intent
   - Server Members Intent

### 2.3 Generate Invite Link
1. Go to "OAuth2" > "URL Generator"
2. Select scopes: `bot`, `applications.commands`
3. Select bot permissions:
   - Send Messages
   - Embed Links
   - Read Message History
   - Use Slash Commands
4. Copy the generated URL and open it in browser
5. Add the bot to your server

### 2.4 Get Channel ID
1. Enable Developer Mode in Discord (User Settings > Advanced)
2. Right-click the channel where you want notifications
3. Click "Copy ID"

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Configuration

### 4.1 Create .env File
Copy `env_example.txt` to `.env` and fill in your values:

```env
# YouTube API Keys (comma-separated)
YOUTUBE_API_KEYS=AIzaSy..._key1,AIzaSy..._key2,AIzaSy..._key3,AIzaSy..._key4

# Discord Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here

# Optional: Customize settings
CHECK_INTERVAL_MINUTES=60
VIEW_THRESHOLD_PERCENTILE=75
```

### 4.2 API Key Format
- Separate multiple keys with commas
- No spaces around commas
- Example: `key1,key2,key3,key4`

## Step 5: Run the Bot

### Local Development
```bash
python main.py
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop bot
docker-compose down
```

## Step 6: Add Channels to Monitor

Once the bot is running, use Discord commands:

```
!add_channel https://youtube.com/channel/UC...
!list_channels
!check_now
```

## Discord Commands

### Basic Commands
- `!add_channel <youtube_url>` - Add channel to monitor
- `!list_channels` - Show all monitored channels
- `!check_now` - Manually trigger channel check

### API Management
- `!stats` - Show bot statistics and quota overview
- `!api_status` - Detailed API key status
- `!rotate_key` - Manually rotate to next API key
- `!quota_reset` - Show time until daily quota reset

## Monitoring Capacity

With 4 API keys (40,000 daily quota):
- **555 channels** checked every hour
- **1,111 channels** checked every 2 hours
- **2,222 channels** checked every 4 hours

## Troubleshooting

### Common Issues

1. **"Invalid API Key"**
   - Verify key is correct in .env file
   - Check if YouTube Data API is enabled
   - Ensure no extra spaces in API key

2. **"Bot not responding"**
   - Check bot token is correct
   - Verify bot has proper permissions
   - Check channel ID is correct

3. **"Quota exceeded"**
   - Bot will automatically rotate keys
   - Check `!api_status` for key health
   - Add more API keys if needed

4. **"No notifications"**
   - Videos need 4+ hours to be evaluated
   - Check `!stats` for channel statistics
   - Verify threshold percentile setting

### Database Reset (if needed)
```sql
-- Reset all API key quotas
UPDATE api_key_usage SET quota_used = 0, error_count = 0;

-- Re-enable a disabled key
UPDATE api_key_usage SET is_active = 1 WHERE api_key_index = 2;
```

## Production Deployment

### VPS Setup (DigitalOcean/Linode)
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

# Create .env file
cp env_example.txt .env
nano .env  # Edit with your credentials

# Build and run
docker-compose up -d
```

### Monitoring & Maintenance
```bash
# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart bot
docker-compose restart

# Update bot
git pull
docker-compose up -d --build
```

## Advanced Configuration

### Custom Check Intervals
```env
# High-priority channels
CHECK_INTERVAL_MINUTES=30

# Lower-priority channels  
CHECK_INTERVAL_MINUTES=120
```

### Threshold Adjustment
```env
# More sensitive (notify more videos)
VIEW_THRESHOLD_PERCENTILE=60

# Less sensitive (notify fewer videos)
VIEW_THRESHOLD_PERCENTILE=85
```

### Database Location
```env
# SQLite (default)
DATABASE_URL=sqlite:///youtube_monitor.db

# PostgreSQL (production)
DATABASE_URL=postgresql://user:pass@localhost/youtube_bot
```

## Support

- Check logs for detailed error messages
- Use `!api_status` to monitor key health
- Review `!stats` for quota usage
- Ensure all dependencies are installed

The bot will automatically handle API key rotation, quota management, and error recovery. With proper setup, you can monitor hundreds of channels efficiently! 