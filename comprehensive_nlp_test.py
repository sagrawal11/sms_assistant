#!/usr/bin/env python3
"""
Comprehensive Test Suite for Intelligent NLP Processor
Tests all possible scenarios to ensure bulletproof performance
"""

from hugging_face_nlp import create_intelligent_processor
from datetime import datetime, timedelta

def run_comprehensive_tests():
    """Run comprehensive tests across all NLP scenarios"""
    print("🧪 COMPREHENSIVE NLP TEST SUITE")
    print("=" * 80)
    
    # Create processor
    processor = create_intelligent_processor({})
    
    # Test categories
    test_categories = {
        "📅 Calendar Events": [
            "Lunch with Ben on Tuesday",
            "Meeting with John tomorrow at 3pm",
            "Block out 2-4pm for team sync",
            "Appointment with doctor next Friday at 10am",
            "Call with client this evening at 7pm",
            "Dinner with Sarah tonight at 8pm",
            "Coffee with Alex tomorrow morning",
            "Workout session at 6am tomorrow",
            "Team standup every Monday at 9am",
            "Client presentation on Wednesday at 2pm"
        ],
        
        "⏰ Reminders": [
            "Remind me to call mom this evening",
            "Don't forget to buy groceries tomorrow",
            "Reminder to pay bills on Friday",
            "Set reminder for dentist appointment",
            "Remind me to text John later",
            "Don't forget to pick up dry cleaning",
            "Reminder to book flight next week",
            "Set alarm for 6am tomorrow",
            "Remind me to call the bank",
            "Don't forget to schedule car maintenance"
        ],
        
        "💪 Gym Workouts": [
            "Hit chest today: bench 225x5, incline 185x8",
            "Worked out legs: squat 315x3, deadlift 405x1",
            "Hit back: pullups 10x3, rows 135x8",
            "Gym session: bench press 225x5, shoulder press 135x8",
            "Worked out arms: curls 45x10, tricep extensions 60x8",
            "Hit shoulders: press 135x8, lateral raises 25x12",
            "Leg day: squats 275x5, leg press 315x10",
            "Back workout: deadlifts 365x3, pullups 8x4",
            "Chest and triceps: bench 205x8, dips 15x3",
            "Full body: deadlift 315x5, press 115x8, rows 185x10"
        ],
        
        "💧 Water Logging": [
            "Drank a bottle of water",
            "Had 24oz water",
            "Finished my water bottle",
            "Drank 2 glasses of water",
            "Hydrated with 500ml water",
            "Consumed 32oz water",
            "Had a glass of water",
            "Finished water bottle",
            "Drank water",
            "Hydrated"
        ],
        
        "🍽️ Food Logging": [
            "Ate chicken breast for lunch",
            "Had oatmeal with berries",
            "Consumed 2000 calories today",
            "Ate protein bar as snack",
            "Had salmon with rice for dinner",
            "Breakfast: eggs and toast",
            "Lunch: turkey sandwich",
            "Dinner: steak and potatoes",
            "Snack: apple and nuts",
            "Meal: pasta with meatballs"
        ],
        
        "📋 Todo Management": [
            "Add buy groceries to my todo list",
            "Need to remember to call the bank",
            "Todo: schedule car maintenance",
            "Add book flight to vacation list",
            "Remember to pick up dry cleaning",
            "Add dentist appointment to list",
            "Todo: buy birthday gift",
            "Need to schedule haircut",
            "Add pay rent to list",
            "Remember to renew insurance"
        ],
        
        "📸 Photo Upload": [
            "Add this photo to work folder",
            "Save this receipt in receipts folder",
            "Organize this image in personal folder",
            "Upload this document to drive",
            "Store this photo in family folder",
            "Save receipt to work folder",
            "Add photo to vacation album",
            "Organize document in project folder",
            "Upload image to shared drive",
            "Store photo in archive folder"
        ],
        
        "📅 Schedule Queries": [
            "What's my schedule looking like on Thursday",
            "Show me my calendar for tomorrow",
            "What meetings do I have today",
            "Check my schedule for next week",
            "Am I free on Friday afternoon",
            "What's on my calendar tomorrow",
            "Show schedule for next Monday",
            "Check if I'm busy on Wednesday",
            "What appointments do I have this week",
            "Am I available on Saturday morning"
        ],
        
        "🔄 Complex Scenarios": [
            "Meeting with marketing team tomorrow at 2pm for 2 hours to discuss Q4 strategy",
            "Lunch with Sarah and John on Tuesday at noon, then workout at 3pm",
            "Call mom this evening at 7pm, remind me to ask about vacation plans",
            "Block out 9am-11am on Thursday for deep work, then team meeting at 2pm",
            "Hit chest and triceps: bench 225x5x3, incline 185x8x3, dips 15x3",
            "Remind me to buy groceries tomorrow morning, then call dentist to reschedule",
            "Lunch with client on Friday at 1pm for 90 minutes, bring presentation materials",
            "Workout tomorrow: legs and shoulders, squat 315x5, press 135x8, then cardio",
            "Meeting with engineering team from 10am-12pm on Monday, then lunch with CEO",
            "Call dad this evening, remind me to discuss the house project and budget"
        ]
    }
    
    # Track results
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    # Run tests for each category
    for category, messages in test_categories.items():
        print(f"\n{category}")
        print("-" * len(category))
        
        for message in messages:
            total_tests += 1
            
            try:
                # Test message cleaning
                clean_message = processor.clean_message(message)
                
                # Test intent classification
                intent = processor.classify_intent(message)
                
                # Test entity extraction
                entities = processor.extract_entities(message)
                
                # Validate results based on expected intent
                expected_intent = get_expected_intent(category, message)
                intent_correct = intent == expected_intent
                
                # Test specific parsing
                parsing_success = test_specific_parsing(processor, intent, message, entities)
                
                # Overall test result
                test_passed = intent_correct and parsing_success
                
                if test_passed:
                    passed_tests += 1
                    status = "✅ PASS"
                else:
                    failed_tests += 1
                    status = "❌ FAIL"
                
                print(f"{status} | {intent:20} | {message[:50]}{'...' if len(message) > 50 else ''}")
                
                if not test_passed:
                    print(f"        Expected: {expected_intent}, Got: {intent}")
                
            except Exception as e:
                failed_tests += 1
                print(f"❌ ERROR | {'ERROR':20} | {message[:50]}{'...' if len(message) > 50 else ''}")
                print(f"        Exception: {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! Alfred the Butler is ready for action!")
    else:
        print(f"\n⚠️  {failed_tests} tests failed. Please review before testing the real app.")
    
    return failed_tests == 0

