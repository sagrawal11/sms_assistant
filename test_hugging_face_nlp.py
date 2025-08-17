#!/usr/bin/env python3
"""
Test script for Intelligent NLP Processor
"""

from hugging_face_nlp import create_intelligent_processor

def test_hugging_face_nlp():
    """Test the hugging face NLP processor capabilities"""
    print("🧠 Testing Hugging Face NLP Processor...")
    print("=" * 60)
    
    # Create processor
    processor = create_intelligent_processor({})
    
    # Test cases that were failing before
    test_messages = [
        "Lunch with Ben on Tuesday",
        "I have a meeting from 3-4pm tomorrow with Alex",
        "block out my schedule at 3pm for meeting with John",
        "hit chest today: bench 225x5, incline 185x8",
        "drank a bottle of water",
        "ate chicken breast for lunch",
        "what's my schedule looking like on Thursday",
        "remind me to call mom this evening",
        "add this photo to work folder"
    ]
    
    for message in test_messages:
        print(f"\n📝 Testing: '{message}'")
        print("-" * 50)
        
        # Test message cleaning
        clean_message = processor.clean_message(message)
        print(f"🧹 Cleaned: '{clean_message}'")
        
        # Test intent classification
        intent = processor.classify_intent(message)
        print(f"🎯 Intent: {intent}")
        
        # Test entity extraction
        entities = processor.extract_entities(message)
        print(f"🔍 Entities: {entities}")
        
        # Test specific parsing based on intent
        if intent == 'calendar_event':
            event_data = processor.parse_calendar_event(message)
            if event_data:
                print(f"✅ Calendar event parsed:")
                print(f"   Title: {event_data['title']}")
                print(f"   Start: {event_data['start_time']}")
                print(f"   End: {event_data['end_time']}")
                print(f"   People: {event_data['people']}")
                print(f"   Location: {event_data['location']}")
            else:
                print("❌ Calendar event parsing failed")
        
        elif intent == 'reminder_set':
            reminder_data = processor.parse_reminder(message)
            if reminder_data:
                print(f"✅ Reminder parsed:")
                print(f"   Text: {reminder_data['text']}")
                print(f"   Time: {reminder_data['scheduled_time']}")
            else:
                print("❌ Reminder parsing failed")
        
        print()

if __name__ == "__main__":
    test_hugging_face_nlp()
