import os
import sys
import json
import atexit
import sqlite3
import csv
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from hugging_face_nlp import create_intelligent_processor
from google_services import GoogleServicesManager
from communication_service import CommunicationService

# Check if another instance is already running
def check_single_instance():
    """Check if another instance of the app is already running"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', 5001))
        sock.close()
        return True
    except OSError:
        print("❌ Another instance is already running on port 5001")
        print("   Please stop the other instance first")
        return False

def daily_database_dump():
    """Export all database data to CSV files and clean the database for the next day"""
    try:
        print("🔄 Starting daily database dump at 5 AM...")
        
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Get today's date for filename
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # 1. Export food logs to CSV (append mode)
        cursor.execute('SELECT * FROM food_logs WHERE DATE(timestamp) = ?', (yesterday,))
        food_logs = cursor.fetchall()
        
        if food_logs:
            food_csv_path = os.path.join(data_dir, 'food_logs.csv')
            file_exists = os.path.exists(food_csv_path)
            
            with open(food_csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Only write headers if file is new
                if not file_exists:
                    writer.writerow(['id', 'timestamp', 'food_name', 'calories', 'protein', 'carbs', 'fat', 'restaurant', 'portion_multiplier'])
                writer.writerows(food_logs)
            print(f"📊 Appended {len(food_logs)} food logs to {food_csv_path}")
        
        # 2. Export water logs to CSV (append mode)
        cursor.execute('SELECT * FROM water_logs WHERE DATE(timestamp) = ?', (yesterday,))
        water_logs = cursor.fetchall()
        
        if water_logs:
            water_csv_path = os.path.join(data_dir, 'water_logs.csv')
            file_exists = os.path.exists(water_csv_path)
            
            with open(water_csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Only write headers if file is new
                if not file_exists:
                    writer.writerow(['id', 'timestamp', 'amount_ml', 'amount_oz'])
                writer.writerows(water_logs)
            print(f"💧 Appended {len(water_logs)} water logs to {water_csv_path}")
        
        # 3. Export gym logs to CSV (append mode)
        cursor.execute('SELECT * FROM gym_logs WHERE DATE(timestamp) = ?', (yesterday,))
        gym_logs = cursor.fetchall()
        
        if gym_logs:
            gym_csv_path = os.path.join(data_dir, 'gym_logs.csv')
            file_exists = os.path.exists(gym_csv_path)
            
            with open(gym_csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Only write headers if file is new
                if not file_exists:
                    writer.writerow(['id', 'timestamp', 'exercise', 'sets', 'reps', 'weight', 'notes'])
                writer.writerows(gym_logs)
            print(f"🏋️ Appended {len(gym_logs)} gym logs to {gym_csv_path}")
        
        # 4. Export reminders/todos to CSV (append mode)
        cursor.execute('SELECT * FROM reminders_todos WHERE DATE(timestamp) = ?', (yesterday,))
        reminder_logs = cursor.fetchall()
        
        if reminder_logs:
            reminder_csv_path = os.path.join(data_dir, 'reminders_todos.csv')
            file_exists = os.path.exists(reminder_csv_path)
            
            with open(reminder_csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Only write headers if file is new
                if not file_exists:
                    writer.writerow(['id', 'timestamp', 'type', 'content', 'due_date', 'completed', 'completed_at'])
                writer.writerows(reminder_logs)
            print(f"📝 Appended {len(reminder_logs)} reminders/todos to {reminder_csv_path}")
        
        # 5. Clean the database for the new day
        cursor.execute('DELETE FROM food_logs WHERE DATE(timestamp) < ?', (today,))
        cursor.execute('DELETE FROM water_logs WHERE DATE(timestamp) < ?', (today,))
        cursor.execute('DELETE FROM gym_logs WHERE DATE(timestamp) < ?', (today,))
        cursor.execute('DELETE FROM reminders_todos WHERE DATE(timestamp) < ?', (today,))
        
        # Keep calendar events cache (don't delete these)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Daily database dump completed! Database cleaned for {today}")
        
    except Exception as e:
        print(f"❌ Error during daily database dump: {e}")

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize services
try:
    google_services = GoogleServicesManager()
    print("✅ Google services initialized")
except Exception as e:
    print(f"⚠️  Google services failed to initialize: {e}")
    google_services = None

communication_service = CommunicationService()

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

# Ensure required directories exist
def ensure_directories():
    """Create required directories if they don't exist"""
    try:
        # Debug: Show current working directory
        print(f"🔍 Current working directory: {os.getcwd()}")
        
        # Create databases directory
        db_dir = os.path.dirname(config.DATABASE_PATH)
        print(f"🔍 Database directory path: {db_dir}")
        print(f"🔍 Full database path: {config.DATABASE_PATH}")
        os.makedirs(db_dir, exist_ok=True)
        print(f"✅ Database directory ensured: {db_dir}")
        
        # Create data directory
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        print(f"🔍 Data directory path: {data_dir}")
        os.makedirs(data_dir, exist_ok=True)
        print(f"✅ Data directory ensured: {data_dir}")
        
        # Check if files actually exist
        if os.path.exists(config.DATABASE_PATH):
            print(f"✅ Database file exists: {config.DATABASE_PATH}")
        else:
            print(f"❌ Database file missing: {config.DATABASE_PATH}")
            
        if os.path.exists(config.FOOD_DATABASE_PATH):
            print(f"✅ Food database exists: {config.FOOD_DATABASE_PATH}")
        else:
            print(f"❌ Food database missing: {config.FOOD_DATABASE_PATH}")
        
    except Exception as e:
        print(f"⚠️  Error creating directories: {e}")

