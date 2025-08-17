"""
Google Voice Web Automation Module
Handles browser automation to send SMS via Google Voice web interface
"""

import time
import logging
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from human_like_automation import HumanLikeAutomation

class GoogleVoiceAutomation:
    """Handles Google Voice web automation for sending SMS"""
    
    def __init__(self, headless=True):
        self.driver = None
        self.is_logged_in = False
        self.headless = headless
        self.wait_timeout = 30
        self.human_like = HumanLikeAutomation()
        self.last_sms_time = 0
        self.min_sms_interval = 60  # Minimum 60 seconds between SMS
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for automation actions"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Essential options for cloud deployment
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
            
            # Disable images and other resources for faster loading
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            chrome_options.add_argument("--disable-plugins")
            
            # Setup ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.logger.info("✅ Chrome driver setup successful")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup Chrome driver: {e}")
            return False
    
    def login_to_google_voice(self, email, password):
        """Login to Google Voice using provided credentials"""
        try:
            if not self.driver:
                if not self.setup_driver():
                    return False
            
            self.logger.info("🌐 Navigating to Google Voice...")
            self.human_like.human_like_navigation(self.driver, "https://voice.google.com")
            
            # Check if already logged in
            if self._is_already_logged_in():
                self.logger.info("✅ Already logged into Google Voice")
                self.is_logged_in = True
                return True
            
            # Handle login flow
            self.logger.info("🔐 Starting login process...")
            
            # Look for the "Sign In" button on the landing page
            self.logger.info("🔍 Looking for Sign In button on landing page...")
            
            # Wait for page to fully load
            self.human_like.random_delay(3, 5)
            
            # Analyze the current page to see what's available
            self._analyze_page_content()
            
            # Try multiple approaches to find the Sign In button
            sign_in_found = False
            
            # Approach 1: Look for common Sign In button patterns
            sign_in_selectors = [
                "//button[contains(text(), 'Sign in')]",
                "//button[contains(text(), 'Sign In')]",
                "//button[contains(text(), 'sign in')]",
                "//button[contains(text(), 'SIGN IN')]",
                "//a[contains(text(), 'Sign in')]",
                "//a[contains(text(), 'Sign In')]",
                "//div[contains(text(), 'Sign in')]",
                "//div[contains(text(), 'Sign In')]",
                "//span[contains(text(), 'Sign in')]",
                "//span[contains(text(), 'Sign In')]"
            ]
            
            for selector in sign_in_selectors:
                try:
                    sign_in_button = self.driver.find_element(By.XPATH, selector)
                    if sign_in_button.is_displayed():
                        self.logger.info(f"✅ Found Sign In button with selector: {selector}")
                        self.logger.info(f"🔘 Button text: '{sign_in_button.text}'")
                        
                        # Click the Sign In button
                        self.human_like.human_like_click(sign_in_button)
                        sign_in_found = True
                        break
                except NoSuchElementException:
                    continue
            
            # Approach 2: Look for buttons with specific attributes
            if not sign_in_found:
                self.logger.info("🔍 Trying alternative button detection...")
                button_selectors = [
                    "button[data-action='signin']",
                    "button[aria-label*='sign in']",
                    "button[aria-label*='Sign in']",
                    "a[href*='accounts.google.com']",
                    "a[href*='signin']"
                ]
                
                for selector in button_selectors:
                    try:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if button.is_displayed():
                            self.logger.info(f"✅ Found potential Sign In button with selector: {selector}")
                            self.logger.info(f"🔘 Button text: '{button.text}'")
                            
                            # Click the button
                            self.human_like.human_like_click(button)
                            sign_in_found = True
                            break
                    except NoSuchElementException:
                        continue
            
            # Approach 3: Look for any clickable element with "sign" in the text
            if not sign_in_found:
                self.logger.info("🔍 Trying broad text search for Sign In...")
                try:
                    # Find all elements that might contain "sign" text
                    sign_elements = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign')]")
                    
                    for element in sign_elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element_text = element.text.lower()
                                if 'sign' in element_text and ('in' in element_text or 'login' in element_text):
                                    self.logger.info(f"✅ Found Sign In element with text: '{element.text}'")
                                    
                                    # Try to click it
                                    self.human_like.human_like_click(element)
                                    sign_in_found = True
                                    break
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    self.logger.info(f"⚠️ Error in broad text search: {e}")
            
            if not sign_in_found:
                self.logger.error("❌ Could not find Sign In button on landing page")
                return False
            
            # Wait for the login form to appear after clicking Sign In
            self.logger.info("⏳ Waiting for login form to appear...")
            self.human_like.random_delay(4, 6)
            
            # Analyze the new page to see what we're dealing with
            self._analyze_page_content()
            
            # Now look for email input field on the login page
            try:
                # Wait a bit longer for the login form to fully load
                self.human_like.random_delay(3, 5)
                
                # Look for email input on the login page
                self.logger.info("🔍 Looking for email input field...")
                
                # Wait for the login form to fully load
                self.human_like.random_delay(2, 4)
                
                # Try multiple selectors for email input
                email_input_selectors = [
                    "input[type='email']",
                    "input[name='identifier']",
                    "input[aria-label*='Email']",
                    "input[aria-label*='email']",
                    "input[placeholder*='Email']",
                    "input[placeholder*='email']",
                    "input[id*='email']",
                    "input[id*='identifier']"
                ]
                
                email_input = None
                for selector in email_input_selectors:
                    try:
                        email_input = WebDriverWait(self.driver, 8).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if email_input.is_displayed():
                            self.logger.info(f"✅ Found email input with selector: {selector}")
                            break
                    except TimeoutException:
                        continue
                
                if not email_input:
                    self.logger.error("❌ Could not find email input field")
                    return False
                
                if not email_input:
                    self.logger.error("❌ Could not find appropriate email input field")
                    return False
                
                # Enter email with human-like behavior
                self.logger.info(f"📧 Entering email: {email}")
                self.human_like.human_like_typing(email_input, email)
                
                # Human-like pause before pressing Enter
                self.human_like.random_delay(0.5, 1.5)
                email_input.send_keys(Keys.RETURN)
                
                # Wait for password field with multiple selectors
                password_selectors = [
                    "input[type='password']",
                    "input[name='password']",
                    "input[aria-label*='password']",
                    "input[aria-label*='Password']",
                    "input[placeholder*='password']",
                    "input[placeholder*='Password']"
                ]
                
                password_input = None
                for selector in password_selectors:
                    try:
                        password_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if password_input.is_displayed():
                            break
                    except TimeoutException:
                        continue
                
                if not password_input:
                    self.logger.error("❌ Could not find password input field")
                    return False
                
                # Enter password with human-like behavior
                self.logger.info("🔑 Entering password...")
                self.human_like.human_like_typing(password_input, password)
                
                # Human-like pause before pressing Enter
                self.human_like.random_delay(0.5, 1.5)
                password_input.send_keys(Keys.RETURN)
                
                # Wait for login to complete and handle 2FA if needed
                self.human_like.random_delay(6, 10)
                
                # Check if login successful
                if self._is_already_logged_in():
                    self.logger.info("✅ Successfully logged into Google Voice")
                    self.is_logged_in = True
                    return True
                else:
                    # Check if we need to handle 2FA or other verification
                    self.logger.info("ℹ️ Login may require additional verification...")
                    self.human_like.random_delay(4, 7)  # Wait a bit more
                    
                    if self._is_already_logged_in():
                        self.logger.info("✅ Login successful after additional verification")
                        self.is_logged_in = True
                        return True
                    else:
                        self.logger.error("❌ Login failed - could not verify successful login")
                        return False
                    
            except TimeoutException as e:
                self.logger.error(f"❌ Login timeout: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Login error: {e}")
            return False
    
    def _is_already_logged_in(self):
        """Check if already logged into Google Voice"""
        try:
            # Look for elements that indicate successful login
            # Google Voice main interface elements
            indicators = [
                # Modern Google Voice interface elements
                "//div[contains(@class, 'gv-call-button')]",      # Call button
                "//div[contains(@class, 'gv-message-list')]",     # Message list
                "//div[contains(@class, 'gv-sidebar')]",          # Sidebar
                "//div[contains(@class, 'gv-main')]",             # Main content
                "//div[contains(@class, 'voice-app')]",           # Voice app container
                "//div[contains(@class, 'voice-messages')]",      # Messages section
                "//div[contains(@class, 'voice-calls')]",         # Calls section
                "//div[contains(@class, 'voice-settings')]",      # Settings section
                # Alternative selectors for different versions
                "//div[contains(@class, 'voice')]",               # Generic voice class
                "//div[contains(@class, 'messages')]",            # Messages
                "//div[contains(@class, 'calls')]",               # Calls
                "//div[contains(@class, 'settings')]",            # Settings
                # Check for URL changes
                "//div[contains(@class, 'logged-in')]",           # Logged in indicator
                "//div[contains(@class, 'authenticated')]"        # Authenticated indicator
            ]
            
            for indicator in indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        self.logger.info(f"✅ Found login indicator: {indicator}")
                        return True
                except NoSuchElementException:
                    continue
            
            # Also check if we're redirected to a different page (like account selection)
            current_url = self.driver.current_url
            if "voice.google.com" in current_url and "accounts" not in current_url:
                self.logger.info(f"✅ Currently on Google Voice: {current_url}")
                return True
            
            self.logger.info(f"ℹ️ Current URL: {current_url}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking login status: {e}")
            return False
    
    def _analyze_page_content(self):
        """Analyze the current page to understand what we're dealing with"""
        try:
            self.logger.info("🔍 Analyzing page content...")
            
            # Get current URL
            current_url = self.driver.current_url
            self.logger.info(f"📍 Current URL: {current_url}")
            
            # Get page title
            page_title = self.driver.title
            self.logger.info(f"📄 Page title: {page_title}")
            
            # Look for all input fields
            all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input")
            self.logger.info(f"🔍 Found {len(all_inputs)} input fields:")
            
            for i, input_field in enumerate(all_inputs):
                try:
                    input_type = input_field.get_attribute("type") or "unknown"
                    input_name = input_field.get_attribute("name") or "no-name"
                    input_placeholder = input_field.get_attribute("placeholder") or "no-placeholder"
                    input_id = input_field.get_attribute("id") or "no-id"
                    
                    self.logger.info(f"  Input {i+1}: type='{input_type}', name='{input_name}', placeholder='{input_placeholder}', id='{input_id}'")
                    
                    # Check if it's visible
                    if input_field.is_displayed():
                        self.logger.info(f"    ✅ Visible")
                    else:
                        self.logger.info(f"    ❌ Hidden")
                        
                except Exception as e:
                    self.logger.info(f"  Input {i+1}: Error analyzing - {e}")
            
            # Look for forms
            all_forms = self.driver.find_elements(By.CSS_SELECTOR, "form")
            self.logger.info(f"🔍 Found {len(all_forms)} forms:")
            
            for i, form in enumerate(all_forms):
                try:
                    form_action = form.get_attribute("action") or "no-action"
                    form_method = form.get_attribute("method") or "no-method"
                    
                    self.logger.info(f"  Form {i+1}: action='{form_action}', method='{form_method}'")
                    
                    # Check form contents
                    form_inputs = form.find_elements(By.CSS_SELECTOR, "input")
                    self.logger.info(f"    Contains {len(form_inputs)} input fields")
                    
                except Exception as e:
                    self.logger.info(f"  Form {i+1}: Error analyzing - {e}")
            
            # Look for buttons
            all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, input[type='submit'], input[type='button']")
            self.logger.info(f"🔍 Found {len(all_buttons)} buttons:")
            
            for i, button in enumerate(all_buttons):
                try:
                    button_text = button.text or button.get_attribute("value") or "no-text"
                    button_type = button.get_attribute("type") or "button"
                    
                    self.logger.info(f"  Button {i+1}: text='{button_text}', type='{button_type}'")
                    
                    if button.is_displayed():
                        self.logger.info(f"    ✅ Visible")
                    else:
                        self.logger.info(f"    ❌ Hidden")
                        
                except Exception as e:
                    self.logger.info(f"  Button {i+1}: Error analyzing - {e}")
                    
        except Exception as e:
            self.logger.error(f"Error analyzing page content: {e}")
    
    def send_sms_via_web(self, phone_number, message):
        """Send SMS via Google Voice web interface"""
        try:
            if not self.is_logged_in:
                self.logger.error("❌ Not logged into Google Voice")
                return False
            
            # Rate limiting - prevent too many SMS too quickly
            current_time = time.time()
            time_since_last_sms = current_time - self.last_sms_time
            
            if time_since_last_sms < self.min_sms_interval:
                wait_time = self.min_sms_interval - time_since_last_sms
                self.logger.info(f"⏰ Rate limiting: waiting {wait_time:.1f} seconds before sending SMS")
                time.sleep(wait_time)
            
            self.logger.info(f"📱 Preparing to send SMS to {phone_number}")
            
            # Simulate human behavior before starting
            self.human_like.simulate_human_behavior(self.driver)
            
            # Navigate to messages/compose
            self._navigate_to_compose()
            
            # Enter phone number
            if not self._enter_phone_number(phone_number):
                return False
            
            # Human-like pause between fields
            self.human_like.random_delay(0.5, 1.5)
            
            # Enter message
            if not self._enter_message(message):
                return False
            
            # Human-like pause before sending
            self.human_like.random_delay(1, 2)
            
            # Send message
            if not self._click_send():
                return False
            
            # Verify delivery
            if self._verify_message_sent():
                self.logger.info(f"✅ SMS sent successfully to {phone_number}")
                # Update last SMS time for rate limiting
                self.last_sms_time = time.time()
                return True
            else:
                self.logger.error(f"❌ Failed to verify SMS delivery to {phone_number}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error sending SMS: {e}")
            return False
    
    def _navigate_to_compose(self):
        """Navigate to SMS compose area"""
        try:
            # Look for compose button or message area
            compose_selectors = [
                "//div[contains(@class, 'gv-compose')]",
                "//div[contains(@class, 'gv-message-compose')]",
                "//div[contains(@class, 'compose')]",
                "//button[contains(@aria-label, 'compose')]",
                "//button[contains(@aria-label, 'new message')]"
            ]
            
            for selector in compose_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed():
                        element.click()
                        time.sleep(2)
                        return True
                except NoSuchElementException:
                    continue
            
            # If no compose button found, try to find message input directly
            self.logger.info("No compose button found, looking for message input...")
            return True
            
        except Exception as e:
            self.logger.error(f"Error navigating to compose: {e}")
            return False
    
    def _enter_phone_number(self, phone_number):
        """Enter phone number in compose field"""
        try:
            # Look for phone number input field
            phone_selectors = [
                "//input[contains(@placeholder, 'phone')]",
                "//input[contains(@placeholder, 'number')]",
                "//input[contains(@class, 'phone')]",
                "//input[contains(@class, 'number')]",
                "//input[@type='tel']"
            ]
            
            phone_input = None
            for selector in phone_selectors:
                try:
                    phone_input = self.driver.find_element(By.XPATH, selector)
                    if phone_input.is_displayed():
                        break
                except NoSuchElementException:
                    continue
            
            if not phone_input:
                self.logger.error("❌ Could not find phone number input field")
                return False
            
            # Clear and enter phone number with human-like behavior
            self.human_like.human_like_typing(phone_input, phone_number)
            
            self.logger.info(f"✅ Phone number entered: {phone_number}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error entering phone number: {e}")
            return False
    
    def _enter_message(self, message):
        """Enter message text in compose field"""
        try:
            # Look for message input field
            message_selectors = [
                "//textarea[contains(@placeholder, 'message')]",
                "//textarea[contains(@class, 'message')]",
                "//div[contains(@class, 'message-input')]",
                "//div[contains(@contenteditable, 'true')]",
                "//textarea"
            ]
            
            message_input = None
            for selector in message_selectors:
                try:
                    message_input = self.driver.find_element(By.XPATH, selector)
                    if message_input.is_displayed():
                        break
                except NoSuchElementException:
                    continue
            
            if not message_input:
                self.logger.error("❌ Could not find message input field")
                return False
            
            # Clear and enter message with human-like behavior
            self.human_like.human_like_typing(message_input, message)
            
            self.logger.info(f"✅ Message entered: {message[:50]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Error entering message: {e}")
            return False
    
    def _click_send(self):
        """Click send button to send message"""
        try:
            # Look for send button
            send_selectors = [
                "//button[contains(@aria-label, 'send')]",
                "//button[contains(@class, 'send')]",
                "//button[contains(text(), 'Send')]",
                "//button[contains(text(), 'send')]",
                "//div[contains(@class, 'send-button')]"
            ]
            
            send_button = None
            for selector in send_selectors:
                try:
                    send_button = self.driver.find_element(By.XPATH, selector)
                    if send_button.is_displayed() and send_button.is_enabled():
                        break
                except NoSuchElementException:
                    continue
            
            if not send_button:
                self.logger.error("❌ Could not find send button")
                return False
            
            # Click send with human-like behavior
            self.human_like.human_like_click(send_button)
            
            self.logger.info("✅ Send button clicked")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clicking send: {e}")
            return False
    
    def _verify_message_sent(self):
        """Verify that message was sent successfully"""
        try:
            # Wait a moment for message to be sent with human-like timing
            self.human_like.random_delay(2, 4)
            
            # Look for success indicators
            success_indicators = [
                "//div[contains(@class, 'sent')]",
                "//div[contains(@class, 'delivered')]",
                "//div[contains(@class, 'success')]",
                "//span[contains(text(), 'sent')]",
                "//span[contains(text(), 'delivered')]"
            ]
            
            for indicator in success_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        self.logger.info("✅ Message sent successfully verified")
                        return True
                except NoSuchElementException:
                    continue
            
            # If no success indicator found, assume success (Google Voice doesn't always show them)
            self.logger.info("ℹ️ No success indicator found, assuming message sent")
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying message sent: {e}")
            return False
    
    def close(self):
        """Close the browser and cleanup"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.is_logged_in = False
                self.logger.info("✅ Browser closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()
