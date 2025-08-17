"""
Human-Like Automation Behavior Module
Adds realistic delays and human-like interactions to reduce detection risk
"""

import time
import random
from typing import List, Optional

class HumanLikeAutomation:
    """Provides human-like behavior for web automation"""
    
    def __init__(self):
        self.min_delay = 0.5
        self.max_delay = 3.0
        
    def random_delay(self, min_seconds: float = None, max_seconds: float = None) -> None:
        """Add a random delay to mimic human thinking time"""
        min_delay = min_seconds or self.min_delay
        max_delay = max_seconds or self.max_delay
        
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def human_like_typing(self, element, text: str, min_char_delay: float = 0.05, max_char_delay: float = 0.2) -> None:
        """Type text with human-like timing between characters"""
        # Clear the field first
        element.clear()
        time.sleep(random.uniform(0.3, 0.8))
        
        # Type each character with random delays
        for char in text:
            element.send_keys(char)
            # Random delay between characters (like human typing)
            char_delay = random.uniform(min_char_delay, max_char_delay)
            time.sleep(char_delay)
        
        # Small pause after typing (like human reviewing)
        time.sleep(random.uniform(0.5, 1.5))
    
    def human_like_click(self, element) -> None:
        """Click an element with human-like timing"""
        # Hover-like behavior (small delay before click)
        time.sleep(random.uniform(0.2, 0.8))
        
        # Click the element
        element.click()
        
        # Post-click delay (like human waiting for response)
        time.sleep(random.uniform(0.5, 1.5))
    
    def human_like_navigation(self, driver, url: str) -> None:
        """Navigate to URL with human-like behavior"""
        # Small delay before navigation
        time.sleep(random.uniform(0.5, 1.5))
        
        # Navigate to URL
        driver.get(url)
        
        # Wait for page load with random timing
        load_delay = random.uniform(3, 6)
        time.sleep(load_delay)
    
    def human_like_scroll(self, driver, direction: str = "down", distance: int = None) -> None:
        """Scroll with human-like behavior"""
        if direction == "down":
            scroll_amount = distance or random.randint(300, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        elif direction == "up":
            scroll_amount = distance or random.randint(200, 500)
            driver.execute_script(f"window.scrollBy(0, -{scroll_amount});")
        
        # Human-like pause after scrolling
        time.sleep(random.uniform(0.5, 1.5))
    
    def human_like_form_fill(self, elements: List, values: List) -> None:
        """Fill multiple form fields with human-like behavior"""
        for element, value in zip(elements, values):
            # Focus on element
            element.click()
            time.sleep(random.uniform(0.3, 0.8))
            
            # Type the value
            self.human_like_typing(element, value)
            
            # Move to next field with natural delay
            time.sleep(random.uniform(0.5, 1.2))
    
    def human_like_wait_for_element(self, driver, by, value, timeout: int = 10) -> Optional[object]:
        """Wait for element with human-like patience"""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        try:
            # Add small random delay before looking for element
            time.sleep(random.uniform(0.5, 1.5))
            
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            
            # Small delay after finding element
            time.sleep(random.uniform(0.3, 0.8))
            
            return element
            
        except Exception:
            return None
    
    def human_like_page_interaction(self, driver) -> None:
        """Simulate natural page interaction to appear more human"""
        # Random mouse movements (simulated)
        time.sleep(random.uniform(1, 3))
        
        # Small scroll action
        if random.random() < 0.3:  # 30% chance
            self.human_like_scroll(driver, "down", random.randint(100, 300))
        
        # Wait like a human would
        time.sleep(random.uniform(2, 4))
    
    def get_realistic_delay(self, action_type: str) -> float:
        """Get realistic delay based on action type"""
        delays = {
            "typing": random.uniform(0.05, 0.2),
            "clicking": random.uniform(0.2, 0.8),
            "navigation": random.uniform(3, 6),
            "form_fill": random.uniform(0.5, 1.2),
            "thinking": random.uniform(1, 3),
            "reading": random.uniform(2, 5)
        }
        
        return delays.get(action_type, random.uniform(1, 3))
    
    def simulate_human_behavior(self, driver) -> None:
        """Simulate various human behaviors to appear more natural"""
        # Random page interaction
        if random.random() < 0.4:  # 40% chance
            self.human_like_page_interaction(driver)
        
        # Random thinking time
        if random.random() < 0.6:  # 60% chance
            thinking_time = random.uniform(1, 4)
            time.sleep(thinking_time)
        
        # Small random movements
        if random.random() < 0.2:  # 20% chance
            time.sleep(random.uniform(0.5, 1.5))
