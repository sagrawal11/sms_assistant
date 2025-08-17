from flask import Flask, request, jsonify
import sqlite3
import json
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from config import Config
from hugging_face_nlp import create_intelligent_processor
from google_services import GoogleServicesManager
import base64

# Initialize Flask app
app = Flask(__name__)

# Load configuration
config = Config()

# Validate configuration
try:
    config.validate()
    print("✅ Configuration validated successfully")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    print("Please check your .env file and ensure all required variables are set")
    exit(1)

# Initialize Google services
google_services = GoogleServicesManager()

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Database initialization
def init_db():
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # Water logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            amount_ml INTEGER,
            notes TEXT
        )
    ''')
    
    # Food logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            food_name TEXT,
            calories INTEGER,
            protein REAL,
            carbs REAL,
            fat REAL,
            notes TEXT
        )
    ''')
    
    # Todos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            priority INTEGER DEFAULT 1
        )
    ''')
    
    # Reminders
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            scheduled_time DATETIME,
            sent BOOLEAN DEFAULT FALSE,
            completed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Gym logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gym_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            muscle_groups TEXT,
            exercises TEXT,
            notes TEXT,
            duration INTEGER
        )
    ''')
    
    # Calendar events cache
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_event_id TEXT UNIQUE,
            summary TEXT,
            start_time DATETIME,
            end_time DATETIME,
            location TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Image uploads tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS image_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            drive_file_id TEXT,
            category TEXT,
            original_message TEXT,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Processed Gmail messages tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Load hardcoded food database
