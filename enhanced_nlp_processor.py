import spacy
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import dateutil.parser
from dateutil.relativedelta import relativedelta

# Load spaCy model (free)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Please install spaCy English model: python -m spacy download en_core_web_sm")
    nlp = None

class EnhancedNLPProcessor:
    def __init__(self):
        self.food_db = {}  # Will be loaded from JSON
        
        # Enhanced intent patterns with more sophisticated matching
        self.intent_patterns = {
            'water': [
                r'\b(drank|drink|had|finished|bottle|water|oz|ml)\b',
                r'\b(thirsty|hydrat|sip)\b'
            ],
            'food': [
                r'\b(ate|eat|had|lunch|dinner|breakfast|snack|meal)\b',
                r'\b(hungry|food|calories|macros)\b'
            ],
            'gym': [
                r'\b(gym|workout|exercise|lift|hit|chest|back|legs|arms|shoulders)\b',
                r'\b(bench|squat|deadlift|cardio|weights|reps?|sets?)\b'
            ],
            'todo': [
                r'\b(todo|task|add|remember|need to|don\'t forget)\b',
                r'\b(list|remind me to)\b'
            ],
            'reminder': [
                r'\b(remind me|reminder|don\'t forget|schedule)\b',
                r'\b(later|tomorrow|tonight|evening|morning|call|text)\b'
            ],
            'completion': [
                r'\b(did|done|finished|completed|called|went|bought)\b',
                r'\b(check off|mark complete|crossed off)\b'
            ],
            'calendar': [
                r'\b(schedule|calendar|meeting|appointment|free|busy)\b',
                r'\b(today|tomorrow|next week|what\'s next)\b'
            ],
            'create_event': [
                r'\b(block out|schedule|book|set up|create|add)\b',
                r'\b(meeting|appointment|call|visit|lunch|dinner)\b'
            ],
            'check_schedule': [
                r'\b(what\'s|what is|show|list|check|how)\b',
                r'\b(schedule|calendar|today|tomorrow|this week|free|busy)\b'
            ],
            'image': [
                r'\b(save|upload|store|organize|photo|picture|image)\b',
                r'\b(receipt|document|scan|backup|add this)\b'
            ],
            'drive': [
                r'\b(drive|folder|organize|file|document)\b',
                r'\b(work|personal|receipts|photos|to [a-z]+)\b'
            ]
        }
        
        # Enhanced time expressions with more granular parsing
        self.time_patterns = {
            'morning': {'start': 9, 'end': 12},
            'afternoon': {'start': 12, 'end': 17},
            'evening': {'start': 17, 'end': 21},
            'night': {'start': 21, 'end': 23},
            'lunch': {'start': 12, 'end': 13},
            'dinner': {'start': 18, 'end': 20},
            'breakfast': {'start': 7, 'end': 9}
        }
        
        # Calendar-specific patterns
        self.calendar_patterns = {
            'create_event': [
                r'\b(meeting|appointment|call|visit|lunch|dinner)\b',
                r'\b(with|to|at|from|for)\b'
            ],
            'check_schedule': [
                r'\b(what\'s|what is|show|list|check|how)\b',
                r'\b(schedule|calendar|today|tomorrow|this week)\b'
            ],
            'modify_event': [
                r'\b(move|reschedule|change|update|edit)\b',
                r'\b(meeting|appointment|event)\b'
            ]
        }
        
        # Gym exercise patterns
        self.gym_patterns = {
            'chest': ['bench', 'incline', 'decline', 'fly', 'press', 'dumbbell'],
            'back': ['pullup', 'row', 'deadlift', 'lat pulldown', 'shrug'],
            'legs': ['squat', 'deadlift', 'leg press', 'lunge', 'calf raise'],
            'arms': ['curl', 'tricep', 'bicep', 'hammer', 'skull crusher'],
            'shoulders': ['press', 'lateral raise', 'rear delt', 'shrug']
        }
    
    def classify_intent(self, message: str) -> List[str]:
        """Classify message intent using pattern matching"""
        message_lower = message.lower()
        intents = []
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    intents.append(intent)
                    break
        
        # Special handling for calendar intents
        if 'calendar' in intents:
            calendar_subintent = self._classify_calendar_intent(message)
            if calendar_subintent:
                intents.append(calendar_subintent)
        
        return intents or ['unknown']
    
    def _classify_calendar_intent(self, message: str) -> Optional[str]:
        """Classify specific calendar intent"""
        message_lower = message.lower()
        
        for intent, patterns in self.calendar_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        return None
    
    def extract_entities(self, message: str) -> Dict:
        """Extract entities using spaCy + custom rules"""
        if not nlp:
            return self._fallback_extraction(message)
        
        doc = nlp(message)
        entities = {
            'numbers': [],
            'times': [],
            'foods': [],
            'quantities': [],
            'tasks': [],
            'people': [],
            'locations': [],
            'dates': [],
            'durations': []
        }
        
        # Extract numbers and quantities
        for token in doc:
            if token.like_num:
                entities['numbers'].append({
                    'value': token.text,
                    'position': token.idx
                })
            
            # Check for units
            if token.text.lower() in ['oz', 'ml', 'cups', 'glasses', 'bottles']:
                entities['quantities'].append({
                    'unit': token.text.lower(),
                    'position': token.idx
                })
        
        # Extract time expressions
        for ent in doc.ents:
            if ent.label_ in ['TIME', 'DATE']:
                entities['times'].append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
            elif ent.label_ == 'PERSON':
                entities['people'].append({
                    'name': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
            elif ent.label_ == 'GPE':
                entities['locations'].append({
                    'name': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
        
        # Extract potential food names
        entities['foods'] = self._extract_foods(message)
        
        # Extract tasks (everything after trigger words)
        entities['tasks'] = self._extract_tasks(message)
        
        # Extract dates and durations
        entities['dates'] = self._extract_dates(message)
        entities['durations'] = self._extract_durations(message)
        
        return entities
    
    def _fallback_extraction(self, message: str) -> Dict:
        """Fallback extraction without spaCy"""
        entities = {
            'numbers': [],
            'times': [],
            'foods': [],
            'quantities': [],
            'tasks': [],
            'people': [],
            'locations': [],
            'dates': [],
            'durations': []
        }
        
        # Extract numbers
        numbers = re.findall(r'\b\d+\.?\d*\b', message)
        entities['numbers'] = [{'value': num, 'position': 0} for num in numbers]
        
        # Extract units
        units = re.findall(r'\b(oz|ml|cups?|glasses?|bottles?)\b', message.lower())
        entities['quantities'] = [{'unit': unit, 'position': 0} for unit in units]
        
        # Extract foods and tasks
        entities['foods'] = self._extract_foods(message)
        entities['tasks'] = self._extract_tasks(message)
        entities['dates'] = self._extract_dates(message)
        entities['durations'] = self._extract_durations(message)
        
        return entities
    
    def _extract_foods(self, message: str) -> List[str]:
        """Extract food names from message"""
        foods = []
        message_lower = message.lower()
        
        # Check against food database
        for food_key, food_data in self.food_db.items():
            names_to_check = [food_key.replace('_', ' ')] + food_data.get('aliases', [])
            for name in names_to_check:
                if name.lower() in message_lower:
                    foods.append(food_data['display_name'])
                    break
        
        # If no known foods found, try to extract unknown foods
        if not foods:
            # Look for words after "ate", "had", etc.
            food_triggers = r'\b(ate|had|eat|lunch|dinner|breakfast)\s+([^.!?]+)'
            matches = re.findall(food_triggers, message_lower)
            for trigger, potential_food in matches:
                # Clean up the extracted text
                clean_food = re.sub(r'\b(a|an|the|some|my)\b', '', potential_food).strip()
                if clean_food:
                    foods.append(clean_food)
        
        return foods
    
    def _extract_tasks(self, message: str) -> List[str]:
        """Extract tasks from message"""
        tasks = []
        
        # Task trigger patterns
        patterns = [
            r'todo:?\s*(.+)',
            r'remember to\s+(.+)',
            r'need to\s+(.+)',
            r'don\'t forget\s+(.+)',
            r'remind me to\s+(.+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            tasks.extend(matches)
        
        return [task.strip() for task in tasks]
    
    def _extract_dates(self, message: str) -> List[Dict]:
        """Extract date references from message"""
        dates = []
        message_lower = message.lower()
        
        # Relative date patterns
        relative_patterns = {
            'today': 0,
            'tomorrow': 1,
            'next week': 7,
            'this weekend': 5,
            'next monday': 'next_monday',
            'next tuesday': 'next_tuesday',
            'next wednesday': 'next_wednesday',
            'next thursday': 'next_thursday',
            'next friday': 'next_friday',
            'next saturday': 'next_saturday',
            'next sunday': 'next_sunday'
        }
        
        for pattern, days in relative_patterns.items():
            if pattern in message_lower:
                dates.append({
                    'type': 'relative',
                    'value': pattern,
                    'days_offset': days
                })
        
        # Specific date patterns (MM/DD, MM-DD, etc.)
        date_patterns = [
            r'\b(\d{1,2})[/-](\d{1,2})\b',
            r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, message)
            for match in matches:
                if len(match) == 2:
                    dates.append({
                        'type': 'month_day',
                        'month': int(match[0]),
                        'day': int(match[1])
                    })
                elif len(match) == 3:
                    dates.append({
                        'type': 'full_date',
                        'month': int(match[0]),
                        'day': int(match[1]),
                        'year': int(match[2])
                    })
        
        return dates
    
    def _extract_durations(self, message: str) -> List[Dict]:
        """Extract duration references from message"""
        durations = []
        message_lower = message.lower()
        
        # Duration patterns
        duration_patterns = [
            (r'(\d+)\s*hours?', 'hours'),
            (r'(\d+)\s*hrs?', 'hours'),
            (r'(\d+)\s*minutes?', 'minutes'),
            (r'(\d+)\s*mins?', 'minutes'),
            (r'(\d+)\s*days?', 'days'),
            (r'(\d+)\s*weeks?', 'weeks')
        ]
        
        for pattern, unit in duration_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                durations.append({
                    'value': int(match),
                    'unit': unit
                })
        
        return durations
    
    def parse_calendar_event(self, message: str) -> Optional[Dict]:
        """Parse calendar event creation from message"""
        entities = self.extract_entities(message)
        
        # Extract event details
        event_time = self.parse_time_reference(message)
        duration = self.parse_duration(message)
        people = self._extract_event_people(message, entities)
        location = self._extract_event_location(message, entities)
        event_type = self._extract_event_type(message)
        description = self._build_event_description(message, entities)
        
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
            'location': location,
            'event_type': event_type,
            'description': description,
            'title': self._generate_event_title(message, people, event_type)
        }
    
    def _extract_event_type(self, message: str) -> str:
        """Extract the type of event from message"""
        message_lower = message.lower()
        
        event_types = {
            'meeting': ['meeting', 'mtg', 'sync'],
            'call': ['call', 'phone', 'zoom', 'video'],
            'appointment': ['appointment', 'apt', 'visit'],
            'lunch': ['lunch', 'dinner', 'breakfast', 'meal'],
            'workout': ['workout', 'gym', 'exercise', 'training'],
            'social': ['coffee', 'drinks', 'hangout', 'get together']
        }
        
        for event_type, keywords in event_types.items():
            if any(keyword in message_lower for keyword in keywords):
                return event_type
        
        return 'event'
    
    def _generate_event_title(self, message: str, people: List[str], event_type: str) -> str:
        """Generate a meaningful event title"""
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
            # Extract key words from message for title
            words = message.split()
            key_words = [word for word in words if len(word) > 3 and word.lower() not in ['with', 'for', 'the', 'and', 'but', 'this', 'that']]
            if key_words:
                return f"{event_type.title()}: {' '.join(key_words[:3])}"
            else:
                return f"{event_type.title()}"
    
    def parse_schedule_query(self, message: str) -> Optional[Dict]:
        """Parse schedule checking queries"""
        message_lower = message.lower()
        
        # Extract date/time to check
        query_time = self.parse_time_reference(message)
        if not query_time:
            # Default to today if no specific time mentioned
            query_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Determine query type
        if any(word in message_lower for word in ['free', 'available', 'open']):
            query_type = 'free_time'
        elif any(word in message_lower for word in ['busy', 'booked', 'scheduled']):
            query_type = 'busy_time'
        else:
            query_type = 'full_schedule'
        
        return {
            'query_time': query_time,
            'query_type': query_type,
            'date': query_time.date()
        }
    
    def parse_water_amount(self, message: str, entities: Dict) -> Optional[int]:
        """Parse water amount from message"""
        message_lower = message.lower()
        
        # Handle bottle references
        if 'bottle' in message_lower:
            if 'half' in message_lower:
                return 355  # 12oz
            elif any(word in message_lower for word in ['two', '2', 'couple']):
                return 1420  # 48oz
            else:
                return 710  # 24oz (your default)
        
        # Handle explicit amounts
        numbers = [float(n['value']) for n in entities['numbers']]
        quantities = [q['unit'] for q in entities['quantities']]
        
        if numbers and quantities:
            amount = numbers[0]
            unit = quantities[0]
            
            if unit in ['oz']:
                return int(amount * 29.5735)  # Convert to ml
            elif unit in ['ml']:
                return int(amount)
            elif unit in ['cups', 'cup']:
                return int(amount * 240)  # 8oz cup
            elif unit in ['glasses', 'glass']:
                return int(amount * 240)
        
        # Default glass/cup assumption
        if any(word in message_lower for word in ['glass', 'cup']) and numbers:
            return int(numbers[0] * 240)
        
        return None
    
    def parse_time_reference(self, message: str) -> Optional[datetime]:
        """Parse time references into datetime objects"""
        message_lower = message.lower()
        now = datetime.now()
        
        # Try to parse specific times first (e.g., "3pm", "2:30")
        specific_time = self._parse_specific_time(message_lower)
        if specific_time:
            return specific_time
        
        # Try to parse specific dates (e.g., "August 13th", "next Thursday")
        specific_date = self._parse_specific_date(message_lower)
        if specific_date:
            return specific_date
        
        # Relative time patterns
        if 'tomorrow' in message_lower:
            if 'morning' in message_lower:
                return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0)
            elif 'evening' in message_lower:
                return (now + timedelta(days=1)).replace(hour=19, minute=0, second=0)
            else:
                return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0)
        
        elif 'today' in message_lower:
            if 'morning' in message_lower:
                return now.replace(hour=9, minute=0, second=0)
            elif 'evening' in message_lower:
                return now.replace(hour=19, minute=0, second=0)
            elif 'afternoon' in message_lower:
                return now.replace(hour=14, minute=0, second=0)
            else:
                return now.replace(hour=9, minute=0, second=0)
        
        elif 'tonight' in message_lower or 'this evening' in message_lower:
            return now.replace(hour=19, minute=0, second=0)
        
        elif 'this afternoon' in message_lower:
            return now.replace(hour=14, minute=0, second=0)
        
        elif 'this morning' in message_lower:
            return now.replace(hour=9, minute=0, second=0)
        
        # Time of day patterns
        for time_word, hour_range in self.time_patterns.items():
            if time_word in message_lower:
                target_time = now.replace(hour=hour_range['start'], minute=0, second=0)
                if target_time <= now:
                    target_time += timedelta(days=1)
                return target_time
        
        return None
    
    def _parse_specific_time(self, message: str) -> Optional[datetime]:
        """Parse specific times like '3pm', '2:30', '14:00'"""
        now = datetime.now()
        
        # Pattern: 3pm, 2:30pm, 14:00, etc.
        time_patterns = [
            r'(\d{1,2}):?(\d{2})?\s*(am|pm)?',  # 3pm, 2:30pm, 14:00
            r'(\d{1,2})\s*(am|pm)',  # 3 pm
            r'(\d{1,2})\s*oclock',  # 3 oclock
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                ampm = match.group(3) if match.group(3) else None
                
                # Handle AM/PM
                if ampm:
                    if ampm.lower() == 'pm' and hour != 12:
                        hour += 12
                    elif ampm.lower() == 'am' and hour == 12:
                        hour = 0
                elif hour > 12:  # 24-hour format
                    pass
                else:  # Assume PM for single digits without AM/PM
                    hour += 12
                
                target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # If time has passed today, schedule for tomorrow
                if target_time <= now:
                    target_time += timedelta(days=1)
                
                return target_time
        
        return None
    
    def _parse_specific_date(self, message: str) -> Optional[datetime]:
        """Parse specific dates like 'August 13th', 'next Thursday'"""
        now = datetime.now()
        
        # Pattern: next Thursday, this Friday, etc.
        day_pattern = r'(next|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
        day_match = re.search(day_pattern, message.lower())
        if day_match:
            modifier = day_match.group(1)
            day_name = day_match.group(2)
            
            # Map day names to numbers (0=Monday, 6=Sunday)
            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            target_day = day_map[day_name]
            current_day = now.weekday()
            
            if modifier == 'next':
                days_ahead = (target_day - current_day) % 7
                if days_ahead == 0:  # Same day, go to next week
                    days_ahead = 7
            else:  # 'this'
                days_ahead = (target_day - current_day) % 7
                if days_ahead == 0:  # Same day, use today
                    days_ahead = 0
            
            target_date = now + timedelta(days=days_ahead)
            return target_date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Pattern: August 13th, Aug 13, etc.
        date_patterns = [
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?',
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})(?:st|nd|rd|th)?'
        ]
        
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        for pattern in date_patterns:
            match = re.search(pattern, message.lower())
            if match:
                month_name = match.group(1)
                day = int(match.group(2))
                
                if month_name in month_map:
                    month = month_map[month_name]
                    year = now.year
                    
                    # If the date has passed this year, assume next year
                    target_date = datetime(year, month, day)
                    if target_date < now:
                        target_date = datetime(year + 1, month, day)
                    
                    return target_date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        return None
    
    def parse_duration(self, message: str) -> Optional[timedelta]:
        """Parse duration expressions like '1 hour', '30 minutes', '2-4pm'"""
        message_lower = message.lower()
        
        # Pattern: 2-4pm, 3-5pm (time range)
        time_range_pattern = r'(\d{1,2})-(\d{1,2})\s*(am|pm)?'
        time_range_match = re.search(time_range_pattern, message_lower)
        if time_range_match:
            start_hour = int(time_range_match.group(1))
            end_hour = int(time_range_match.group(2))
            ampm = time_range_match.group(3)
            
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
            return timedelta(hours=duration_hours)
        
        # Pattern: 1 hour, 30 minutes, etc.
        duration_patterns = [
            (r'(\d+)\s*hours?', 'hours'),
            (r'(\d+)\s*hrs?', 'hours'),
            (r'(\d+)\s*minutes?', 'minutes'),
            (r'(\d+)\s*mins?', 'minutes'),
            (r'(\d+)\s*days?', 'days')
        ]
        
        for pattern, unit in duration_patterns:
            match = re.search(pattern, message_lower)
            if match:
                value = int(match.group(1))
                if unit == 'hours':
                    return timedelta(hours=value)
                elif unit == 'minutes':
                    return timedelta(minutes=value)
                elif unit == 'days':
                    return timedelta(days=value)
        
        return None
    
    def parse_portion_multiplier(self, message: str) -> float:
        """Parse portion multiplier from message"""
        message_lower = message.lower()
        
        if 'half' in message_lower:
            return 0.5
        elif 'quarter' in message_lower:
            return 0.25
        elif any(word in message_lower for word in ['two', '2', 'double']):
            return 2.0
        elif any(word in message_lower for word in ['three', '3']):
            return 3.0
        
        # Look for explicit numbers
        portion_match = re.search(r'\b(\d+\.?\d*)\s*(of|x)?\s*', message_lower)
        if portion_match:
            return float(portion_match.group(1))
        
        return 1.0
    
    def extract_muscle_groups(self, message: str) -> List[str]:
        """Extract muscle groups from gym message"""
        muscle_map = {
            'chest': ['chest', 'pecs', 'pectorals'],
            'back': ['back', 'lats', 'latissimus', 'rhomboids'],
            'legs': ['legs', 'quads', 'hamstrings', 'glutes', 'calves'],
            'shoulders': ['shoulders', 'delts', 'deltoids'],
            'arms': ['arms', 'biceps', 'triceps', 'bis', 'tris'],
            'core': ['core', 'abs', 'abdominals']
        }
        
        message_lower = message.lower()
        found_groups = []
        
        for group, keywords in muscle_map.items():
            if any(keyword in message_lower for keyword in keywords):
                found_groups.append(group)
        
        return found_groups
    
    def extract_image_category(self, message: str) -> str:
        """Extract image category from message"""
        message_lower = message.lower()
        
        # Category patterns
        category_patterns = {
            'receipts': ['receipt', 'bill', 'invoice', 'purchase'],
            'documents': ['document', 'paper', 'form', 'contract'],
            'work': ['work', 'office', 'business', 'meeting'],
            'personal': ['personal', 'family', 'friends', 'home'],
            'photos': ['photo', 'picture', 'image', 'selfie']
        }
        
        for category, keywords in category_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                return category
        
        # Default to photos if no specific category
        return 'photos'

    def parse_gym_workout(self, message: str) -> Optional[Dict]:
        """Parse gym workout from message"""
        message_lower = message.lower()
        
        # Extract muscle group
        muscle_group = self._extract_muscle_group(message_lower)
        if not muscle_group:
            return None
        
        # Extract exercises with details
        exercises = self._extract_exercises(message_lower)
        if not exercises:
            return None
        
        return {
            'muscle_group': muscle_group,
            'exercises': exercises,
            'date': datetime.now().date(),
            'total_exercises': len(exercises)
        }
    
    def _extract_muscle_group(self, message: str) -> Optional[str]:
        """Extract the muscle group being worked"""
        for muscle, exercises in self.gym_patterns.items():
            if muscle in message:
                return muscle
        
        # Look for specific muscle group mentions
        muscle_keywords = {
            'chest': ['chest', 'pecs', 'pec'],
            'back': ['back', 'lats', 'traps'],
            'legs': ['legs', 'quads', 'hamstrings', 'calves'],
            'arms': ['arms', 'biceps', 'triceps'],
            'shoulders': ['shoulders', 'delts', 'deltoids'],
            'core': ['core', 'abs', 'abs', 'stomach']
        }
        
        for muscle, keywords in muscle_keywords.items():
            if any(keyword in message for keyword in keywords):
                return muscle
        
        return None
    
    def _extract_exercises(self, message: str) -> List[Dict]:
        """Extract exercises with weights, reps, and sets"""
        exercises = []
        
        # Pattern: exercise weight x reps (e.g., "bench 225x5", "squat 315x3")
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
                'sets': 1  # Default to 1 set
            })
        
        # Pattern: exercise weight x reps x sets (e.g., "bench 225x5x3")
        exercise_pattern_sets = r'(\w+)\s+(\d+)(?:x|×)(\d+)(?:x|×)(\d+)'
        matches_sets = re.finditer(exercise_pattern_sets, message)
        
        for match in matches_sets:
            exercise_name = match.group(1)
            weight = int(match.group(2))
            reps = int(match.group(3))
            sets = int(match.group(4))
            
            exercises.append({
                'name': exercise_name,
                'weight': weight,
                'reps': reps,
                'sets': sets
            })
        
        # Pattern: exercise with just weight (e.g., "bench 225")
        exercise_pattern_weight = r'(\w+)\s+(\d+)(?!\s*(?:x|×))'
        matches_weight = re.finditer(exercise_pattern_weight, message)
        
        for match in matches_weight:
            exercise_name = match.group(1)
            weight = int(match.group(2))
            
            # Check if this exercise was already captured with reps
            if not any(ex['name'] == exercise_name and ex['weight'] == weight for ex in exercises):
                exercises.append({
                    'name': exercise_name,
                    'weight': weight,
                    'reps': None,
                    'sets': 1
                })
        
        return exercises
    
    def parse_reminder(self, message: str) -> Optional[Dict]:
        """Parse reminder creation from message"""
        message_lower = message.lower()
        
        # Extract reminder text
        reminder_text = self._extract_reminder_text(message)
        if not reminder_text:
            return None
        
        # Extract reminder time
        reminder_time = self.parse_time_reference(message)
        if not reminder_time:
            return None
        
        # Extract priority
        priority = self._extract_reminder_priority(message)
        
        return {
            'text': reminder_text,
            'scheduled_time': reminder_time,
            'priority': priority,
            'created_at': datetime.now()
        }
    
    def _extract_reminder_text(self, message: str) -> Optional[str]:
        """Extract the reminder text from message"""
        # Look for reminder triggers
        triggers = ['remind me to', 'reminder to', 'don\'t forget to', 'call', 'text', 'email']
        
        for trigger in triggers:
            if trigger in message.lower():
                # Extract text after the trigger
                start_idx = message.lower().find(trigger) + len(trigger)
                reminder_text = message[start_idx:].strip()
                
                # Clean up the reminder text
                reminder_text = re.sub(r'\b(this evening|tonight|tomorrow|today)\b', '', reminder_text, flags=re.IGNORECASE)
                reminder_text = reminder_text.strip()
                
                if reminder_text:
                    return reminder_text
        
        return None
    
    def _extract_reminder_priority(self, message: str) -> str:
        """Extract reminder priority from message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['urgent', 'asap', 'important', 'critical']):
            return 'high'
        elif any(word in message_lower for word in ['soon', 'quick', 'fast']):
            return 'medium'
        else:
            return 'low'

    def parse_photo_upload(self, message: str) -> Optional[Dict]:
        """Parse photo upload request from message"""
        message_lower = message.lower()
        
        # Check if this is a photo upload request
        photo_triggers = ['add this photo', 'save this photo', 'upload this photo', 'organize this photo']
        if not any(trigger in message_lower for trigger in photo_triggers):
            return None
        
        # Extract target folder
        target_folder = self._extract_target_folder(message)
        if not target_folder:
            return None
        
        return {
            'action': 'upload_photo',
            'target_folder': target_folder,
            'message': message
        }
    
    def _extract_target_folder(self, message: str) -> Optional[str]:
        """Extract the target folder from message"""
        message_lower = message.lower()
        
        # Look for "to [folder]" pattern
        to_pattern = r'to\s+(\w+)'
        to_match = re.search(to_pattern, message_lower)
        if to_match:
            folder = to_match.group(1)
            return folder
        
        # Look for "in [folder]" pattern
        in_pattern = r'in\s+(\w+)'
        in_match = re.search(in_pattern, message_lower)
        if in_match:
            folder = in_match.group(1)
            return folder
        
        # Look for "folder" keyword
        folder_pattern = r'(\w+)\s+folder'
        folder_match = re.search(folder_pattern, message_lower)
        if folder_match:
            folder = folder_match.group(1)
            return folder
        
        return None
    
    def parse_drive_organization(self, message: str) -> Optional[Dict]:
        """Parse drive organization request from message"""
        message_lower = message.lower()
        
        # Check if this is a drive organization request
        drive_triggers = ['organize', 'organise', 'sort', 'file', 'backup', 'save']
        if not any(trigger in message_lower for trigger in drive_triggers):
            return None
        
        # Extract file type
        file_type = self._extract_file_type(message)
        
        # Extract target folder
        target_folder = self._extract_target_folder(message)
        
        return {
            'action': 'organize_drive',
            'file_type': file_type,
            'target_folder': target_folder,
            'message': message
        }
    
    def _extract_file_type(self, message: str) -> Optional[str]:
        """Extract the type of file being organized"""
        message_lower = message.lower()
        
        file_types = {
            'photos': ['photo', 'picture', 'image', 'pic'],
            'documents': ['document', 'doc', 'pdf', 'file'],
            'receipts': ['receipt', 'bill', 'invoice'],
            'work': ['work', 'business', 'professional'],
            'personal': ['personal', 'private', 'family']
        }
        
        for file_type, keywords in file_types.items():
            if any(keyword in message_lower for keyword in keywords):
                return file_type
        
        return None

# Usage example
def create_enhanced_processor(food_database: Dict) -> EnhancedNLPProcessor:
    """Create enhanced processor with food database"""
    processor = EnhancedNLPProcessor()
    processor.food_db = food_database
    return processor
