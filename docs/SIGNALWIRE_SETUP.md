# 📱 SignalWire Setup Guide for Alfred the Butler

## **🎯 What We're Building**

A hybrid communication system that:
- **Primary**: Sends SMS via SignalWire (real phone number)
- **Fallback**: Uses push notifications if SMS fails
- **Cost**: ~$1.50-2.00/month for your usage

## **🚀 Step-by-Step Setup**

### **Step 1: Create SignalWire Account**

1. Go to [signalwire.com](https://signalwire.com)
2. Click "Get Started" or "Sign Up"
3. Create your account with email/password
4. Verify your email address

### **Step 2: Create a Project**

1. **Dashboard**: Click "Create New Project"
2. **Project Name**: `Alfred the Butler`
3. **Description**: `Personal SMS assistant`
4. **Click**: "Create Project"

### **Step 3: Get Your Credentials**

1. **Project ID**: Copy from project dashboard
2. **Auth Token**: Click "Generate Token" → Copy the token
3. **Space URL**: Usually `https://your-space.signalwire.com`

### **Step 4: Buy a Phone Number**

1. **Phone Numbers**: Click "Phone Numbers" in sidebar
2. **Buy Number**: Click "Buy Number"
3. **Select**: Choose a local number (easier for testing)
4. **Capabilities**: Make sure SMS is enabled
5. **Cost**: $1/month + $0.00075 per SMS

### **Step 5: Configure Webhook**

1. **Phone Numbers**: Click on your purchased number
2. **Webhook URL**: Set to `https://your-app.com/webhook/signalwire`
3. **HTTP Method**: POST
4. **Save**: Click "Save Configuration"

### **Step 6: Update Environment Variables**

Add these to your `.env` file:

```bash
# Communication Mode
COMMUNICATION_MODE=hybrid

# SignalWire Configuration
SIGNALWIRE_PROJECT_ID=your_project_id_here
SIGNALWIRE_AUTH_TOKEN=your_auth_token_here
SIGNALWIRE_SPACE_URL=https://your-space.signalwire.com
SIGNALWIRE_PHONE_NUMBER=+1234567890
```

### **Step 7: Test the System**

1. **Start the app**: `cd src && python app.py`
2. **Check health**: Visit `/health` endpoint
3. **Send SMS**: Text your SignalWire number
4. **Receive response**: Get SMS back from Alfred!

## **💰 Cost Breakdown**

### **Monthly Costs:**
- **Phone Number**: $1.00
- **SMS (100 messages)**: $0.075
- **Total**: ~$1.08/month

### **For Your Usage (10-20 messages/day):**
- **300-600 messages/month**
- **SMS cost**: $0.23 - $0.45
- **Total monthly**: $1.23 - $1.45

## **🔧 Configuration Options**

### **Communication Modes:**

#### **1. SMS Only (`COMMUNICATION_MODE=sms`)**
- Only sends SMS via SignalWire
- No push notifications
- Cheapest option

#### **2. Push Only (`COMMUNICATION_MODE=push`)**
- Only push notifications
- No SMS capability
- Free (Pushover)

#### **3. Hybrid (`COMMUNICATION_MODE=hybrid`) - RECOMMENDED**
- Tries SMS first
- Falls back to push notifications if SMS fails
- Best reliability

## **📱 How It Works**

### **Incoming SMS Flow:**
1. **User texts** your SignalWire number
2. **SignalWire webhook** sends data to `/webhook/signalwire`
3. **Alfred processes** the message using NLP
4. **Response sent** via SignalWire SMS
5. **User receives** SMS from Alfred the Butler

### **Fallback Flow (Hybrid Mode):**
1. **SMS fails** (network issues, etc.)
2. **Automatic fallback** to push notification
3. **User gets** push notification instead
4. **No messages lost**

## **🧪 Testing Your Setup**

### **1. Check Communication Status:**
```bash
curl http://localhost:5001/health
```

Look for:
```json
{
  "communication": {
    "mode": "hybrid",
    "signalwire_available": true,
    "pushover_available": true
  }
}
```

### **2. Test SMS:**
1. Text your SignalWire number: "Hello Alfred"
2. You should receive: "Hello! I'm Alfred the Butler..."
3. Check app logs for success/failure

### **3. Test Fallback:**
1. Temporarily break SignalWire (wrong credentials)
2. Send a message
3. Should fall back to push notification

## **🚨 Troubleshooting**

### **Common Issues:**

#### **1. "SignalWire client not initialized"**
- Check your credentials in `.env`
- Verify project ID and auth token
- Ensure space URL is correct

#### **2. "Webhook not receiving messages"**
- Verify webhook URL in SignalWire dashboard
- Check if your app is accessible from internet
- Test webhook endpoint manually

#### **3. "SMS not sending"**
- Check phone number format (+1XXXXXXXXXX)
- Verify account has sufficient credits
- Check SignalWire logs for errors

### **Debug Commands:**
```bash
# Check communication service status
curl http://localhost:5001/health

# Test manual SMS (if you add a test endpoint)
curl -X POST http://localhost:5001/test-sms \
  -H "Content-Type: application/json" \
  -d '{"message": "Test", "phone": "+1234567890"}'
```

## **🎉 Success Indicators**

✅ **SignalWire client initialized successfully** in app logs
✅ **Health endpoint shows** `"signalwire_available": true`
✅ **SMS received** when you text the number
✅ **Response sent** back via SMS
✅ **Fallback works** if SMS fails

## **🚀 Next Steps**

1. **Deploy to cloud** (Render/Railway) for 24/7 availability
2. **Set up webhook** to point to your cloud URL
3. **Test thoroughly** with various message types
4. **Monitor costs** in SignalWire dashboard
5. **Enjoy texting** Alfred the Butler directly! 📱✨

---

**Need help? Check SignalWire docs or create an issue in the repository!**
