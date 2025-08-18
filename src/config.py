import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Google API Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GMAIL_WEBHOOK_SECRET = os.getenv('GMAIL_WEBHOOK_SECRET')
    GOOGLE_CREDENTIALS_FILE = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'config',
        'client_secrets.json'
    )
    
    # Pushover Configuration (fallback)
    PUSHOVER_EMAIL_ALIAS = os.getenv('PUSHOVER_EMAIL_ALIAS')
    
    # SignalWire Configuration (primary SMS)
    SIGNALWIRE_PROJECT_ID = os.getenv('SIGNALWIRE_PROJECT_ID')
    SIGNALWIRE_AUTH_TOKEN = os.getenv('SIGNALWIRE_AUTH_TOKEN')
    SIGNALWIRE_SPACE_URL = os.getenv('SIGNALWIRE_SPACE_URL', 'https://the-butler.signalwire.com')
    SIGNALWIRE_PHONE_NUMBER = os.getenv('SIGNALWIRE_PHONE_NUMBER')
    
    # Communication Mode
    COMMUNICATION_MODE = os.getenv('COMMUNICATION_MODE', 'hybrid')  # 'sms', 'push', 'hybrid'
    
    # App Settings
    MORNING_CHECKIN_HOUR = int(os.getenv('MORNING_CHECKIN_HOUR', 8))
    GMAIL_POLLING_INTERVAL = int(os.getenv('GMAIL_POLLING_INTERVAL', 5))
    EVENING_REMINDER_HOUR = int(os.getenv('EVENING_REMINDER_HOUR', 20))
    
    # Database
    DATABASE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'databases',
        'personal_assistant.db'
    )
    
    # Food Database
    FOOD_DATABASE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data',
        'wu_foods.json'
    )
    
    # Google Drive Folders
    DRIVE_FOLDERS = {
        'receipts': os.getenv('DRIVE_RECEIPTS_FOLDER_ID'),
        'documents': os.getenv('DRIVE_DOCUMENTS_FOLDER_ID'),
        'photos': os.getenv('DRIVE_PHOTOS_FOLDER_ID'),
        'work': os.getenv('DRIVE_WORK_FOLDER_ID'),
        'personal': os.getenv('DRIVE_PERSONAL_FOLDER_ID')
    }
    
    # Legacy phone number (for compatibility)
    YOUR_PHONE_NUMBER = os.getenv('YOUR_PHONE_NUMBER', '')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = []
        
        # Check communication mode requirements
        if cls.COMMUNICATION_MODE in ['sms', 'hybrid']:
            required_vars.extend([
                'SIGNALWIRE_PROJECT_ID',
                'SIGNALWIRE_AUTH_TOKEN',
                'SIGNALWIRE_SPACE_URL',
                'SIGNALWIRE_PHONE_NUMBER'
            ])
        
        if cls.COMMUNICATION_MODE in ['push', 'hybrid']:
            required_vars.append('PUSHOVER_EMAIL_ALIAS')
        
        # Always require Google API for Gmail integration
        required_vars.extend([
            'GOOGLE_CLIENT_ID',
            'GOOGLE_CLIENT_SECRET',
            'GMAIL_WEBHOOK_SECRET'
        ])
        
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        return True
