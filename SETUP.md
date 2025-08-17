# Enhanced Personal SMS Assistant Setup Guide

## 🚀 What's New

This enhanced version replaces Twilio with **Google Voice** and adds:
- 📅 **Google Calendar integration** - Create events from natural language
- 📁 **Google Drive organization** - Auto-organize images into smart folders
- 📧 **Gmail webhook processing** - Handle SMS forwarded from Google Voice
- 🧠 **Enhanced NLP** - Better intent recognition and entity extraction

## 📋 Prerequisites

1. ✅ **Google Voice number** (already set up)
2. **Google Cloud Project** with APIs enabled
3. **Gmail account** (for webhook processing)

## 🔧 Step 1: Google Cloud Setup

### Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable these APIs:
   - Gmail API
   - Google Drive API
   - Google Calendar API

### Create OAuth 2.0 Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth 2.0 Client IDs**
3. Choose **Desktop application**
4. Download the `client_secrets.json` file
5. Place it in your project root

## 🔑 Step 2: Environment Configuration

Create a `.env` file in your project root:

```bash
# Copy the template
cp env_template.txt .env

# Edit .env with your actual values
nano .env  # or use your preferred editor
```

**Required variables:**
- `PUSHOVER_EMAIL_ALIAS` - Your Pushover email alias (username@pomail.net)
- `YOUR_PHONE_NUMBER` - Your personal phone number  
- `GOOGLE_CLIENT_ID` - From Google Cloud Console
- `GOOGLE_CLIENT_SECRET` - From Google Cloud Console
- `GMAIL_WEBHOOK_SECRET` - Any random secret string

**Optional variables (with defaults):**
- `MORNING_CHECKIN_HOUR=8` - Daily check-in time
- `DEFAULT_WATER_BOTTLE_ML=710` - Your water bottle size
- `MAX_IMAGE_SIZE=10485760` - Max image size (10MB)

## 📱 Step 3: Google Voice Configuration

### Enable SMS Forwarding to Gmail
1. Go to [Google Voice](https://voice.google.com/)
2. **Settings** → **Messages**
3. Enable **"Forward messages to email"**
4. Make sure it forwards to your Gmail address

### Test SMS Forwarding
1. Send a text to your Google Voice number
2. Check your Gmail for the forwarded message
3. Verify it appears in your inbox

## 🌐 Step 4: Gmail Webhook Setup

### Option A: Gmail Push Notifications (Recommended)
1. Go to [Gmail API Console](https://console.cloud.google.com/apis/credentials)
2. Create a **Service Account** with domain-wide delegation
3. Enable Gmail push notifications
4. Set webhook URL to: `https://your-domain.com/webhook/gmail`

### Option B: Gmail Polling (Fallback)
If push notifications don't work, we'll implement polling:
1. Set up a cron job to check Gmail every minute
2. Process new messages automatically
3. Less real-time but more reliable

## 🚀 Step 5: Run the Application

### Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### First Run Authentication
```bash
python app.py
```
- A browser window will open for Google OAuth
- Grant permissions for Gmail, Drive, and Calendar
- Credentials will be saved to `credentials.json`

### Test the System
1. Send a text to your Google Voice number: "drank a bottle"
2. Check the app logs for processing
3. Verify response is sent back

## 📊 Step 6: Test All Features

### Health & Fitness
- ✅ "drank a bottle" → Water logging
- ✅ "ate quesadilla" → Food logging with macros
- ✅ "hit chest today" → Gym workout logging

### Productivity
- ✅ "todo call mom tomorrow" → Task creation
- ✅ "remind me to buy groceries at 6pm" → Smart reminders
- ✅ "meeting with John tomorrow 2pm" → Calendar event

### Organization
- ✅ "save receipt" → Image upload instructions
- ✅ "what's my schedule tomorrow?" → Calendar query
- ✅ "organize work documents" → Drive organization

## 🔍 Troubleshooting

### Common Issues

**"No module named 'google'"**
```bash
pip install google-auth google-api-python-client google-auth-oauthlib
```

**"spaCy model not found"**
```bash
python -m spacy download en_core_web_sm
```

**"Authentication failed"**
- Delete `credentials.json`
- Re-run the app for new OAuth flow
- Check `client_secrets.json` is in project root

**"Gmail webhook not working"**
- Verify webhook secret matches
- Check Gmail forwarding is enabled
- Test with legacy SMS endpoint first

### Debug Endpoints
- `/health` - System status
- `/debug` - Configuration values
- `/webhook/sms` - Legacy SMS testing

## 📈 Next Steps

### Enhanced NLP Research
While this system works, consider these alternatives:
- **Rasa**: Open-source, great for custom intents
- **Dialogflow**: Google's NLP, excellent integration
- **Wit.ai**: Facebook's free NLP service
- **Hugging Face**: Latest transformer models

### Image Processing Enhancement
- **Google Vision API** for automatic categorization
- **OCR for receipts** and documents
- **Smart folder naming** based on content

### Calendar Intelligence
- **Conflict detection** for scheduling
- **Travel time calculation** for locations
- **Recurring event patterns**

## 🎯 Success Metrics

You'll know it's working when:
- ✅ SMS sent to Google Voice → Response received
- ✅ Calendar events created from natural language
- ✅ Morning check-ins include today's schedule
- ✅ Images organized into appropriate Drive folders
- ✅ All existing functionality preserved

## 🆘 Need Help?

1. Check the logs in your terminal
2. Verify all environment variables are set
3. Test with simple commands first
4. Use the debug endpoints to verify configuration

---

**🎉 Congratulations!** You now have a powerful personal assistant that integrates seamlessly with Google's ecosystem while maintaining all your existing health and productivity tracking features.
