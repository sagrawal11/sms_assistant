import os
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image
import io
import mimetypes
from config import Config
# Google Voice automation removed - using push notifications instead

# Google API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

class GoogleServicesManager:
    def __init__(self):
        self.config = Config()
        self.creds = None
        self.gmail_service = None
        self.drive_service = None
        self.calendar_service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google APIs"""
        if os.path.exists(self.config.GOOGLE_CREDENTIALS_FILE):
            self.creds = Credentials.from_authorized_user_file(
                self.config.GOOGLE_CREDENTIALS_FILE, SCOPES)
        
        # If no valid credentials available, let the user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secrets.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.config.GOOGLE_CREDENTIALS_FILE, 'w') as token:
                token.write(self.creds.to_json())
        
        # Build services
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
    
    # Old SMS methods removed - now using push notifications via email
    
    # Phone number cleaning removed - no longer needed
    
    def _send_gmail_to_self(self, subject: str, body: str) -> bool:
        """Send Gmail to yourself (for now)"""
        try:
            # Get your own email address from Gmail API
            profile = self.gmail_service.users().getProfile(userId='me').execute()
            your_email = profile['emailAddress']
            
            # Create properly formatted Gmail message
            message_body = f"""From: {your_email}
To: {your_email}
Subject: {subject}

{body}"""
            
            message_bytes = message_body.encode('utf-8')
            message_b64 = base64.urlsafe_b64encode(message_bytes).decode('utf-8')
            
            # Send via Gmail to yourself
            self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': message_b64}
            ).execute()
            
            print(f"📧 Response sent to your Gmail: {your_email}")
            return True
            
        except HttpError as error:
            print(f"Error sending Gmail to self: {error}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
    
    def _send_gmail_to_pushover(self, to_email: str, subject: str, body: str) -> bool:
        """Send email to Pushover email alias via Gmail API"""
        try:
            # Get user's email address
            profile = self.gmail_service.users().getProfile(userId='me').execute()
            user_email = profile['emailAddress']
            
            # Create properly formatted Gmail message
            message_body = f"""From: {user_email}
To: {to_email}
Subject: {subject}

