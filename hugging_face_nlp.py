#!/usr/bin/env python3
"""
Intelligent NLP Processor using Hugging Face Transformers
"""

import re
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch
import numpy as np
from datetime import datetime, timedelta
import re
from spellchecker import SpellChecker

class IntelligentNLPProcessor:
    def __init__(self, food_db=None):
        """Initialize the intelligent NLP processor with custom data"""
        print("🧠 Initializing Intelligent NLP Processor...")
        
        # Load sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Sentence transformer model loaded")
        
        # Initialize spell checker
        self.spell_checker = SpellChecker()
        print("✅ Spell checker initialized")
        
        # Load custom common sayings
        self.common_sayings = self._load_common_sayings()
        
        # Load custom food database
        self.food_db = food_db or self._load_food_database()
        
        # Create intent examples from custom sayings
        self.intent_examples = self._create_intent_examples()
        
        # Pre-compute embeddings for all examples
        self.example_embeddings = self.model.encode(self.intent_examples)
        print("✅ Intent embeddings created")
        
        # Time parsing patterns
        self.time_patterns = {
            'morning': {'start': 9, 'end': 12},
            'afternoon': {'start': 12, 'end': 17},
            'evening': {'start': 17, 'end': 21},
            'night': {'start': 21, 'end': 23},
            'noon': {'start': 12, 'end': 13},
            'midnight': {'start': 0, 'end': 1}
        }
        
        print("🧠 Intelligent NLP Processor ready!")
    
    def _load_common_sayings(self):
        """Load custom common sayings from file"""
        try:
            with open('common_sayings.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️  common_sayings.json not found, using default examples")
            return self._get_default_intent_examples()
    
    def _load_food_database(self):
        """Load custom food database from file"""
        try:
            with open('custom_food_database.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️  custom_food_database.json not found, using default food DB")
            return {}
    
    def _get_default_intent_examples(self):
        """Fallback default intent examples if custom file not found"""
        return {
            "water_logging": ["drank water", "had water", "finished water bottle"],
            "food_logging": ["ate breakfast", "had lunch", "dinner time"],
            "gym_workout": ["hit the gym", "worked out", "lifted weights"],
            "calendar_event": ["meeting with", "appointment with", "lunch with"],
            "schedule_check": ["what's my schedule", "show my calendar"],
            "reminder_set": ["remind me to", "don't forget to"],
            "todo_add": ["add to todo", "add to list"],
            "photo_upload": ["add this photo to", "save this to"]
        }
    
    def _create_intent_examples(self):
        """Create flat list of examples from custom sayings"""
        examples = []
        for intent, phrases in self.common_sayings.items():
            examples.extend(phrases)
        return examples
    
    def clean_message(self, message: str) -> str:
        """Clean message by removing Google Voice metadata, formatting, and fixing common typos"""
        # Remove Google Voice metadata
        message = re.sub(r'<https://voice\.google\.com[^>]*>', '', message)
        message = re.sub(r'your account <https://[^>]*>', '', message)
        message = re.sub(r'google llc[^>]*usa', '', message)
        message = re.sub(r'\r\n', ' ', message)
        
        # Clean up extra whitespace
        message = re.sub(r'\s+', ' ', message)
        message = message.strip()
        
        # Fix common food-related typos
        message = self._fix_common_typos(message)
        
        # Spell check and correct
        message = self._spell_check_message(message)
        
        return message
    
    def _fix_common_typos(self, message: str) -> str:
        """Fix common typos that affect intent classification"""
        # Common food-related typos
        typos = {
            'are': 'ate',  # "are half a tub" -> "ate half a tub"
            'eated': 'ate',
            'eaten': 'ate',
            'drinked': 'drank',
            'drunk': 'drank',
            'hitted': 'hit',
            'hitted the': 'hit the',
            'workout out': 'worked out',
            'workouted': 'worked out',
            'meeting with': 'meeting with',  # Keep as is
            'appointment with': 'appointment with'  # Keep as is
        }
        
        message_lower = message.lower()
        for typo, correction in typos.items():
            if typo in message_lower:
                # Replace the typo with correction (case-insensitive)
                message = re.sub(rf'\b{typo}\b', correction, message, flags=re.IGNORECASE)
        
        return message
    
    def _spell_check_message(self, message: str) -> str:
        """Spell check and correct the message"""
        words = message.split()
        corrected_words = []
        
        for word in words:
            # Skip words with numbers or special characters
            if re.search(r'[0-9@#$%^&*()]', word):
                corrected_words.append(word)
                continue
            
            # Skip very short words
            if len(word) <= 2:
                corrected_words.append(word)
                continue
            
            # Check if word is misspelled
            if word.lower() not in self.spell_checker:
                # Get the most likely correction
                correction = self.spell_checker.correction(word)
                if correction and correction != word:
                    corrected_words.append(correction)
                    print(f"🔤 Spell corrected: '{word}' -> '{correction}'")
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def classify_intent(self, message: str) -> str:
        """Classify the intent of a message using semantic similarity"""
        # Clean the message first
        clean_message = self.clean_message(message)
        
        # Encode the message
        message_embedding = self.model.encode([clean_message])
        
        # Find the best matching intent
        best_intent = 'unknown'
        best_score = 0.0
        
        # Check each intent category
        for intent, phrases in self.common_sayings.items():
            # Encode all phrases for this intent
            intent_embeddings = self.model.encode(phrases)
            
            # Calculate cosine similarity
            similarities = cosine_similarity(message_embedding, intent_embeddings)
            max_similarity = np.max(similarities)
            
            if max_similarity > best_score:
                best_score = max_similarity
                best_intent = intent
        
        # If semantic similarity is too low, use fallback
        if best_score < 0.5:
            return self._fallback_classification(clean_message)
        
        return best_intent
    
    def _fallback_classification(self, message: str) -> str:
        """Enhanced fallback classification using keyword matching for edge cases"""
        message_lower = message.lower()
        
        # Priority-based classification for mixed intent messages
        # Check for calendar events first (highest priority)
        calendar_keywords = ['meeting', 'appointment', 'call', 'lunch', 'dinner', 'coffee', 'sync', 'standup', 'presentation', 'block out', 'schedule']
        if any(keyword in message_lower for keyword in calendar_keywords):
            # Special handling for mixed calendar + reminder messages
            if any(word in message_lower for word in ['remind', 'reminder', 'don\'t forget']):
                # If it's a calendar event with reminder, prioritize calendar
                return 'calendar_event'
            return 'calendar_event'
        
        # Check for gym workouts (high priority)
        gym_keywords = ['workout', 'gym', 'exercise', 'hit', 'bench', 'squat', 'deadlift', 'reps', 'sets', 'chest', 'back', 'legs', 'arms', 'shoulders']
        if any(keyword in message_lower for keyword in gym_keywords):
            return 'gym_workout'
        
        # Check for reminders
        reminder_keywords = ['remind', 'reminder', 'alarm', 'don\'t forget', 'set reminder', 'set alarm']
        if any(keyword in message_lower for keyword in reminder_keywords):
            return 'reminder_set'
        
        # Check for todos
        todo_keywords = ['todo', 'add to', 'need to', 'remember to', 'list']
        if any(keyword in message_lower for keyword in todo_keywords):
            return 'todo_add'
        
        # Check for food logging with better pattern matching
        food_patterns = [
            r'breakfast:\s*', r'lunch:\s*', r'dinner:\s*', r'snack:\s*', r'meal:\s*',
            r'ate\s+\w+', r'had\s+\w+', r'consumed\s+\w+', r'breakfast\s+', r'lunch\s+', r'dinner\s+'
        ]
        for pattern in food_patterns:
            if re.search(pattern, message_lower):
                return 'food_logging'
        
        # Check for water logging
        water_keywords = ['water', 'drank', 'hydrated', 'bottle', 'glass', 'hydrate']
        if any(keyword in message_lower for keyword in water_keywords):
            return 'water_logging'
        
        # Check for photo upload with better pattern matching
        photo_patterns = [
            r'add\s+(?:this\s+)?(?:photo|image|receipt|document)',
            r'save\s+(?:this\s+)?(?:photo|image|receipt|document)',
            r'upload\s+(?:this\s+)?(?:photo|image|receipt|document)',
            r'organize\s+(?:this\s+)?(?:photo|image|receipt|document)',
            r'store\s+(?:this\s+)?(?:photo|image|receipt|document)'
        ]
        for pattern in photo_patterns:
            if re.search(pattern, message_lower):
                return 'photo_upload'
        
        # Check for schedule queries with better pattern matching
        schedule_patterns = [
            r'what\s+(?:is|are)\s+(?:my\s+)?(?:schedule|calendar)',
            r'show\s+(?:me\s+)?(?:my\s+)?(?:schedule|calendar)',
            r'check\s+(?:my\s+)?(?:schedule|calendar)',
            r'am\s+I\s+(?:free|busy|available)',
            r'what\s+(?:meetings|appointments)\s+do\s+I\s+have'
        ]
        for pattern in schedule_patterns:
            if re.search(pattern, message_lower):
                return 'schedule_check'
        
        return 'unknown'
    
    def extract_entities(self, message: str) -> Dict:
        """Extract entities using intelligent parsing"""
        clean_message = self.clean_message(message)
        
        entities = {
            'people': self._extract_people(clean_message),
            'times': self._extract_times(clean_message),
            'dates': self._extract_dates(clean_message),
            'durations': self._extract_durations(clean_message),
            'locations': self._extract_locations(clean_message),
            'numbers': self._extract_numbers(clean_message),
            'exercises': self._extract_exercises(clean_message)
        }
        
        return entities
    
    def _extract_people(self, message: str) -> List[str]:
        """Extract people names using intelligent patterns"""
        people = []
        
        # Look for "with [name]" pattern
        with_pattern = r'with\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)'
        matches = re.finditer(with_pattern, message, re.IGNORECASE)
        
        for match in matches:
            name = match.group(1).strip()
            if len(name) > 1:  # Filter out single letters
                people.append(name)
        
        # Look for "meeting with [name]" pattern
        meeting_pattern = r'meeting\s+with\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)'
        matches = re.finditer(meeting_pattern, message, re.IGNORECASE)
        
        for match in matches:
            name = match.group(1).strip()
            if len(name) > 1 and name not in people:
                people.append(name)
        
        return people
    
    def _extract_times(self, message: str) -> List[Dict]:
        """Extract time expressions"""
        times = []
        
        # Pattern: 3pm, 2:30pm, 14:00
        time_patterns = [
            r'(\d{1,2}):?(\d{2})?\s*(am|pm)?',
            r'(\d{1,2})\s*(am|pm)',
            r'(\d{1,2})\s*oclock'
        ]
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                times.append({
                    'text': match.group(0),
                    'start': match.start(),
                    'end': match.end()
                })
        
        # Add time-of-day expressions
        for time_word in self.time_patterns.keys():
            if time_word in message.lower():
                times.append({
                    'text': time_word,
                    'start': message.lower().find(time_word),
                    'end': message.lower().find(time_word) + len(time_word)
                })
        
        return times
    
    def _extract_dates(self, message: str) -> List[Dict]:
        """Extract date expressions"""
        dates = []
        
        # Relative dates
        relative_patterns = {
            'today': 0,
            'tomorrow': 1,
            'tonight': 0,
            'this evening': 0,
            'this afternoon': 0,
            'this morning': 0
        }
        
        for date_word, days_offset in relative_patterns.items():
            if date_word in message.lower():
                dates.append({
                    'type': 'relative',
                    'value': date_word,
                    'days_offset': days_offset,
                    'start': message.lower().find(date_word),
                    'end': message.lower().find(date_word) + len(date_word)
                })
        
        # Day names
        day_pattern = r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
        matches = re.finditer(day_pattern, message, re.IGNORECASE)
        
        for match in matches:
            day_name = match.group(1)
            # Calculate days ahead
            now = datetime.now()
            target_day = self._get_next_day(day_name)
            days_ahead = (target_day - now.date()).days
            
            dates.append({
                'type': 'relative',
                'value': day_name,
                'days_offset': days_ahead,
                'start': match.start(),
                'end': match.end()
            })
        
        return dates
    
    def _extract_durations(self, message: str) -> List[Dict]:
        """Extract duration expressions"""
        durations = []
        
        # Time ranges like "3-4pm", "2-5pm"
        range_pattern = r'(\d{1,2})-(\d{1,2})\s*(am|pm)?'
        match = re.search(range_pattern, message, re.IGNORECASE)
        
        if match:
            start_hour = int(match.group(1))
            end_hour = int(match.group(2))
            ampm = match.group(3)
            
            # Handle AM/PM
            if ampm:
                if ampm.lower() == 'pm' and start_hour != 12:
                    start_hour += 12
                    end_hour += 12
                elif ampm.lower() == 'am' and start_hour == 12:
                    start_hour = 0
                    end_hour = 0
            
            # Calculate duration
            if end_hour < start_hour:  # Crosses midnight
                end_hour += 24
            
            duration_hours = end_hour - start_hour
            
            durations.append({
                'type': 'time_range',
                'start_hour': start_hour,
                'end_hour': end_hour,
                'duration_hours': duration_hours,
                'start': match.start(),
                'end': match.end()
            })
        
        return durations
    
    def _extract_locations(self, message: str) -> List[str]:
        """Extract location expressions"""
        locations = []
        
        # Look for "at [location]" pattern
        at_pattern = r'at\s+([^.!?]+?)(?:\s+(?:tomorrow|today|tonight|this|next|on|with|for))'
        matches = re.finditer(at_pattern, message, re.IGNORECASE)
        
        for match in matches:
            location = match.group(1).strip()
            if len(location) > 2:  # Filter out very short locations
                locations.append(location)
        
        return locations
    
    def _extract_numbers(self, message: str) -> List[Dict]:
        """Extract numbers from message"""
        numbers = []
        
        # Find all numbers
        number_pattern = r'\b(\d+\.?\d*)\b'
        matches = re.finditer(number_pattern, message)
        
        for match in matches:
            numbers.append({
                'value': match.group(1),
                'start': match.start(),
                'end': match.end()
            })
        
        return numbers
    
    def _extract_exercises(self, message: str) -> List[Dict]:
        """Extract gym exercises with weights and reps"""
        exercises = []
        
        # Pattern: exercise weight x reps (e.g., "bench 225x5")
        exercise_pattern = r'(\w+)\s+(\d+)(?:x|×)(\d+)'
        matches = re.finditer(exercise_pattern, message)
        
        for match in matches:
            exercise_name = match.group(1)
            weight = int(match.group(2))
            reps = int(match.group(3))
            
            exercises.append({
                'name': exercise_name,
                'weight': weight,
                'reps': reps,
                'sets': 1
            })
        
        return exercises
    
    def _get_next_day(self, day_name: str) -> datetime.date:
        """Get the next occurrence of a day of the week"""
        now = datetime.now()
        day_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_day = day_map[day_name.lower()]
        current_day = now.weekday()
        
        days_ahead = (target_day - current_day) % 7
        if days_ahead == 0:  # Same day, go to next week
            days_ahead = 7
        
        return now.date() + timedelta(days=days_ahead)
    
    def parse_calendar_event(self, message: str) -> Optional[Dict]:
        """Parse calendar event creation from message"""
        clean_message = self.clean_message(message)
        entities = self.extract_entities(clean_message)
        
        # Extract event details
        event_time = self._parse_event_time(clean_message, entities)
        duration = self._parse_event_duration(clean_message, entities)
        people = entities.get('people', [])
        location = entities.get('locations', [])
        event_type = self._extract_event_type(clean_message)
        
        if not event_time:
            return None
        
        # Default duration if not specified
        if not duration:
            duration = timedelta(hours=1)
        
        # Calculate end time
        end_time = event_time + duration
        
        return {
            'start_time': event_time,
            'end_time': end_time,
            'duration': duration,
            'people': people,
            'location': location[0] if location else None,
            'event_type': event_type,
            'description': f"Created from: {clean_message}",
            'title': self._generate_event_title(clean_message, people, event_type)
        }
    
    def _parse_event_time(self, message: str, entities: Dict) -> Optional[datetime]:
        """Parse event start time"""
        now = datetime.now()
        
        # Check for specific times
        times = entities.get('times', [])
        if times:
            # Use the first time found
            time_text = times[0]['text'].lower()
            
            # Handle specific times like "3pm"
            if ':' in time_text or any(word in time_text for word in ['am', 'pm', 'oclock']):
                return self._parse_specific_time(time_text)
            
            # Handle time of day
            for time_word, hour_range in self.time_patterns.items():
                if time_word in time_text:
                    target_time = now.replace(hour=hour_range['start'], minute=0, second=0, microsecond=0)
                    if target_time <= now:
                        target_time += timedelta(days=1)
                    return target_time
        
        # Check for relative dates
        dates = entities.get('dates', [])
        if dates:
            date_info = dates[0]
            if date_info['type'] == 'relative':
                target_date = now.date() + timedelta(days=date_info['days_offset'])
                # Default to 9 AM if no specific time
                return datetime.combine(target_date, datetime.min.time().replace(hour=9))
        
        return None
    
    def _parse_specific_time(self, time_text: str) -> Optional[datetime]:
        """Parse specific time like '3pm', '2:30pm'"""
        now = datetime.now()
        
        # Pattern: 3pm, 2:30pm, 14:00
        time_pattern = r'(\d{1,2}):?(\d{2})?\s*(am|pm)?'
        match = re.search(time_pattern, time_text, re.IGNORECASE)
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3)
            
            # Handle AM/PM
            if ampm:
                if ampm.lower() == 'pm' and hour != 12:
                    hour += 12
                elif ampm.lower() == 'am' and hour == 12:
                    hour = 0
            
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time has passed today, schedule for tomorrow
            if target_time <= now:
                target_time += timedelta(days=1)
            
            return target_time
        
        return None
    
    def _parse_event_duration(self, message: str, entities: Dict) -> Optional[timedelta]:
        """Parse event duration"""
        durations = entities.get('durations', [])
        
        if durations:
            duration_info = durations[0]
            if duration_info['type'] == 'time_range':
                return timedelta(hours=duration_info['duration_hours'])
        
        return None
    
    def _extract_event_type(self, message: str) -> str:
        """Extract event type from message"""
        message_lower = message.lower()
        
        event_types = {
            'meeting': ['meeting', 'mtg', 'sync'],
            'call': ['call', 'phone', 'zoom', 'video'],
            'appointment': ['appointment', 'apt', 'visit'],
            'lunch': ['lunch', 'dinner', 'breakfast', 'meal'],
            'workout': ['workout', 'gym', 'exercise', 'training']
        }
        
        for event_type, keywords in event_types.items():
            if any(keyword in message_lower for keyword in keywords):
                return event_type
        
        return 'event'
    
    def _generate_event_title(self, message: str, people: List[str], event_type: str) -> str:
        """Generate event title"""
        if people:
            if event_type == 'meeting':
                return f"Meeting with {', '.join(people)}"
            elif event_type == 'call':
                return f"Call with {', '.join(people)}"
            elif event_type == 'lunch':
                return f"Lunch with {', '.join(people)}"
            else:
                return f"{event_type.title()} with {', '.join(people)}"
        else:
            # Extract key words for title
            words = message.split()
            key_words = [word for word in words if len(word) > 3 and word.lower() not in ['with', 'for', 'the', 'and', 'but', 'this', 'that']]
            if key_words:
                return f"{event_type.title()}: {' '.join(key_words[:3])}"
            else:
                return f"{event_type.title()}"
    
    def parse_reminder(self, message: str) -> Optional[Dict]:
        """Parse reminder creation from message"""
        clean_message = self.clean_message(message)
        entities = self.extract_entities(clean_message)
        
        # Extract reminder text
        reminder_text = self._extract_reminder_text(clean_message)
        if not reminder_text:
            return None
        
        # Extract reminder time
        reminder_time = self._parse_event_time(clean_message, entities)
        if not reminder_time:
            return None
        
        return {
            'text': reminder_text,
            'scheduled_time': reminder_time,
            'created_at': datetime.now()
        }
    
    def _extract_reminder_text(self, message: str) -> Optional[str]:
        """Extract reminder text"""
        # Look for reminder triggers
        triggers = ['remind me to', 'reminder to', 'don\'t forget to', 'call', 'text', 'email']
        
        for trigger in triggers:
            if trigger in message.lower():
                start_idx = message.lower().find(trigger) + len(trigger)
                reminder_text = message[start_idx:].strip()
                
                # Clean up time references
                reminder_text = re.sub(r'\b(this evening|tonight|tomorrow|today)\b', '', reminder_text, flags=re.IGNORECASE)
                reminder_text = reminder_text.strip()
                
                if reminder_text:
                    return reminder_text
        
        return None

# Factory function
def create_intelligent_processor(food_database: Dict) -> IntelligentNLPProcessor:
    """Create an intelligent NLP processor"""
    return IntelligentNLPProcessor()