def load_food_database():
    try:
        with open(config.FOOD_DATABASE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create empty database if it doesn't exist
        return {}

FOOD_DATABASE = load_food_database()

# Core message processing
class EnhancedMessageProcessor:
    def __init__(self):
        # Load custom food database
        try:
            with open('custom_food_database.json', 'r') as f:
                custom_food_db = json.load(f)
                print("✅ Custom food database loaded")
        except FileNotFoundError:
            print("⚠️  custom_food_database.json not found, using default")
            custom_food_db = FOOD_DATABASE
        
        self.nlp_processor = create_intelligent_processor(custom_food_db)
        self.google_services = google_services
    
    def process_message(self, message_body):
        """Main message processing pipeline using intelligent NLP"""
        # Use intelligent NLP processor to classify intent and extract entities
        intent = self.nlp_processor.classify_intent(message_body)
        entities = self.nlp_processor.extract_entities(message_body)
        
        print(f"🧠 Intelligent NLP Results:")
        print(f"   Intent: {intent}")
        print(f"   Entities: {entities}")
        
        # Process based on intent
        response = self.handle_intent(intent, message_body, entities)
        if response:
            return response
        
        return self.fallback_response(message_body)
    
    def handle_intent(self, intent, message, entities):
        """Handle specific intent using intelligent NLP"""
        if intent == 'water_logging':
            return self.handle_water(message, entities)
        elif intent == 'food_logging':
            return self.handle_food(message, entities)
        elif intent == 'gym_workout':
            return self.handle_gym(message, entities)
        elif intent == 'todo_add':
            return self.handle_todo(message, entities)
        elif intent == 'reminder_set':
            return self.handle_reminder(message, entities)
        elif intent == 'calendar_event':
            return self.handle_calendar(message, entities)
        elif intent == 'schedule_check':
            return self.handle_schedule_check(message, entities)
        elif intent == 'photo_upload':
            return self.handle_image_upload(message, entities)
        elif intent == 'unknown':
            return self.fallback_response(message)
        
        return None
    
    def handle_water(self, message, entities):
        """Handle water logging using enhanced NLP processor"""
        amount_ml = self.nlp_processor.parse_water_amount(message, entities)
        if amount_ml:
            self.log_water(amount_ml)
            oz = round(amount_ml / 29.5735, 1)
            return f"✅ Logged {oz}oz water ({amount_ml}ml)"
        return None
    
    def log_water(self, amount_ml):
        """Log water intake to database"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO water_logs (amount_ml) VALUES (?)',
            (amount_ml,)
        )
        conn.commit()
        conn.close()
    
    def handle_food(self, message, entities):
        """Handle food logging using enhanced NLP processor"""
        foods = entities.get('foods', [])
        if foods:
            food_info = self.parse_food_from_entities(message, foods[0])
            if food_info:
                self.log_food(food_info)
                return f"✅ Logged {food_info['calories']} cal ({food_info['protein']}p/{food_info['carbs']}c/{food_info['fat']}f)"
            else:
                # Unknown food - log and remind
                unknown_food = foods[0]
                self.log_unknown_food(unknown_food)
                self.schedule_food_reminder(unknown_food)
                return f"Logged '{unknown_food}' as unknown food. I'll remind you tonight to add the macros."
        return None
    
    def parse_food_from_entities(self, message, food_name):
        """Parse known food with portion multiplier"""
        # Find matching food in database
        for food_key, food_data in self.food_db.items():
            if food_data['display_name'].lower() == food_name.lower():
                # Handle portions using enhanced NLP processor
                multiplier = self.nlp_processor.parse_portion_multiplier(message)
                return {
                    'name': food_data['display_name'],
                    'calories': int(food_data['calories'] * multiplier),
                    'protein': round(food_data['protein'] * multiplier, 1),
                    'carbs': round(food_data['carbs'] * multiplier, 1),
                    'fat': round(food_data['fat'] * multiplier, 1)
                }
        return None
    
    def log_food(self, food_info):
        """Log food to database"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO food_logs (food_name, calories, protein, carbs, fat)
            VALUES (?, ?, ?, ?, ?)
        ''', (food_info['name'], food_info['calories'], 
              food_info['protein'], food_info['carbs'], food_info['fat']))
        conn.commit()
        conn.close()
    
    def log_unknown_food(self, food_name):
        """Log unknown food"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO food_logs (food_name, calories, protein, carbs, fat, notes)
            VALUES (?, 0, 0, 0, 0, 'UNKNOWN - needs macros')
        ''', (food_name,))
        conn.commit()
        conn.close()
    
    def schedule_food_reminder(self, food_name):
        """Schedule evening reminder to add food to database"""
        reminder_time = datetime.now().replace(hour=config.EVENING_REMINDER_HOUR, minute=0, second=0, microsecond=0)
        if reminder_time <= datetime.now():
            reminder_time += timedelta(days=1)
        
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reminders (text, scheduled_time)
            VALUES (?, ?)
        ''', (f"Add macros for '{food_name}' to food database", reminder_time))
        conn.commit()
        conn.close()
    
    def handle_gym(self, message, entities):
        """Handle gym workout logging using enhanced NLP processor"""
        workout_data = self.nlp_processor.parse_gym_workout(message)
        if workout_data:
            self.log_gym_workout(workout_data)
            
            # Build response message
            exercises = workout_data['exercises']
            exercise_details = []
            for ex in exercises:
                if ex['reps']:
                    detail = f"{ex['name']} {ex['weight']}x{ex['reps']}"
                    if ex['sets'] > 1:
                        detail += f"x{ex['sets']}"
                else:
                    detail = f"{ex['name']} {ex['weight']}"
                exercise_details.append(detail)
            
            response = f"💪 Logged {workout_data['muscle_group']} workout: {', '.join(exercise_details)}"
            return response
        
        return None
    
    def log_gym_workout(self, workout_data):
        """Log gym workout to database"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO gym_logs (date, muscle_groups, exercises)
            VALUES (?, ?, ?)
        ''', (datetime.now().date(), workout_data['muscle_group'], json.dumps(workout_data['exercises'])))
        conn.commit()
        conn.close()
    
    def handle_todo(self, message, entities):
        """Handle todo creation using enhanced NLP processor"""
        tasks = entities.get('tasks', [])
        if tasks:
            task = tasks[0]
            self.add_todo(task)
            return f"✅ Added to todo list: {task}"
        return None
    
    def add_todo(self, task):
        """Add todo to database"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO todos (text) VALUES (?)', (task,))
        conn.commit()
        conn.close()
    
    def handle_reminder(self, message, entities):
        """Handle reminder creation using enhanced NLP processor"""
        reminder_data = self.nlp_processor.parse_reminder(message)
        if reminder_data:
            self.schedule_reminder(reminder_data)
            
            time_str = reminder_data['scheduled_time'].strftime("%I:%M %p")
            date_str = reminder_data['scheduled_time'].strftime("%B %d")
            
            response = f"⏰ Reminder set: {reminder_data['text']} on {date_str} at {time_str}"
            if reminder_data['priority'] == 'high':
                response += " (URGENT)"
            return response
        
        return None
    
    def schedule_reminder(self, reminder_data):
        """Schedule reminder to database"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reminders (text, scheduled_time)
            VALUES (?, ?)
        ''', (reminder_data['text'], reminder_data['scheduled_time']))
        conn.commit()
        conn.close()
    
    def handle_calendar(self, message, entities):
        """Handle calendar event creation using enhanced NLP processor"""
        event_data = self.nlp_processor.parse_calendar_event(message)
        if event_data:
            # Create calendar event via Google services
            event_id = self.google_services.create_calendar_event(
                summary=event_data['title'],
                start_time=event_data['start_time'],
                end_time=event_data['end_time'],
                description=event_data['description'],
                location=event_data['location']
            )
            
            if event_id:
                start_time_str = event_data['start_time'].strftime("%I:%M %p")
                end_time_str = event_data['end_time'].strftime("%I:%M %p")
                response = f"📅 Event created: {event_data['title']} from {start_time_str} to {end_time_str}"
                if event_data['location']:
                    response += f" at {event_data['location']}"
                return response
            else:
                return "❌ Failed to create calendar event"
        
        return None
    
    def handle_schedule_check(self, message, entities):
        """Handle schedule checking queries"""
        schedule_query = self.nlp_processor.parse_schedule_query(message)
        if schedule_query:
            # Get schedule from Google Calendar
            events = self.google_services.get_calendar_events(
                start_date=schedule_query['date']
            )
            
            if events:
                response = f"📅 Schedule for {schedule_query['date'].strftime('%B %d')}:\n"
                for event in events[:5]:  # Show first 5 events
                    # Parse the start time from Google's format
                    start_time = event['start']
                    if 'T' in start_time:  # Has time component
                        try:
                            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            time_str = dt.strftime("%I:%M %p")
                        except:
                            time_str = "All day"
                    else:
                        time_str = "All day"
                    
                    response += f"• {time_str}: {event['summary']}\n"
                if len(events) > 5:
                    response += f"... and {len(events) - 5} more events"
                return response
            else:
                return f"📅 No events scheduled for {schedule_query['date'].strftime('%B %d')}"
        
        return None
    
    def handle_event_modification(self, message, entities):
        """Handle calendar event modifications"""
        # This is a simplified version - you can enhance this
        return "📅 Event modification coming soon! For now, you can create new events."
    
    def handle_image_upload(self, message, entities):
        """Handle photo upload requests"""
        photo_data = self.nlp_processor.parse_photo_upload(message)
        if photo_data:
            # For now, acknowledge the request
            # TODO: Implement actual photo upload when image is attached
            response = f"📸 Photo upload request received for {photo_data['target_folder']} folder"
            response += "\n💡 Note: Photo uploads will be implemented when you attach images"
            return response
        
        return None
    
    def handle_drive_organization(self, message, entities):
        """Handle drive organization requests"""
        drive_data = self.nlp_processor.parse_drive_organization(message)
        if drive_data:
            response = f"📁 Drive organization request received"
            if drive_data['file_type']:
                response += f" for {drive_data['file_type']}"
            if drive_data['target_folder']:
                response += f" in {drive_data['target_folder']} folder"
            response += "\n💡 Note: File organization will be implemented for attached files"
            return response
        
        return None
    
    def cache_calendar_event(self, google_event_id, event_info):
        """Cache calendar event in database"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO calendar_events 
            (google_event_id, summary, start_time, end_time, location, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (google_event_id, event_info['summary'], event_info['start_time'],
              event_info['end_time'], event_info['location'], event_info['description']))
        conn.commit()
        conn.close()
    
    def handle_completion(self, message, entities):
        """Handle task/reminder completions"""
        completion_patterns = [
            'did', 'done', 'finished', 'completed', 'called', 'went'
        ]
        
        if any(pattern in message for pattern in completion_patterns):
            # Try to match and complete tasks/reminders
            self.mark_recent_task_complete(message)
            return "✅ Task marked as complete!"
        return None
    
    def mark_recent_task_complete(self, message):
        """Mark recent task as complete based on message content"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Simple approach: mark the most recent incomplete todo as complete
        cursor.execute('''
            UPDATE todos SET completed_at = CURRENT_TIMESTAMP 
            WHERE completed_at IS NULL 
            ORDER BY created_at DESC LIMIT 1
        ''')
        
        cursor.execute('''
            UPDATE reminders SET completed_at = CURRENT_TIMESTAMP 
            WHERE completed_at IS NULL 
            ORDER BY created_at DESC LIMIT 1
        ''')
        
        conn.commit()
        conn.close()
    
    def fallback_response(self, message):
        """Fallback response for unrecognized messages"""
        return "🤔 I didn't understand that. Try:\n• 'drank a bottle' (water)\n• 'ate [food]' (food logging)\n• 'remind me to [task]' (reminders)\n• 'todo [task]' (todos)\n• 'meeting with John tomorrow 2pm' (calendar)\n• 'save receipt' (image upload)"

# Routes
@app.route('/webhook/gmail', methods=['POST'])
def gmail_webhook():
    """Handle incoming Gmail webhook (Google Voice SMS forwarded to Gmail)"""
    try:
        # Verify webhook secret
        webhook_secret = request.headers.get('X-Webhook-Secret')
        if webhook_secret != config.GMAIL_WEBHOOK_SECRET:
            return '', 403
        
        # Process webhook data
        webhook_data = request.get_json()
        if not webhook_data:
            return '', 400
        
        # Process Gmail message
        message_data = google_services.process_gmail_webhook(webhook_data)
        if not message_data:
            return '', 200  # Not a relevant message
        
        print(f"=== INCOMING SMS VIA GMAIL ===")
        print(f"Message: '{message_data['body']}'")
        print(f"Timestamp: {message_data['timestamp']}")
        print("===============================")
        
        # Process message with enhanced processor
        processor = EnhancedMessageProcessor()
        response_text = processor.process_message(message_data['body'])
        
        print(f"Response: {response_text}")
        
        # Send response via push notification
        if response_text:
            google_services.send_push_notification(
                "Alfred the Butler", 
                response_text
            )
        
        return '', 200
        
    except Exception as e:
        print(f"Error processing Gmail webhook: {e}")
        return '', 500

@app.route('/webhook/sms', methods=['POST'])
def sms_webhook():
    """Legacy SMS webhook (kept for compatibility)"""
    message_body = request.form.get('Body', '')
    from_number = request.form.get('From', '')
    
    print(f"=== LEGACY SMS WEBHOOK ===")
    print(f"Message: '{message_body}'")
    print(f"From: '{from_number}'")
    print("===========================")
    
    # Process message
    processor = EnhancedMessageProcessor()
    response_text = processor.process_message(message_body)
    
    # For legacy webhook, return response in webhook format
    return jsonify({
        "response": response_text,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "google_services": "active",
        "nlp_processor": "enhanced"
    })

@app.route('/debug', methods=['GET'])
def debug_config():
    """Debug endpoint to check config values"""
    return jsonify({
        "PUSHOVER_EMAIL_ALIAS": config.PUSHOVER_EMAIL_ALIAS,
        "YOUR_PHONE_NUMBER": config.YOUR_PHONE_NUMBER,
        "HAS_GOOGLE_CREDENTIALS": bool(config.GOOGLE_CLIENT_ID),
        "DRIVE_FOLDERS": config.DRIVE_FOLDERS
    })

def send_push_notification(title, message):
    """Send push notification to user's phone"""
    try:
        success = google_services.send_push_notification(title, message)
        if success:
            print(f"📱 Push notification sent: {title}")
        else:
            print(f"❌ Failed to send push notification: {title}")
    except Exception as e:
        print(f"Error sending push notification: {e}")

def morning_checkin():
    """Daily 8am check-in"""
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get incomplete todos
        cursor.execute('''
            SELECT text FROM todos 
            WHERE completed_at IS NULL
            ORDER BY created_at
        ''')
        incomplete_todos = cursor.fetchall()
        
        # Get incomplete reminders from yesterday or earlier
        yesterday = datetime.now() - timedelta(days=1)
        cursor.execute('''
            SELECT text FROM reminders 
            WHERE completed_at IS NULL 
            AND scheduled_time <= ?
            ORDER BY scheduled_time
        ''', (yesterday,))
        incomplete_reminders = cursor.fetchall()
        
        # Get last gym session
        cursor.execute('''
            SELECT date, muscle_groups FROM gym_logs 
            ORDER BY date DESC LIMIT 1
        ''')
        last_gym = cursor.fetchone()
        
        # Get today's calendar events
        today = datetime.now()
        today_events = google_services.get_calendar_events(today, today + timedelta(days=1))
        
        conn.close()
        
        # Build message
        message_parts = ["Good morning! ☀️"]
        
        # Add incomplete items
        incomplete_items = []
        for todo in incomplete_todos:
            incomplete_items.append(todo[0])
        for reminder in incomplete_reminders:
            incomplete_items.append(reminder[0])
        
        if incomplete_items:
            items_text = ', '.join([f"{i+1}) {item}" for i, item in enumerate(incomplete_items)])
            message_parts.append(f"📋 Unfinished: {items_text}")
        
        # Add gym accountability
        if last_gym:
            last_date = datetime.strptime(last_gym[0], '%Y-%m-%d').date()
            days_since = (datetime.now().date() - last_date).days
            if days_since >= 2:
                message_parts.append(f"💪 Last workout: {days_since} days ago ({last_gym[1]}) - time for next session?")
        
        # Add today's schedule
        if today_events:
            event_list = []
            for event in today_events[:3]:  # Top 3 events
                start_time = event['start']
                if 'T' in start_time:
                    time_str = datetime.fromisoformat(start_time.replace('Z', '+00:00')).strftime('%I:%M%p')
                else:
                    time_str = 'All day'
                event_list.append(f"• {event['summary']} at {time_str}")
            
            message_parts.append(f"📅 Today's schedule:\n" + "\n".join(event_list))
        
        # Always add water/outside reminder
        message_parts.append("💧 Don't forget: drink water & get outside!")
        
        send_push_notification("Morning Check-in", '\n'.join(message_parts))
        
    except Exception as e:
        print(f"Error in morning check-in: {e}")

def check_pending_reminders():
    """Check for pending reminders every minute"""
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get reminders that should be sent now
        now = datetime.now()
        cursor.execute('''
            SELECT id, text FROM reminders 
            WHERE sent = FALSE 
            AND completed_at IS NULL
            AND scheduled_time <= ?
        ''', (now,))
        
        pending_reminders = cursor.fetchall()
        
        for reminder_id, reminder_text in pending_reminders:
            # Send reminder via push notification
            send_push_notification("Reminder", f"⏰ {reminder_text}")
            
            # Mark as sent
            cursor.execute('''
                UPDATE reminders SET sent = TRUE 
                WHERE id = ?
            ''', (reminder_id,))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error checking reminders: {e}")

def check_gmail_for_sms():
    """Check Gmail every 5 seconds for new SMS from Google Voice"""
    try:
        # Get the last processed message ID from database
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Create table to track processed messages if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Get last processed message ID
        cursor.execute('''
            SELECT message_id FROM processed_messages 
            ORDER BY processed_at DESC LIMIT 1
        ''')
        last_processed = cursor.fetchone()
        last_message_id = last_processed[0] if last_processed else None
        
        # Query Gmail for new messages
        try:
            # Get recent messages from Gmail
            messages_result = google_services.gmail_service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                maxResults=10,
                q='from:voice.google.com'  # Only messages from Google Voice
            ).execute()
            
            messages = messages_result.get('messages', [])
            
            if not messages:
                return
            
            # Process new messages
            for message in messages:
                message_id = message['id']
                
                # Skip if already processed
                if last_message_id and message_id == last_message_id:
                    break
                
                # Get full message details
                try:
                    full_message = google_services.gmail_service.users().messages().get(
                        userId='me', id=message_id
                    ).execute()
                    
                    # Extract message body
                    body = google_services._extract_message_body(full_message)
                    
                    if body:
                        print(f"📱 Processing SMS from Gmail: {body[:50]}...")
                        
                        # Process with your assistant
                        processor = EnhancedMessageProcessor()
                        response_text = processor.process_message(body)
                        
                        if response_text:
                            print(f"🤖 Generated response: {response_text}")
                            
                            # Send push notification instead of SMS
                            success = google_services.send_push_notification(
                                "Alfred the Butler",
                                response_text
                            )
                            
                            if success:
                                print(f"📱 Push notification sent successfully")
                            else:
                                print(f"❌ Failed to send push notification")
                        
                        # Mark as processed
                        cursor.execute('''
                            INSERT OR REPLACE INTO processed_messages (message_id)
                            VALUES (?)
                        ''', (message_id,))
                        
                except Exception as e:
                    print(f"Error processing message {message_id}: {e}")
                    continue
            
            conn.commit()
            
        except Exception as e:
            print(f"Error querying Gmail: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error in Gmail SMS check: {e}")

# Schedule morning check-in
scheduler.add_job(
    func=morning_checkin,
    trigger="cron",
    hour=config.MORNING_CHECKIN_HOUR,
    minute=0,
    id='morning_checkin'
)

# Schedule reminder checks every minute
scheduler.add_job(
    func=check_pending_reminders,
    trigger="interval",
    minutes=1,
    id='reminder_check'
)

# Schedule Gmail SMS checks every 5 seconds
scheduler.add_job(
    func=check_gmail_for_sms,
    trigger="interval",
    seconds=5,
    id='gmail_sms_check'
)

# Cleanup
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    print("🚀 Initializing Enhanced Personal SMS Assistant...")
    print("Features: Google Voice + Gmail, Drive, Calendar, Enhanced NLP, Push Notifications")
    
    init_db()
    print("Database initialized.")
    
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting Flask app on port {port}...")
    print(f"Morning check-in scheduled for {config.MORNING_CHECKIN_HOUR}:00 AM")
    print(f"📱 Gmail SMS polling: Every 5 seconds")
    print(f"📱 Responses via: Push Notifications")
    print(f"Gmail webhook endpoint: /webhook/gmail")
    print(f"Legacy SMS endpoint: /webhook/sms")
    
    app.run(debug=False, host='0.0.0.0', port=port)
