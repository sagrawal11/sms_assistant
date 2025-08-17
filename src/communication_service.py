"""
Communication Service for Alfred the Butler
Handles SMS via SignalWire and push notifications as fallback
"""

import os
import sys
import requests
from datetime import datetime
from typing import Optional, Dict, Any

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

class CommunicationService:
    """Handles all communication methods for Alfred the Butler"""
    
    def __init__(self):
        self.config = Config()
        self.mode = self.config.COMMUNICATION_MODE
        
        # Initialize SignalWire client if SMS mode is enabled
        self.signalwire_client = None
        if self.mode in ['sms', 'hybrid']:
            self._init_signalwire()
    
    def _init_signalwire(self):
        """Initialize SignalWire client"""
        try:
            from signalwire.rest import Client as signalwire_client
            
            self.signalwire_client = signalwire_client(
                username=self.config.SIGNALWIRE_PROJECT_ID,
                password=self.config.SIGNALWIRE_AUTH_TOKEN,
                account_sid=self.config.SIGNALWIRE_PROJECT_ID
            )
            print("✅ SignalWire client initialized successfully")
            
        except ImportError:
            print("⚠️  SignalWire package not installed. SMS functionality disabled.")
            self.signalwire_client = None
        except Exception as e:
            print(f"❌ Failed to initialize SignalWire: {e}")
            self.signalwire_client = None
    
    def send_response(self, message: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Send response using the configured communication method
        
        Args:
            message: The message to send
            phone_number: Phone number to send SMS to (if SMS mode)
        
        Returns:
            Dict with status and details
        """
        if self.mode == 'sms':
            return self._send_sms(message, phone_number)
        elif self.mode == 'push':
            return self._send_push_notification(message)
        elif self.mode == 'hybrid':
            return self._send_hybrid(message, phone_number)
        else:
            raise ValueError(f"Invalid communication mode: {self.mode}")
    
    def _send_sms(self, message: str, phone_number: str) -> Dict[str, Any]:
        """Send SMS via SignalWire"""
        if not self.signalwire_client:
            return {
                'success': False,
                'method': 'sms',
                'error': 'SignalWire client not initialized',
                'timestamp': datetime.now().isoformat()
            }
        
        if not phone_number:
            return {
                'success': False,
                'method': 'sms',
                'error': 'No phone number provided',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Send SMS via SignalWire
            sms = self.signalwire_client.messages.create(
                from_=self.config.SIGNALWIRE_PHONE_NUMBER,
                body=message,
                to=phone_number
            )
            
            print(f"📱 SMS sent via SignalWire: {sms.sid}")
            
            return {
                'success': True,
                'method': 'sms',
                'message_id': sms.sid,
                'timestamp': datetime.now().isoformat(),
                'to': phone_number,
                'from': self.config.SIGNALWIRE_PHONE_NUMBER
            }
            
        except Exception as e:
            print(f"❌ SMS failed: {e}")
            return {
                'success': False,
                'method': 'sms',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _send_push_notification(self, message: str) -> Dict[str, Any]:
        """Send push notification via Pushover"""
        try:
            # Send email to Pushover alias
            response = requests.post(
                'https://api.mailgun.net/v3/your-domain.com/messages',
                auth=('api', 'your-mailgun-key'),
                data={
                    'from': 'Alfred the Butler <alfred@your-domain.com>',
                    'to': self.config.PUSHOVER_EMAIL_ALIAS,
                    'subject': 'Alfred the Butler',
                    'text': message
                }
            )
            
            if response.status_code == 200:
                print(f"📱 Push notification sent via Pushover")
                return {
                    'success': True,
                    'method': 'push',
                    'timestamp': datetime.now().isoformat(),
                    'to': self.config.PUSHOVER_EMAIL_ALIAS
                }
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Push notification failed: {e}")
            return {
                'success': False,
                'method': 'push',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _send_hybrid(self, message: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Hybrid mode: Try SMS first, fallback to push notification
        
        Args:
            message: The message to send
            phone_number: Phone number to send SMS to
        """
        # Try SMS first if we have a phone number
        if phone_number and self.signalwire_client:
            sms_result = self._send_sms(message, phone_number)
            
            if sms_result['success']:
                return sms_result
            else:
                print(f"⚠️  SMS failed, falling back to push notification: {sms_result['error']}")
        
        # Fallback to push notification
        push_result = self._send_push_notification(message)
        
        # Add fallback info to result
        if 'fallback_from' not in push_result:
            push_result['fallback_from'] = 'sms'
            push_result['fallback_reason'] = 'SMS failed or no phone number provided'
        
        return push_result
    
    def get_status(self) -> Dict[str, Any]:
        """Get communication service status"""
        return {
            'mode': self.mode,
            'signalwire_available': self.signalwire_client is not None,
            'pushover_available': bool(self.config.PUSHOVER_EMAIL_ALIAS),
            'timestamp': datetime.now().isoformat()
        }
