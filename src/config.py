import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Pushover settings for push notifications
    PUSHOVER_EMAIL_ALIAS = os.environ.get('PUSHOVER_EMAIL_ALIAS')
    YOUR_PHONE_NUMBER = os.environ.get('YOUR_PHONE_NUMBER')  # Keep for reference
    
    # Google APIs
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    
    # Gmail webhook settings
    GMAIL_WEBHOOK_SECRET = os.environ.get('GMAIL_WEBHOOK_SECRET')
    
    # Google Drive folder IDs for organization
    DRIVE_FOLDERS = {
        'receipts': os.environ.get('DRIVE_RECEIPTS_FOLDER_ID'),
        'documents': os.environ.get('DRIVE_DOCUMENTS_FOLDER_ID'),
        'photos': os.environ.get('DRIVE_PHOTOS_FOLDER_ID'),
        'work': os.environ.get('DRIVE_WORK_FOLDER_ID'),
        'personal': os.environ.get('DRIVE_PERSONAL_FOLDER_ID')
    }
    
    # Database
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'personal_assistant.db')
    FOOD_DATABASE_PATH = os.environ.get('FOOD_DATABASE_PATH', 'food_database.json')
    
    # Scheduling
    MORNING_CHECKIN_HOUR = int(os.environ.get('MORNING_CHECKIN_HOUR', 8))
    EVENING_REMINDER_HOUR = int(os.environ.get('EVENING_REMINDER_HOUR', 20))
    DEFAULT_REMINDER_HOUR = int(os.environ.get('DEFAULT_REMINDER_HOUR', 19))
    
    # Personal defaults
    DEFAULT_WATER_BOTTLE_ML = int(os.environ.get('DEFAULT_WATER_BOTTLE_ML', 710))  # 24oz
    DEFAULT_LUNCH_TIME = int(os.environ.get('DEFAULT_LUNCH_TIME', 12))
    DEFAULT_MEETING_DURATION = int(os.environ.get('DEFAULT_MEETING_DURATION', 60))  # minutes
    
    # Image processing
    MAX_IMAGE_SIZE = int(os.environ.get('MAX_IMAGE_SIZE', 10 * 1024 * 1024))  # 10MB
    SUPPORTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            'PUSHOVER_EMAIL_ALIAS',
            'GOOGLE_CLIENT_ID',
            'GOOGLE_CLIENT_SECRET',
            'GMAIL_WEBHOOK_SECRET'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        return True