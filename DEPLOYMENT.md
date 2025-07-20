# 🚀 YouTube Notification Bot - FastAPI Deployment Guide

## ✅ **What's Changed**

Your Discord bot is now a **FastAPI web server** that's much easier to deploy! 

### **Key Features:**
- 🌐 **Web API** - Access via HTTP endpoints
- 📊 **Health monitoring** - Check system status
- 🔄 **Background tasks** - Non-blocking operations
- 📱 **RESTful API** - Easy to integrate and test
- 🎯 **Same functionality** - All Discord bot features preserved

## 🛠️ **Deployment Options**

### **Option 1: Render.com (Recommended)**

1. **Connect your GitHub repo**
2. **Set environment variables:**
   ```
   DISCORD_TOKEN=your_discord_token
   DISCORD_CHANNEL_ID=your_channel_id
   YOUTUBE_API_KEYS=key1,key2,key3
   DATABASE_URL=your_database_url
   ```

3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`

### **Option 2: Railway.app**

1. **Deploy from GitHub**
2. **Add environment variables** (same as above)
3. **Auto-detects FastAPI** and deploys

### **Option 3: Heroku**

1. **Create new app**
2. **Set environment variables**
3. **Deploy from GitHub**

## 📡 **API Endpoints**

### **Health & Status**
- `GET /` - Basic health check
- `GET /health` - Detailed system status

### **Channel Management**
- `GET /channels` - List all monitored channels
- `POST /channels/add` - Add single channel
- `POST /channels/add-batch` - Add multiple channels

### **Video Monitoring**
- `GET /videos/recent` - Recent videos (all)
- `GET /videos/shorts` - Recent short videos only
- `POST /monitor/update-all` - Update all channels
- `POST /notifications/check` - Check for notifications

### **Analytics**
- `GET /analytics/channel/{channel_id}/average` - Channel average views

## 🔧 **Testing Your Deployment**

### **1. Health Check**
```bash
curl https://your-app.herokuapp.com/health
```

### **2. Add a Channel**
```bash
curl -X POST https://your-app.herokuapp.com/channels/add \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "UC123456789"}'
```

### **3. List Channels**
```bash
curl https://your-app.herokuapp.com/channels
```

### **4. Update Channels**
```bash
curl -X POST https://your-app.herokuapp.com/monitor/update-all
```

### **5. Check Notifications**
```bash
curl -X POST https://your-app.herokuapp.com/notifications/check
```

## ⚙️ **Environment Variables**

```bash
# Required
DISCORD_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=your_discord_channel_id
YOUTUBE_API_KEYS=key1,key2,key3

# Optional
DATABASE_URL=your_database_url
VIEW_THRESHOLD_PERCENTILE=75
NOTIFICATION_COOLDOWN_HOURS=2
```

## 🔄 **Scheduler (Optional)**

For automatic monitoring, run the scheduler:

```bash
python scheduler.py
```

Or set up a cron job:
```bash
# Every 30 minutes
*/30 * * * * curl -X POST https://your-app.herokuapp.com/monitor/update-all

# Every 15 minutes  
*/15 * * * * curl -X POST https://your-app.herokuapp.com/notifications/check
```

## 🎯 **Benefits of FastAPI Version**

1. **✅ Easy Deployment** - Standard web app deployment
2. **✅ Health Monitoring** - Built-in status checks
3. **✅ API Access** - Test and manage via HTTP
4. **✅ Background Tasks** - Non-blocking operations
5. **✅ Auto Documentation** - Visit `/docs` for interactive API docs
6. **✅ Scalable** - Can handle multiple requests
7. **✅ Debugging** - Easy to test individual endpoints

## 🚨 **Troubleshooting**

### **Deployment Issues**
- Check environment variables are set
- Verify Discord token is valid
- Ensure YouTube API keys are working

### **API Issues**
- Check `/health` endpoint
- Verify database connection
- Test individual endpoints

### **Discord Bot Issues**
- Check Discord token permissions
- Verify channel ID is correct
- Test bot connection

## 🎉 **Success!**

Your bot is now deployed as a web service! You can:
- ✅ Monitor channels automatically
- ✅ Send Discord notifications
- ✅ Manage via API endpoints
- ✅ Scale as needed

**Visit your deployed URL to see the API documentation!** 