def get_expected_intent(category: str, message: str) -> str:
    """Get expected intent based on category and message content"""
    category_intents = {
        "📅 Calendar Events": "calendar_event",
        "⏰ Reminders": "reminder_set",
        "💪 Gym Workouts": "gym_workout",
        "💧 Water Logging": "water_logging",
        "🍽️ Food Logging": "food_logging",
        "📋 Todo Management": "todo_add",
        "📸 Photo Upload": "photo_upload",
        "📅 Schedule Queries": "schedule_check"
    }
    
    # Special handling for complex scenarios
    if category == "🔄 Complex Scenarios":
        if any(word in message.lower() for word in ['meeting', 'lunch', 'call', 'appointment']):
            return "calendar_event"
        elif any(word in message.lower() for word in ['remind', 'reminder']):
            return "reminder_set"
        elif any(word in message.lower() for word in ['hit', 'workout', 'bench', 'squat']):
            return "gym_workout"
    
    return category_intents.get(category, "unknown")

def test_specific_parsing(processor, intent: str, message: str, entities: dict) -> bool:
    """Test specific parsing based on intent"""
    try:
        if intent == "calendar_event":
            event_data = processor.parse_calendar_event(message)
            return event_data is not None and event_data.get('start_time') is not None
        
        elif intent == "reminder_set":
            reminder_data = processor.parse_reminder(message)
            return reminder_data is not None and reminder_data.get('scheduled_time') is not None
        
        elif intent == "gym_workout":
            # Check if exercises were extracted
            exercises = entities.get('exercises', [])
            return len(exercises) > 0
        
        elif intent == "water_logging":
            # Basic validation for water logging
            return "water" in message.lower() or "drank" in message.lower()
        
        elif intent == "food_logging":
            # Basic validation for food logging
            return any(word in message.lower() for word in ['ate', 'had', 'consumed', 'breakfast', 'lunch', 'dinner'])
        
        elif intent == "todo_add":
            # Basic validation for todo
            return any(word in message.lower() for word in ['add', 'todo', 'remember', 'need to'])
        
        elif intent == "photo_upload":
            # Basic validation for photo upload
            return any(word in message.lower() for word in ['photo', 'image', 'save', 'upload', 'add this'])
        
        elif intent == "schedule_check":
            # Basic validation for schedule check
            return any(word in message.lower() for word in ['schedule', 'calendar', 'what', 'show', 'check'])
        
        return True  # Default pass for unknown intents
        
    except Exception:
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)
