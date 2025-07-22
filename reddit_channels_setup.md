# Reddit Story Channels - SHORTS Monitoring Setup

## 🎯 Quick Setup for Your 60+ Reddit Story Channels (SHORTS ONLY)

You have **60 Reddit story channels** to monitor. This system now focuses specifically on **YouTube Shorts** (videos under 3 minutes) which are perfect for Reddit story content!

## Step 1: Configure for SHORTS Monitoring

### Update your `.env` file with optimized settings:

```env
# YouTube API Keys (comma-separated)
YOUTUBE_API_KEYS=AIzaSy..._key1,AIzaSy..._key2,AIzaSy..._key3,AIzaSy..._key4

# Discord Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here

# Optimized for Reddit Story SHORTS
CHECK_INTERVAL_MINUTES=120  # Check every 2 hours
VIEW_THRESHOLD_PERCENTILE=80  # Higher threshold for Reddit story shorts

# API Quota Settings
QUOTA_WARNING_THRESHOLD=8000
QUOTA_EMERGENCY_THRESHOLD=9500
```

## Step 2: Batch Add Your Channels

### Option A: Automatic Batch Processing (Recommended)

```bash
# Run the batch script to add all channels automatically
python batch_add_channels.py
```

This will:
- Process channels in batches of 10
- Save progress to `channel_progress.json`
- Resume if interrupted
- Show detailed progress

### Option B: Manual Addition

If some channels fail automatic detection, add them manually:

```bash
# Run the main bot first
python main.py
```

Then use Discord commands:
```
!add_channel https://youtube.com/@taletrailz
!add_channel https://youtube.com/@SaneRedditor
# ... etc for failed channels
```

## Step 3: Monitor SHORTS Quota Usage

With 60 channels checking every 2 hours for SHORTS only:
- **Daily quota needed**: ~2,160 units (60 channels × 3 units × 12 checks/day)
- **With 4 API keys**: 40,000 daily quota available
- **Safety margin**: 18x more quota than needed! ✅
- **Focus**: Only YouTube Shorts (under 60 seconds)

## Step 4: SHORTS-Specific Features

### What the Bot Monitors:

1. **YouTube Shorts Only**: Videos under 3 minutes
2. **Reddit Story Content**: Perfect for short-form storytelling
3. **Viral Potential**: Shorts that are performing above average
4. **Engagement Metrics**: Views, likes, comments for shorts

### Enhanced Notifications for SHORTS:

- 📱 **Short Video Indicator**: Clear labeling as YouTube Short
- ⏱️ **Duration Display**: Shows exact length in seconds
- 📊 **Performance Metrics**: How the short compares to channel average
- 📝 **Transcript Preview**: Important for Reddit story content

## Step 5: Run the SHORTS Bot

```bash
# Start the monitoring system
python main.py
```

## SHORTS-Specific Commands

Once running, use these Discord commands:

```
!list_channels          # See all 60+ channels
!list_shorts           # Show recent shorts from all channels
!list_shorts channel   # Show shorts from specific channel
!stats                 # Check quota usage and shorts count
!api_status            # Monitor API key rotation
!check_now             # Manual check of all channels for shorts
```

## Expected Results for SHORTS

With 60 Reddit story channels monitoring SHORTS:

### Daily Monitoring:
- **Channel checks**: 720 per day (60 × 12)
- **SHORTS detected**: 50-200 new shorts per day
- **Viral notifications**: 5-15 high-performing shorts per day
- **API key rotation**: Automatic when needed

### Typical SHORTS Notifications:
- Reddit stories that go viral as shorts
- Shorts with unusual engagement
- Stories from trending subreddits
- High-comment discussion shorts

## Why SHORTS for Reddit Stories?

### Perfect Match:
1. **Short Attention Span**: Reddit stories work well in 60-second format
2. **Viral Potential**: Shorts have higher chance of going viral
3. **Mobile Consumption**: Most Reddit users consume content on mobile
4. **Algorithm Favor**: YouTube's algorithm favors shorts

### Reddit Story Shorts Benefits:
- **Quick Consumption**: Users can watch multiple stories quickly
- **Higher Engagement**: Shorts get more views and comments
- **Better Discovery**: Shorts appear in YouTube Shorts feed
- **Cross-Platform**: Easy to share on Reddit and other platforms

## Troubleshooting

### If Some Channels Fail to Add:

1. **Check the progress file**: `channel_progress.json`
2. **Manual addition**: Use Discord `!add_channel` command
3. **Verify channel names**: Some may have slight variations

### If No SHORTS Detected:

1. **Check channel content**: Ensure channels actually post shorts
2. **Verify duration**: Bot only tracks videos under 3 minutes
3. **Use `!list_shorts`**: See what shorts are being detected

### For Reddit Story SHORTS Issues:

1. **High false positives**: Increase `VIEW_THRESHOLD_PERCENTILE` to 85
2. **Too many notifications**: Increase check interval to 4 hours
3. **Missing viral shorts**: Decrease threshold to 70

## Advanced SHORTS Configuration

### For Different Reddit Story Types:

```env
# For r/AmItheAsshole style shorts
VIEW_THRESHOLD_PERCENTILE=75

# For r/relationship_advice shorts  
VIEW_THRESHOLD_PERCENTILE=80

# For r/entitledparents shorts
VIEW_THRESHOLD_PERCENTILE=85
```

### SHORTS-Specific Analytics:

The bot automatically:
- Tracks which story types work best as shorts
- Monitors short video engagement patterns
- Identifies trending Reddit story themes
- Alerts on viral short-form content

## Success Metrics for SHORTS

With proper setup, you should see:
- ✅ 60+ channels monitored for SHORTS only
- ✅ 2-5 notifications per day for viral shorts
- ✅ Automatic API key rotation
- ✅ Detailed analytics for short video performance
- ✅ Rich Discord notifications with short video indicators

## SHORTS Monitoring Advantages

### For Reddit Story Channels:
1. **Faster Detection**: Shorts show viral potential quicker
2. **Higher Engagement**: Shorts typically get more views
3. **Better Analytics**: Clear performance metrics for short content
4. **Viral Tracking**: Catch trending stories before they explode

The bot is now optimized specifically for YouTube Shorts from Reddit story channels and will help you catch viral short-form content before it goes mainstream! 🚀📱 