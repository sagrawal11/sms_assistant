"""
Test Script for Google Voice Web Automation
Tests the web automation module to ensure it can login and send SMS
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_web_automation():
    """Test the Google Voice web automation module"""
    print("🧪 Testing Google Voice Web Automation...")
    
    # Check environment variables
    required_vars = ['GOOGLE_EMAIL', 'GOOGLE_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("💡 Please set these in your .env file:")
        for var in missing_vars:
            print(f"   {var}=your_value_here")
        return False
    
    print("✅ Environment variables configured")
    
    try:
        # Import the automation module
        from google_voice_automation import GoogleVoiceAutomation
        
        print("✅ Google Voice automation module imported successfully")
        
        # Test basic initialization
        automation = GoogleVoiceAutomation(headless=False)  # Set to False for testing
        print("✅ GoogleVoiceAutomation initialized")
        
        # Test driver setup
        if automation.setup_driver():
            print("✅ Chrome driver setup successful")
        else:
            print("❌ Chrome driver setup failed")
            return False
        
        # Test login (this will open a browser window)
        print("🔐 Testing Google Voice login...")
        print("💡 A browser window will open - please complete the login manually if needed")
        
        email = os.environ.get('GOOGLE_EMAIL')
        password = os.environ.get('GOOGLE_PASSWORD')
        
        if automation.login_to_google_voice(email, password):
            print("✅ Google Voice login successful")
            
            # Test SMS sending (to your own number for safety)
            test_number = os.environ.get('YOUR_PHONE_NUMBER')
            test_message = "🧪 Test message from your SMS Assistant - Web automation is working!"
            
            print(f"📱 Testing SMS sending to {test_number}...")
            
            if automation.send_sms_via_web(test_number, test_message):
                print("✅ SMS sent successfully via web automation!")
                print("🎉 Your SMS assistant is now fully functional!")
            else:
                print("❌ SMS sending failed")
                
        else:
            print("❌ Google Voice login failed")
            
        # Cleanup
        automation.close()
        print("✅ Browser cleanup completed")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Google Voice automation module: {e}")
        print("💡 Make sure you've installed the required dependencies:")
        print("   pip install selenium webdriver-manager playwright")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Google Voice Web Automation Test")
    print("=" * 50)
    
    success = test_web_automation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Your SMS assistant is ready for deployment.")
        print("💡 Next step: Deploy to Render for 24/7 operation")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("💡 Make sure all dependencies are installed and credentials are set")
    
    return success

if __name__ == "__main__":
    main()
