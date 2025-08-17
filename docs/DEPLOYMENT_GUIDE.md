# 🚀 Deploy Alfred the Butler to Render

## **🎯 What We're Deploying:**

- **Flask App**: Alfred the Butler backend
- **SignalWire Integration**: SMS handling
- **Google Services**: Calendar, Drive, Gmail
- **NLP Processing**: Hugging Face Transformers
- **Database**: SQLite with CSV export

## **🌐 Render Setup Steps:**

### **Step 1: Create Render Account**
1. Go to [render.com](https://render.com)
2. Click "Get Started" → Sign up with GitHub
3. Verify your email

### **Step 2: Connect GitHub Repository**
1. **Dashboard**: Click "New +" → "Web Service"
2. **Connect**: Your GitHub repository
3. **Repository**: Select `personal_sms_assistant`

### **Step 3: Configure Web Service**
1. **Name**: `alfred-the-butler`
2. **Environment**: `Python 3`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `cd src && python app.py`
5. **Plan**: Free (750 hours/month)

### **Step 4: Set Environment Variables**
Click "Environment" tab and add:

```bash
# Google API
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GMAIL_WEBHOOK_SECRET=your_gmail_webhook_secret

# SignalWire
SIGNALWIRE_PROJECT_ID=your_project_id
SIGNALWIRE_AUTH_TOKEN=your_auth_token
SIGNALWIRE_SPACE_URL=https://the-butler.signalwire.com
SIGNALWIRE_PHONE_NUMBER=+13092885370

# Communication
COMMUNICATION_MODE=hybrid
PUSHOVER_EMAIL_ALIAS=your_pushover_email

# App Settings
MORNING_CHECKIN_HOUR=8
GMAIL_POLLING_INTERVAL=5
```

### **Step 5: Deploy**
1. **Click**: "Create Web Service"
2. **Wait**: Build completes (5-10 minutes)
3. **Get URL**: Your app will be at `https://alfred-the-butler.onrender.com`

## **🔧 Update SignalWire Webhook:**

1. **SignalWire Dashboard**: Go to phone number settings
2. **Webhook URL**: Update to your Render URL
   - **Old**: `https://the-butler.com/webhook/signalwire`
   - **New**: `https://alfred-the-butler.onrender.com/webhook/signalwire`
3. **Save**: Configuration

## **🧪 Test Your Deployment:**

### **1. Health Check:**
```bash
curl https://alfred-the-butler.onrender.com/health
```

### **2. Test SMS:**
1. **Text your number**: `+13092885370`
2. **Message**: "Hello Alfred"
3. **Expected**: Response from Alfred via SMS

## **📊 Monitoring:**

- **Logs**: View in Render dashboard
- **Health**: `/health` endpoint
- **Uptime**: Render monitors automatically
- **Scaling**: Auto-scales based on traffic

## **💰 Cost:**

- **Free Tier**: 750 hours/month (covers full month)
- **Your Usage**: ~10-20 messages/day = very low traffic
- **Total Cost**: $0/month! 🎉

## **🚨 Troubleshooting:**

### **Build Fails:**
- Check requirements.txt
- Verify Python version (3.12)
- Check build logs

### **App Won't Start:**
- Check environment variables
- Verify start command
- Check app logs

### **SMS Not Working:**
- Verify webhook URL in SignalWire
- Check app logs for errors
- Test webhook endpoint manually

## **🎉 Success Indicators:**

✅ **App deploys** without errors
✅ **Health endpoint** responds
✅ **SignalWire webhook** receives messages
✅ **SMS responses** sent back
✅ **Google services** working

---

**Need help? Check Render logs or create an issue in the repository!**
