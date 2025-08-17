# 🚀 Cloud Deployment Guide for Alfred the Butler

## **☁️ Why Deploy to the Cloud?**

- **24/7 Availability**: Alfred never sleeps
- **No Local Computer**: Works from anywhere
- **Automatic Gmail Polling**: Always checking for your messages
- **Push Notifications**: Instant responses to your phone

## **🎯 Recommended: Render (Free Tier)**

### **Why Render?**
- ✅ **Free**: 750 hours/month (covers full month)
- ✅ **Easy**: Git-based deployment
- ✅ **Reliable**: Good uptime for personal projects
- ✅ **Perfect**: For low message volume (10-20/day)

### **Limitations**
- ⚠️ **Sleeps**: After 15 minutes of inactivity
- ⚠️ **Wake Time**: 1-2 minutes to respond after sleeping
- ⚠️ **Free Tier**: Limited to 750 hours/month

## **📋 Pre-Deployment Checklist**

### **1. Environment Variables**
Make sure you have these in your `.env` file:
```bash
# Google API
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GMAIL_WEBHOOK_SECRET=your_webhook_secret

# Pushover
PUSHOVER_EMAIL_ALIAS=your_email@pomail.net

# App Settings
MORNING_CHECKIN_HOUR=8
GMAIL_POLLING_INTERVAL=5
```

### **2. Google Cloud Console**
- ✅ OAuth consent screen configured
- ✅ Your email added as test user
- ✅ Gmail API enabled
- ✅ Google Drive API enabled
- ✅ Google Calendar API enabled

### **3. Pushover Account**
- ✅ Account created
- ✅ Email alias configured
- ✅ Test notification sent

## **🚀 Deploy to Render**

### **Step 1: Create Render Account**
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Verify your email

### **Step 2: Connect Your Repository**
1. Click "New +"
2. Select "Web Service"
3. Connect your GitHub repository
4. Select the `personal_sms_assistant` repository

### **Step 3: Configure the Service**
```
Name: alfred-the-butler
Environment: Python 3
Build Command: pip install -r config/requirements.txt
Start Command: cd src && python app.py
```

### **Step 4: Add Environment Variables**
In Render dashboard, add these environment variables:
```
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GMAIL_WEBHOOK_SECRET=your_webhook_secret
PUSHOVER_EMAIL_ALIAS=your_email@pomail.net
MORNING_CHECKIN_HOUR=8
GMAIL_POLLING_INTERVAL=5
```

### **Step 5: Deploy**
1. Click "Create Web Service"
2. Wait for build to complete
3. Your app will be available at: `https://alfred-the-butler.onrender.com`

## **🔧 Alternative: Railway**

### **Why Railway?**
- ✅ **Free**: 500 hours/month
- ✅ **Fast**: Quick deployments
- ✅ **Good**: For development and testing

### **Deployment Steps**
1. Go to [railway.app](https://railway.app)
2. Connect GitHub repository
3. Deploy automatically
4. Add environment variables

## **📱 Testing Your Deployed App**

### **1. Check App Status**
- Visit your app URL
- Should see "Alfred the Butler is running"

### **2. Test Gmail Integration**
- Send SMS to Google Voice
- Check if you get push notification
- Look at Render logs for any errors

### **3. Test Calendar Integration**
- Send: "Lunch with Ben tomorrow at 2pm"
- Check if event appears in Google Calendar

## **🔄 Keeping Your App Awake**

### **Render Free Tier Sleep Issue**
Since Render sleeps after 15 minutes, your app won't poll Gmail continuously.

### **Solutions:**

#### **Option 1: Accept Sleep (Recommended)**
- **Pros**: Free, simple
- **Cons**: 1-2 minute delay after sleeping
- **Best for**: Personal use, low message volume

#### **Option 2: Upgrade to Paid Plan**
- **Cost**: $7/month
- **Pros**: Always awake, instant responses
- **Cons**: Monthly cost

#### **Option 3: Use External Ping Service**
- **Services**: UptimeRobot, Pingdom
- **How**: Ping your app every 10 minutes
- **Cost**: Free tier available
- **Setup**: Add ping URL to keep app awake

## **📊 Monitoring Your App**

### **Render Dashboard**
- **Logs**: View real-time application logs
- **Metrics**: CPU, memory usage
- **Deployments**: Automatic from Git pushes

### **Health Check Endpoint**
Your app includes a health check at `/health`:
```
GET https://alfred-the-butler.onrender.com/health
Response: {"status": "healthy", "timestamp": "..."}
```

## **🔄 Updating Your App**

### **Automatic Updates**
1. Push changes to GitHub
2. Render automatically redeploys
3. No manual intervention needed

### **Manual Updates**
1. Go to Render dashboard
2. Click "Manual Deploy"
3. Select branch/commit

## **🚨 Troubleshooting**

### **Common Issues**

#### **1. App Won't Start**
- Check environment variables
- Verify requirements.txt
- Check Render logs

#### **2. Gmail Authentication Fails**
- Verify OAuth consent screen
- Check client ID/secret
- Ensure your email is added as test user

#### **3. Push Notifications Not Working**
- Verify Pushover email alias
- Check email format
- Test with simple message

#### **4. Database Errors**
- Check if database file is writable
- Verify file paths in cloud environment

### **Getting Help**
- **Render Logs**: Check application logs
- **GitHub Issues**: Create issue in repository
- **Environment Variables**: Double-check all values

## **🎉 Success!**

Once deployed, Alfred the Butler will:
- ✅ **Run 24/7** (with sleep limitations on free tier)
- ✅ **Poll Gmail** every 5 seconds when awake
- ✅ **Send Push Notifications** instantly
- ✅ **Log Food, Water, Gym** automatically
- ✅ **Manage Calendar** events
- ✅ **Set Reminders** and todos

---

**🚀 Ready to deploy? Follow the steps above and Alfred will be available worldwide!**
