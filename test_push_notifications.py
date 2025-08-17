#!/usr/bin/env python3
"""
Test script for push notifications
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_push_notifications():
    """Test the push notification system"""
    print("🧪 Testing Push Notifications...")
    
    # Check environment variables
    required_vars = ['PUSHOVER_EMAIL_ALIAS']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("💡 Please set this in your .env file:")
        print(f"   PUSHOVER_EMAIL_ALIAS=your_username@pomail.net")
        return False
    
    print("✅ Environment variables configured")
    
    try:
        # Import the Google services module
        from google_services import GoogleServicesManager
        
        print("✅ Google services module imported successfully")
        
        # Initialize Google services
        google_services = GoogleServicesManager()
        print("✅ Google services initialized")
        
        # Test push notification
        test_title = "🧪 Test Notification"
        test_message = "This is a test push notification from Alfred the Butler!"
        
        print(f"📱 Sending test push notification...")
        print(f"   Title: {test_title}")
        print(f"   Message: {test_message}")
        
        success = google_services.send_push_notification(test_title, test_message)
        
        if success:
            print("✅ Push notification sent successfully!")
            print("💡 Check your phone for the notification")
        else:
            print("❌ Push notification failed")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Google services module: {e}")
        print("💡 Make sure you've installed the required dependencies:")
        print("   pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Push Notification Test")
    print("=" * 50)
    
    success = test_push_notifications()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Push notifications are working! Alfred the Butler is ready.")
        print("💡 Next step: Send a test SMS to your Google Voice number")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("💡 Make sure all dependencies are installed and credentials are set")
    
    return success

if __name__ == "__main__":
    main()