{body}"""
            
            message_bytes = message_body.encode('utf-8')
            message_b64 = base64.urlsafe_b64encode(message_bytes).decode('utf-8')
            
            # Send via Gmail to Pushover
            self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': message_b64}
            ).execute()
            
            print(f"📧 Email sent to Pushover: {to_email}")
            return True
            
        except HttpError as error:
            print(f"Error sending Gmail to Pushover: {error}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
    
    def send_push_notification(self, title: str, message: str) -> bool:
        """Send push notification via email to Pushover email alias"""
        try:
            # Get Pushover email alias from environment
            pushover_email = os.environ.get('PUSHOVER_EMAIL_ALIAS')
            
            if not pushover_email:
                print("❌ Missing Pushover email alias in environment variables")
                print("💡 Set PUSHOVER_EMAIL_ALIAS in your .env file")
                return False
            
            # Create email content with title and message
            email_subject = title
            email_body = message
            
            # Send email via Gmail API to Pushover
            success = self._send_gmail_to_pushover(pushover_email, email_subject, email_body)
            
            if success:
                print(f"📱 Email sent to Pushover: {title}")
                return True
            else:
                print(f"❌ Failed to send email to Pushover")
                return False
                
        except Exception as e:
            print(f"Error sending to Pushover email: {e}")
            return False
    
    def process_gmail_webhook(self, webhook_data: Dict) -> Optional[Dict]:
        """Process incoming Gmail webhook data"""
        try:
            # Extract message data
            message_id = webhook_data.get('message', {}).get('data', '')
            if not message_id:
                return None
            
            # Get full message
            message = self.gmail_service.users().messages().get(
                userId='me', id=message_id).execute()
            
            # Check if it's from Google Voice
            headers = message['payload']['headers']
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), '')
            
            if 'voice.google.com' not in from_header:
                return None
            
            # Extract SMS content
            body = self._extract_message_body(message)
            if not body:
                return None
            
            return {
                'message_id': message_id,
                'body': body,
                'timestamp': datetime.fromtimestamp(
                    int(message['internalDate']) / 1000
                ).isoformat()
            }
            
        except HttpError as error:
            print(f"Error processing Gmail webhook: {error}")
            return None
    
    def _extract_message_body(self, message: Dict) -> Optional[str]:
        """Extract text body from Gmail message"""
        try:
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body']['data']
                        return base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                # Single part message
                data = message['payload']['body']['data']
                return base64.urlsafe_b64decode(data).decode('utf-8')
        except Exception as e:
            print(f"Error extracting message body: {e}")
        
        return None
    
    def upload_image_to_drive(self, image_data: bytes, filename: str, 
                            category: str = 'photos') -> Optional[str]:
        """Upload image to Google Drive with smart organization"""
        try:
            # Determine folder based on category
            folder_id = self._get_folder_id(category)
            
            # Process image if needed
            processed_image = self._process_image(image_data)
            
            # Create file metadata
            file_metadata = {
                'name': filename,
                'parents': [folder_id] if folder_id else []
            }
            
            # Upload file
            media = MediaIoBaseUpload(
                io.BytesIO(processed_image),
                mimetype='image/jpeg',
                resumable=True
            )
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()
            
            return file.get('id')
            
        except HttpError as error:
            print(f"Error uploading to Drive: {error}")
            return None
    
    def _process_image(self, image_data: bytes) -> bytes:
        """Process image for optimal storage"""
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (max 1920x1080)
            max_size = (1920, 1080)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save as JPEG with compression
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return image_data
    
    def _get_folder_id(self, category: str) -> Optional[str]:
        """Get Google Drive folder ID for category"""
        folder_id = self.config.DRIVE_FOLDERS.get(category)
        if folder_id:
            return folder_id
        
        # Create folder if it doesn't exist
        try:
            folder_metadata = {
                'name': category.title(),
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            # Update config with new folder ID
            self.config.DRIVE_FOLDERS[category] = folder['id']
            return folder['id']
            
        except HttpError as error:
            print(f"Error creating folder: {error}")
            return None
    
    def create_calendar_event(self, summary: str, start_time: datetime, 
                            end_time: datetime = None, description: str = None,
                            location: str = None) -> Optional[str]:
        """Create Google Calendar event"""
        try:
            if not end_time:
                end_time = start_time + timedelta(hours=1)
            
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/New_York',  # Adjust as needed
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/New_York',  # Adjust as needed
                }
            }
            
            if description:
                event['description'] = description
            if location:
                event['location'] = location
            
            event = self.calendar_service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return event['id']
            
        except HttpError as error:
            print(f"Error creating calendar event: {error}")
            return None
    
    def get_calendar_events(self, start_date: datetime, 
                           end_date: datetime = None) -> List[Dict]:
        """Get calendar events for date range"""
        try:
            if not end_date:
                end_date = start_date + timedelta(days=1)
            
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return [
                {
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'location': event.get('location', ''),
                    'description': event.get('description', '')
                }
                for event in events
            ]
            
        except HttpError as error:
            print(f"Error getting calendar events: {error}")
            return []
    
    def update_calendar_event(self, event_id: str, **kwargs) -> bool:
        """Update existing calendar event"""
        try:
            # Get current event
            event = self.calendar_service.events().get(
                calendarId='primary', eventId=event_id).execute()
            
            # Update fields
            for key, value in kwargs.items():
                if key in ['summary', 'description', 'location']:
                    event[key] = value
                elif key in ['start', 'end']:
                    event[key] = {
                        'dateTime': value.isoformat(),
                        'timeZone': 'America/New_York'
                    }
            
            # Update event
            self.calendar_service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            return True
            
        except HttpError as error:
            print(f"Error updating calendar event: {error}")
            return False
    
    def delete_calendar_event(self, event_id: str) -> bool:
        """Delete calendar event"""
        try:
            self.calendar_service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return True
        except HttpError as error:
            print(f"Error deleting calendar event: {error}")
            return False