# Create directories before initializing services
ensure_directories()

# Initialize Google services
# google_services = GoogleServicesManager() # This line is now redundant as it's initialized above

def check_reminders():
    """Check for due reminders and send push notifications"""
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get all due reminders that haven't been sent
        current_time = datetime.now()
        cursor.execute('''
            SELECT id, content, due_date FROM reminders_todos 
            WHERE type = 'reminder' 
            AND completed = FALSE 
            AND due_date <= ?
        ''', (current_time,))
        
        due_reminders = cursor.fetchall()
        
        for reminder_id, content, due_date in due_reminders:
            # Send reminder via communication service
            message = f"⏰ REMINDER: {content}"
            result = communication_service.send_response(message)
            
            if result['success']:
                print(f"🔔 Reminder sent via {result['method']}: {content}")
                
                # Mark as completed
                cursor.execute('''
                    UPDATE reminders_todos 
                    SET completed = TRUE, completed_at = ? 
                    WHERE id = ?
                ''', (current_time, reminder_id))
            else:
                print(f"❌ Failed to send reminder: {result.get('error', 'Unknown error')}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking reminders: {e}")

# Scheduler will be initialized after all functions are defined

@app.route('/csv/<filename>')
def view_csv(filename):
    """View the contents of a CSV file"""
    try:
        # Validate filename to prevent directory traversal
        allowed_files = ['food_logs.csv', 'water_logs.csv', 'gym_logs.csv', 'reminders_todos.csv']
        if filename not in allowed_files:
            return jsonify({'error': 'Invalid filename'}), 400
        
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        csv_path = os.path.join(data_dir, filename)
        
        if not os.path.exists(csv_path):
            return jsonify({'error': 'CSV file not found'}), 404
        
        # Read CSV and return as JSON
        data = []
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
        
        return jsonify({
            'filename': filename,
            'row_count': len(data),
            'data': data[:100],  # Limit to first 100 rows for performance
            'total_rows': len(data)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error reading CSV: {str(e)}'}), 500

@app.route('/csvs')
def list_csvs():
    """List all available CSV files with their sizes"""
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        
        if not os.path.exists(data_dir):
            return jsonify({'csvs': []})
        
        csv_files = []
        for filename in os.listdir(data_dir):
            if filename.endswith('.csv'):
                file_path = os.path.join(data_dir, filename)
                file_size = os.path.getsize(file_path)
                csv_files.append({
                    'filename': filename,
                    'size_bytes': file_size,
                    'size_kb': round(file_size / 1024, 2)
                })
        
        return jsonify({'csvs': csv_files})
        
    except Exception as e:
        return jsonify({'error': f'Error listing CSVs: {str(e)}'}), 500

# Add manual dump endpoint
@app.route('/dump', methods=['POST'])
def manual_dump():
    """Manual database dump endpoint"""
    try:
        daily_database_dump()
        return jsonify({
            'status': 'success',
            'message': 'Database dumped successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Dump failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

# Database initialization
def init_db():
    """Initialize the database with all required tables"""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create food logs table with enhanced fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            food_name TEXT NOT NULL,
            calories INTEGER NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fat REAL NOT NULL,
            restaurant TEXT,
            portion_multiplier REAL DEFAULT 1.0
        )
    ''')
    
    # Create water logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            amount_ml REAL NOT NULL,
            amount_oz REAL NOT NULL
        )
    ''')
    
    # Create gym logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gym_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            exercise TEXT NOT NULL,
            sets INTEGER,
            reps INTEGER,
            weight REAL,
            notes TEXT
        )
    ''')
    
    # Create reminders and todos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders_todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            due_date DATETIME,
            completed BOOLEAN DEFAULT FALSE,
            completed_at DATETIME
        )
    ''')
    
    # Create calendar events cache table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_event_id TEXT UNIQUE NOT NULL,
            summary TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            location TEXT,
            description TEXT,
            cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with all tables")

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
            with open(config.FOOD_DATABASE_PATH, 'r') as f:
                custom_food_db = json.load(f)
                print("✅ Custom food database loaded")
        except FileNotFoundError:
            print("⚠️  Custom food database not found, using default")
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
        """Handle food logging"""
        food_data = self.nlp_processor.parse_food(message)
        if food_data:
            # Extract nutrition info
            food_info = food_data['food_data']
            portion_mult = food_data['portion_multiplier']
            
            # Calculate actual nutrition based on portion
            calories = int(food_info['calories'] * portion_mult)
            protein = round(food_info['protein'] * portion_mult, 1)
            carbs = round(food_info['carbs'] * portion_mult, 1)
            fat = round(food_info['fat'] * portion_mult, 1)
            
            # Log to database
            self.log_food(
                food_name=food_data['food_name'],
                calories=calories,
                protein=protein,
                carbs=carbs,
                fat=fat,
                restaurant=food_data['restaurant'],
                portion_multiplier=portion_mult
            )
            
            # Format response
            serving_info = f" ({food_info['serving_size']})" if 'serving_size' in food_info else ""
            response = f"🍽️ Logged {food_data['food_name'].replace('_', ' ').title()}{serving_info}\n"
            response += f"📊 Nutrition: {calories} cal, {protein}g protein, {carbs}g carbs, {fat}g fat"
            
            return response
        
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
    
    def log_food(self, food_name, calories, protein, carbs, fat, restaurant=None, portion_multiplier=1.0):
        """Log food to database"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO food_logs (food_name, calories, protein, carbs, fat, restaurant, portion_multiplier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (food_name, calories, protein, carbs, fat, restaurant, portion_multiplier))
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
            # Store reminder in database
            self.schedule_reminder(reminder_data)
            
            # Format response
            time_str = reminder_data['due_date'].strftime("%I:%M %p")
            date_str = reminder_data['due_date'].strftime("%B %d")
            
            response = f"⏰ Reminder set: {reminder_data['content']} on {date_str} at {time_str}"
            if reminder_data.get('priority') == 'high':
                response += " (URGENT)"
            return response
        
        return None
    
    def schedule_reminder(self, reminder_data):
        """Schedule reminder to database"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reminders_todos (type, content, due_date, completed)
            VALUES (?, ?, ?, FALSE)
        ''', ('reminder', reminder_data['content'], reminder_data['due_date']))
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
            UPDATE reminders_todos SET completed_at = CURRENT_TIMESTAMP 
            WHERE completed_at IS NULL 
            ORDER BY timestamp DESC LIMIT 1
        ''')
        
        conn.commit()
        conn.close()
    
    def fallback_response(self, message):
        """Fallback response for unrecognized messages"""
        return "🤔 I didn't understand that. Try:\n• 'drank a bottle' (water)\n• 'ate [food]' (food logging)\n• 'remind me to [task]' (reminders)\n• 'todo [task]' (todos)\n• 'meeting with John tomorrow 2pm' (calendar)\n• 'save receipt' (image upload)"

