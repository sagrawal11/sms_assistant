#!/usr/bin/env python3
"""
Test script for Google Services integration
Run this to verify your setup before using the main app
"""

import os
from dotenv import load_dotenv
from google_services import GoogleServicesManager
from enhanced_nlp_processor import create_enhanced_processor

def test_google_services():
    """Test Google services integration"""
    print("🧪 Testing Google Services Integration...")
    
    try:
        # Test Google services initialization
        google_services = GoogleServicesManager()
        print("✅ Google services initialized successfully")
        
        # Test calendar access
        print("\n📅 Testing Calendar access...")
        from datetime import datetime, timedelta
        today = datetime.now()
        events = google_services.get_calendar_events(today, today + timedelta(days=1))
        print(f"✅ Calendar access working - found {len(events)} events today")
        
        # Test Drive access
        print("\n📁 Testing Drive access...")
        # This will create a test folder if none exists
        folder_id = google_services._get_folder_id('test')
        print(f"✅ Drive access working - test folder ID: {folder_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Google services test failed: {e}")
        return False

def test_nlp_processor():
    """Test enhanced NLP processor"""
    print("\n🧠 Testing Enhanced NLP Processor...")
    
    try:
        # Test NLP processor initialization
        processor = create_enhanced_processor({})
        print("✅ NLP processor initialized successfully")
        
        # Test intent classification
        test_messages = [
            "drank a bottle of water",
            "meeting with John tomorrow 2pm",
            "ate quesadilla for lunch",
            "hit chest and back today",
            "remind me to call mom tonight"
        ]
        
        for message in test_messages:
            intents = processor.classify_intent(message)
            entities = processor.extract_entities(message)
            print(f"✅ '{message}' → Intents: {intents}, Entities: {len(entities)}")
        
        return True
        
    except Exception as e:
        print(f"❌ NLP processor test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n⚙️ Testing Configuration...")
    
    try:
        from config import Config
        config = Config()
        
        # Use the new validation method
        config.validate()
        print("✅ Configuration validated successfully")
        
        # Show that variables are present (without revealing values)
        required_vars = [
            'PUSHOVER_EMAIL_ALIAS',
            'YOUR_PHONE_NUMBER',
            'GOOGLE_CLIENT_ID',
            'GOOGLE_CLIENT_SECRET',
            'GMAIL_WEBHOOK_SECRET'
        ]
        
        for var in required_vars:
            value = getattr(config, var, None)
            if value:
                print(f"✅ {var}: {'*' * len(str(value))} (hidden)")
            else:
                print(f"❌ {var}: MISSING")
        
        return True
            
    except ValueError as e:
        print(f"❌ Configuration validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Enhanced Personal SMS Assistant - System Test")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Run tests
    tests = [
        ("Configuration", test_configuration),
        ("Google Services", test_google_services),
        ("NLP Processor", test_nlp_processor)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your system is ready to go.")
        print("Next steps:")
        print("1. Run: python app.py")
        print("2. Send a text to your Google Voice number")
        print("3. Test with: 'drank a bottle'")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        print("Common issues:")
        print("- Missing environment variables in .env file")
        print("- Google Cloud APIs not enabled")
        print("- OAuth credentials not set up")
        print("- spaCy model not installed")

if __name__ == "__main__":
    main()
