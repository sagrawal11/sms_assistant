from flask import Flask, request, jsonify
import sqlite3
import json
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from config import Config
from enhanced_nlp_processor import create_enhanced_processor
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
        self.food_db = FOOD_DATABASE
        self.nlp_processor = create_enhanced_processor(self.food_db)
        self.google_services = google_services
    
    def process_message(self, message_body):
        """Main message processing pipeline using enhanced NLP"""
        message = message_body.lower().strip()
        
        # Use enhanced NLP processor to classify intent and extract entities
        intents = self.nlp_processor.classify_intent(message)
        entities = self.nlp_processor.extract_entities(message)
        
        print(f"Intents: {intents}")
        print(f"Entities: {entities}")
        
        # Process based on intents
        for intent in intents:
            response = self.handle_intent(intent, message, entities)
            if response:
                return response
        
        return self.fallback_response(message)
    
    def handle_intent(self, intent, message, entities):
        """Handle specific intent"""
        if intent == 'water':
            return self.handle_water(message, entities)
        elif intent == 'food':
            return self.handle_food(message, entities)
        elif intent == 'gym':
            return self.handle_gym(message, entities)
        elif intent == 'todo':
            return self.handle_todo(message, entities)
        elif intent == 'reminder':
            return self.handle_reminder(message, entities)
        elif intent == 'calendar' or intent == 'create_event':
            return self.handle_calendar(message, entities)
        elif intent == 'check_schedule':
            return self.handle_schedule_check(message, entities)
        elif intent == 'modify_event':
            return self.handle_event_modification(message, entities)
        elif intent == 'image':
            return self.handle_image_upload(message, entities)
        elif intent == 'drive':
            return self.handle_drive_organization(message, entities)
        elif intent == 'completion':
            return self.handle_completion(message, entities)
        
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
        """Handle gym logging using enhanced NLP processor"""
        muscle_groups = self.nlp_processor.extract_muscle_groups(message)
        if muscle_groups:
            gym_info = {
                'muscle_groups': ', '.join(muscle_groups),
                'exercises': message,  # Store full message for now
                'date': datetime.now().date()
            }
            self.log_gym(gym_info)
            return f"✅ Logged workout: {', '.join(muscle_groups)}"
        return None
    
    def log_gym(self, gym_info):
        """Log gym workout"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO gym_logs (date, muscle_groups, exercises)
            VALUES (?, ?, ?)
        ''', (gym_info['date'], gym_info['muscle_groups'], gym_info['exercises']))
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
        tasks = entities.get('tasks', [])
        if tasks or 'remind me' in message:
            reminder_time = self.nlp_processor.parse_time_reference(message)
            text = tasks[0] if tasks else message.split('remind me')[-1].strip('to ')
            
            reminder_info = {
                'text': text,
                'time': reminder_time
            }
            self.add_reminder(reminder_info)
            return f"✅ Reminder set: {text} at {reminder_time.strftime('%m/%d %I:%M%p')}"
        return None
    
    def add_reminder(self, reminder_info):
        """Add reminder to database"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reminders (text, scheduled_time)
            VALUES (?, ?)
        ''', (reminder_info['text'], reminder_info['time']))
        conn.commit()
        conn.close()
    
    def handle_calendar(self, message, entities):
        """Handle calendar event creation"""
        event_info = self.nlp_processor.parse_calendar_event(message, entities)
        if event_info:
            # Create Google Calendar event
            event_id = self.google_services.create_calendar_event(
                summary=event_info['summary'],
                start_time=event_info['start_time'],
                end_time=event_info['end_time'],
                description=event_info['description'],
                location=event_info['location']
            )
            
            if event_id:
                # Cache event in database
                self.cache_calendar_event(event_id, event_info)
                return f"✅ Calendar event created: {event_info['summary']} on {event_info['start_time'].strftime('%m/%d at %I:%M%p')}"
            else:
                return "❌ Failed to create calendar event"
        
        return "📅 I couldn't understand the event details. Try: 'meeting with John tomorrow 2pm'"
    
    def handle_schedule_check(self, message, entities):
        """Handle schedule/calendar queries"""
        # Extract date range
        dates = entities.get('dates', [])
        if dates:
            start_date = datetime.now()
            if dates[0]['type'] == 'relative':
                if dates[0]['value'] == 'tomorrow':
                    start_date = datetime.now() + timedelta(days=1)
                elif dates[0]['value'] == 'next week':
                    start_date = datetime.now() + timedelta(days=7)
            
            end_date = start_date + timedelta(days=1)
        else:
            start_date = datetime.now()
            end_date = start_date + timedelta(days=1)
        
        # Get events from Google Calendar
        events = self.google_services.get_calendar_events(start_date, end_date)
        
        if events:
            event_list = []
            for event in events[:5]:  # Limit to 5 events
                start_time = event['start']
                if 'T' in start_time:  # Has time
                    time_str = datetime.fromisoformat(start_time.replace('Z', '+00:00')).strftime('%I:%M%p')
                else:  # All day
                    time_str = 'All day'
                
                event_list.append(f"• {event['summary']} at {time_str}")
            
            return f"📅 Your schedule:\n" + "\n".join(event_list)
        else:
            return f"📅 No events scheduled for {start_date.strftime('%m/%d')}"
    
    def handle_event_modification(self, message, entities):
        """Handle calendar event modifications"""
        # This is a simplified version - you can enhance this
        return "📅 Event modification coming soon! For now, you can create new events."
    
    def handle_image_upload(self, message, entities):
        """Handle image upload requests"""
        # Extract category from message
        category = self.nlp_processor.extract_image_category(message)
        
        # This would typically handle MMS or email attachments
        # For now, return instructions
        return f"📸 To upload an image to {category} folder:\n1. Send the image via MMS\n2. Include '{category}' in your message\n3. I'll organize it automatically!"
    
    def handle_drive_organization(self, message, entities):
        """Handle Google Drive organization requests"""
        return "📁 Drive organization features:\n• Send images to auto-organize\n• Use keywords: receipts, documents, work, personal\n• I'll create folders and organize automatically!"
    
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
        
        # Send response back via Google Voice
        if response_text:
            google_services.send_sms_via_gmail(
                config.YOUR_PHONE_NUMBER, 
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
        "GOOGLE_VOICE_NUMBER": config.GOOGLE_VOICE_NUMBER,
        "YOUR_PHONE_NUMBER": config.YOUR_PHONE_NUMBER,
        "HAS_GOOGLE_CREDENTIALS": bool(config.GOOGLE_CLIENT_ID),
        "DRIVE_FOLDERS": config.DRIVE_FOLDERS
    })

def send_sms(message):
    """Send outbound SMS via Google Voice"""
    try:
        success = google_services.send_sms_via_google_voice(
            config.YOUR_PHONE_NUMBER, 
            message
        )
        if success:
            print(f"📱 SMS response sent: {message}")
        else:
            print(f"❌ Failed to send SMS response: {message}")
    except Exception as e:
        print(f"Error sending SMS: {e}")

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
        
        send_sms('\n'.join(message_parts))
        
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
            # Send reminder
            send_sms(f"⏰ Reminder: {reminder_text}")
            
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
                            
                            # Send response back via Google Voice
                            success = google_services.send_sms_via_google_voice(
                                config.YOUR_PHONE_NUMBER,
                                response_text
                            )
                            
                            if success:
                                print(f"📤 Response sent successfully")
                            else:
                                print(f"❌ Failed to send response")
                        
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
    print("Features: Google Voice, Drive, Calendar, Enhanced NLP")
    
    init_db()
    print("Database initialized.")
    
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting Flask app on port {port}...")
    print(f"Morning check-in scheduled for {config.MORNING_CHECKIN_HOUR}:00 AM")
    print(f"📱 Gmail SMS polling: Every 5 seconds")
    print(f"Gmail webhook endpoint: /webhook/gmail")
    print(f"Legacy SMS endpoint: /webhook/sms")
    
    app.run(debug=False, host='0.0.0.0', port=port)