# Routes
@app.route('/webhook/signalwire', methods=['POST'])
def signalwire_webhook():
    """Handle incoming SMS from SignalWire"""
    try:
        data = request.get_json()
        
        # Extract SMS data from SignalWire webhook
        if data.get('type') == 'message':
            from_number = data.get('from_number')
            to_number = data.get('to_number')
            message_body = data.get('body', '')
            message_id = data.get('id')
            
            print(f"📱 SignalWire SMS received from {from_number}: {message_body}")
            
            # Process the message
            processor = EnhancedMessageProcessor()
            response_text = processor.process_message(message_body)
            
            # Send response back via SignalWire
            if response_text:
                result = communication_service.send_response(response_text, from_number)
                
                if result['success']:
                    print(f"✅ Response sent via {result['method']}: {response_text}")
                else:
                    print(f"❌ Failed to send response: {result.get('error', 'Unknown error')}")
            
            return jsonify({'status': 'success', 'message_id': message_id}), 200
        else:
            return jsonify({'status': 'ignored', 'type': data.get('type')}), 200
            
    except Exception as e:
        print(f"❌ Error processing SignalWire webhook: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

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

@app.route('/health')
def health_check():
    """Health check endpoint for local testing"""
    try:
        # Get database stats
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Count records in each table
        cursor.execute('SELECT COUNT(*) FROM food_logs')
        food_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM water_logs')
        water_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM gym_logs')
        gym_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM reminders_todos')
        reminder_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM calendar_events')
        calendar_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Get communication service status
        comm_status = communication_service.get_status()
        
        return jsonify({
            "status": "healthy", 
            "timestamp": datetime.now().isoformat(),
            "service": "Alfred the Butler (Local)",
            "environment": "development",
            "communication": comm_status,
            "database_stats": {
                "food_logs": food_count,
                "water_logs": water_count,
                "gym_logs": gym_count,
                "reminders_todos": reminder_count,
                "calendar_events": calendar_count
            },
            "scheduled_jobs": [
                "Morning Check-in (every day)",
                "Reminder Checker (every 1m)",
                "Daily Database Dump (5:00 AM)"
            ]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

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
            SELECT text FROM reminders_todos 
            WHERE completed_at IS NULL 
            AND due_date <= ?
            ORDER BY due_date
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

# Old Gmail SMS checking function removed - now using SignalWire webhooks

# Initialize the scheduler (after all functions are defined)
scheduler = BackgroundScheduler(
    job_defaults={
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 15
    }
)

# Add jobs to scheduler
scheduler.add_job(
    func=morning_checkin,
    trigger='cron',
    hour=config.MORNING_CHECKIN_HOUR,
    id='morning_checkin',
    name='Morning Check-in',
    replace_existing=True
)

scheduler.add_job(
    func=check_reminders,
    trigger=IntervalTrigger(minutes=1),
    id='check_reminders',
    name='Reminder Checker',
    replace_existing=True
)

scheduler.add_job(
    func=daily_database_dump,
    trigger='cron',
    hour=5,
    id='daily_dump',
    name='Daily Database Dump',
    replace_existing=True
)

# Cleanup
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    # Check if another instance is already running
    if not check_single_instance():
        exit(1)
    
    # Get port from environment (for cloud deployment) or use default
    port = int(os.getenv('PORT', 5001))
    host = '0.0.0.0' if os.getenv('RENDER') else 'localhost'
    
    print(f"🚀 Starting Alfred the Butler on {host}:{port}")
    print(f"🌐 Health check: http://{host}:{port}/health")
    print(f"📱 SignalWire webhook: http://{host}:{port}/webhook/signalwire")
    
    # Start the scheduler
    scheduler.start()
    print("⏰ Background scheduler started")
    
    # Start the Flask app
    app.run(host=host, port=port, debug=False)
