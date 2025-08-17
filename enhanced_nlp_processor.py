import spacy
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

# Load spaCy model (free)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Please install spaCy English model: python -m spacy download en_core_web_sm")
    nlp = None

class EnhancedNLPProcessor:
    def __init__(self):
        self.food_db = {}  # Will be loaded from JSON
        
        # Enhanced intent patterns
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
                r'\b(bench|squat|deadlift|cardio|weights)\b'
            ],
            'todo': [
                r'\b(todo|task|add|remember|need to|don\'t forget)\b',
                r'\b(list|remind me to)\b'
            ],
            'reminder': [
                r'\b(remind me|reminder|don\'t forget|schedule)\b',
                r'\b(later|tomorrow|tonight|evening|morning)\b'
            ],
            'completion': [
                r'\b(did|done|finished|completed|called|went|bought)\b',
                r'\b(check off|mark complete|crossed off)\b'
            ],
            'calendar': [
                r'\b(schedule|calendar|meeting|appointment|free|busy)\b',
                r'\b(today|tomorrow|next week|what\'s next)\b'
            ],
            'image': [
                r'\b(save|upload|store|organize|photo|picture|image)\b',
                r'\b(receipt|document|scan|backup)\b'
            ],
            'drive': [
                r'\b(drive|folder|organize|file|document)\b',
                r'\b(work|personal|receipts|photos)\b'
            ]
        }
        
        # Time expressions with spaCy
        self.time_patterns = {
            'morning': 9,
            'afternoon': 14,
            'evening': 19,
            'night': 20,
            'lunch': 12,
            'dinner': 18
        }
        
        # Calendar-specific patterns
        self.calendar_patterns = {
            'create_event': [
                r'\b(meeting|appointment|call|visit|lunch|dinner)\b',
                r'\b(with|to|at|from)\b'
            ],
            'check_schedule': [
                r'\b(what\'s|what is|show|list|check)\b',
                r'\b(schedule|calendar|today|tomorrow|this week)\b'
            ],
            'modify_event': [
                r'\b(move|reschedule|change|update|edit)\b',
                r'\b(meeting|appointment|event)\b'
            ]
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
    
    def parse_calendar_event(self, message: str, entities: Dict) -> Optional[Dict]:
        """Parse calendar event from message"""
        try:
            # Extract event details
            summary = self._extract_event_summary(message, entities)
            start_time = self._extract_event_time(message, entities)
            duration = self._extract_event_duration(message, entities)
            location = self._extract_event_location(message, entities)
            people = self._extract_event_people(message, entities)
            
            if not summary or not start_time:
                return None
            
            # Calculate end time
            if duration:
                end_time = start_time + duration
            else:
                end_time = start_time + timedelta(hours=1)
            
            return {
                'summary': summary,
                'start_time': start_time,
                'end_time': end_time,
                'location': location,
                'people': people,
                'description': self._build_event_description(message, entities)
            }
            
        except Exception as e:
            print(f"Error parsing calendar event: {e}")
            return None
    
    def _extract_event_summary(self, message: str, entities: Dict) -> Optional[str]:
        """Extract event summary/title"""
        # Look for meeting/appointment keywords
        meeting_keywords = ['meeting', 'appointment', 'call', 'visit', 'lunch', 'dinner']
        message_lower = message.lower()
        
        for keyword in meeting_keywords:
            if keyword in message_lower:
                # Extract text around the keyword
                start_idx = message_lower.find(keyword)
                end_idx = start_idx + len(keyword)
                
                # Look for "with [person]" or "at [location]"
                with_match = re.search(r'with\s+([^.!?]+)', message[start_idx:])
                if with_match:
                    return f"{keyword.title()} with {with_match.group(1).strip()}"
                
                # Look for person names
                people = entities.get('people', [])
                if people:
                    person = people[0]['name']
                    return f"{keyword.title()} with {person}"
                
                return keyword.title()
        
        return None
    
    def _extract_event_time(self, message: str, entities: Dict) -> Optional[datetime]:
        """Extract event start time"""
        # Use existing time parsing
        return self.parse_time_reference(message)
    
    def _extract_event_duration(self, message: str, entities: Dict) -> Optional[timedelta]:
        """Extract event duration"""
        durations = entities.get('durations', [])
        if not durations:
            return None
        
        duration = durations[0]
        if duration['unit'] == 'hours':
            return timedelta(hours=duration['value'])
        elif duration['unit'] == 'minutes':
            return timedelta(minutes=duration['value'])
        elif duration['unit'] == 'days':
            return timedelta(days=duration['value'])
        
        return None
    
    def _extract_event_location(self, message: str, entities: Dict) -> Optional[str]:
        """Extract event location"""
        locations = entities.get('locations', [])
        if locations:
            return locations[0]['name']
        
        # Look for "at [location]" pattern
        at_match = re.search(r'at\s+([^.!?]+)', message.lower())
        if at_match:
            return at_match.group(1).strip()
        
        return None
    
    def _extract_event_people(self, message: str, entities: Dict) -> List[str]:
        """Extract people involved in event"""
        people = entities.get('people', [])
        return [p['name'] for p in people]
    
    def _build_event_description(self, message: str, entities: Dict) -> str:
        """Build event description from message and entities"""
        description_parts = []
        
        # Add original message context
        description_parts.append(f"Created from: {message}")
        
        # Add people
        people = self._extract_event_people(message, entities)
        if people:
            description_parts.append(f"People: {', '.join(people)}")
        
        # Add location
        location = self._extract_event_location(message, entities)
        if location:
            description_parts.append(f"Location: {location}")
        
        return ' | '.join(description_parts)
    
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
        
        # Relative time patterns
        if 'tomorrow' in message_lower:
            if 'morning' in message_lower:
                return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0)
            elif 'evening' in message_lower:
                return (now + timedelta(days=1)).replace(hour=19, minute=0, second=0)
            else:
                return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0)
        
        elif 'tonight' in message_lower or 'this evening' in message_lower:
            return now.replace(hour=19, minute=0, second=0)
        
        elif 'next week' in message_lower:
            days_ahead = 6 - now.weekday()  # Next Sunday
            return (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0)
        
        elif 'monday' in message_lower:
            days_ahead = (0 - now.weekday()) % 7
            if days_ahead == 0:  # Today is Monday
                days_ahead = 7  # Next Monday
            return (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0)
        
        # Time of day patterns
        for time_word, hour in self.time_patterns.items():
            if time_word in message_lower:
                target_time = now.replace(hour=hour, minute=0, second=0)
                if target_time <= now:
                    target_time += timedelta(days=1)
                return target_time
        
        # Specific time patterns (3pm, 15:30, etc.)
        time_match = re.search(r'\b(\d{1,2}):?(\d{2})?\s*(am|pm)?\b', message_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3)
            
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            elif not ampm and hour <= 12:
                # Assume PM for reasonable hours
                hour += 12 if hour < 8 else 0
            
            target_time = now.replace(hour=hour, minute=minute, second=0)
            if target_time <= now:
                target_time += timedelta(days=1)
            return target_time
        
        # Default to evening if no specific time
        return now.replace(hour=19, minute=0, second=0)
    
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

# Usage example
def create_enhanced_processor(food_database: Dict) -> EnhancedNLPProcessor:
    """Create enhanced processor with food database"""
    processor = EnhancedNLPProcessor()
    processor.food_db = food_database
    return processor
