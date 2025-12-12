"""
Location detection utility.
Extracts location information from user prompts using simple pattern matching.
"""
import re
from typing import Optional, List


class LocationDetector:
    """
    Detects location mentions in user prompts.
    Uses pattern matching to identify city, state, or country names.
    """
    
    # Common location patterns
    LOCATION_PATTERNS = [
        r'\b(in|at|from|near|around)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "in New York", "at London"
        r'\b(in|at|from|near|around)\s+([a-z]+(?:\s+[a-z]+)+)',  # "at alamo ranch", "in new york" (lowercase)
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(city|state|country|location)',  # "New York city"
        r'\bI\s+(am|live|located)\s+(in|at|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "I am in New York"
        r'\b(location|place|area|region):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "location: New York"
    ]
    
    # Common location keywords that might indicate location context
    LOCATION_KEYWORDS = [
        'location', 'city', 'state', 'country', 'area', 'region', 
        'near', 'around', 'in', 'at', 'from', 'local'
    ]
    
    # Words to exclude from location detection (common question words, pronouns, etc.)
    EXCLUDED_WORDS = {
        'what', 'where', 'when', 'how', 'why', 'who', 'which', 'whom',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'these', 'those',
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'am', 'be', 'been', 'being',
        'can', 'could', 'should', 'would', 'will', 'shall', 'may', 'might', 'must',
        'do', 'does', 'did', 'done', 'have', 'has', 'had', 'having',
        'get', 'got', 'give', 'gave', 'go', 'went', 'come', 'came',
        'say', 'said', 'tell', 'told', 'know', 'knew', 'think', 'thought',
        'see', 'saw', 'look', 'looked', 'want', 'wanted', 'need', 'needed',
        'make', 'made', 'take', 'took', 'use', 'used', 'find', 'found',
        'work', 'worked', 'call', 'called', 'try', 'tried', 'ask', 'asked'
    }
    
    def extract_location(self, text: str) -> Optional[str]:
        """
        Extract location from user prompt.
        
        Args:
            text: User's question/prompt text
            
        Returns:
            Optional[str]: Extracted location name if found, None otherwise
        """
        if not text:
            return None
        
        text = text.strip()
        
        # Try each pattern
        for pattern in self.LOCATION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Get the last match (most likely to be the location)
                match = matches[-1]
                # Extract location from tuple (pattern might return multiple groups)
                if isinstance(match, tuple):
                    # Find the location part (usually the longest capitalized or lowercase word)
                    location = None
                    for part in match:
                        if part and len(part) > 2:
                            # Check if it's not a common word or excluded word
                            part_lower = part.lower()
                            if (part_lower not in ['in', 'at', 'from', 'near', 'around', 'city', 'state', 'country', 'location', 'place', 'area', 'region'] and
                                part_lower not in self.EXCLUDED_WORDS):
                                if location is None or len(part) > len(location):
                                    location = part
                    if location:
                        # Capitalize first letter of each word if lowercase
                        if location and not location[0].isupper():
                            location = ' '.join(word.capitalize() for word in location.split())
                        return location.strip()
                elif isinstance(match, str) and len(match) > 2:
                    # Check if it's not an excluded word
                    match_lower = match.lower()
                    if match_lower not in self.EXCLUDED_WORDS:
                        # Capitalize first letter of each word if lowercase
                        if not match[0].isupper():
                            match = ' '.join(word.capitalize() for word in match.split())
                        return match.strip()
        
        # Fallback: Look for capitalized words that might be locations
        # Also check for lowercase location names after location keywords
        words = text.split()
        text_lower = text.lower()
        
        # First, check for lowercase locations after location keywords (e.g., "at alamo ranch")
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w\s]', '', word)
            clean_word_lower = clean_word.lower()
            
            # Check if this is a location keyword
            if clean_word_lower in self.LOCATION_KEYWORDS:
                # Look ahead for potential location name (next 1-3 words)
                location_parts = []
                for j in range(i + 1, min(i + 4, len(words))):
                    next_word = re.sub(r'[^\w\s]', '', words[j])
                    next_word_lower = next_word.lower()
                    
                    # Stop if we hit another location keyword or excluded word
                    if (next_word_lower in self.LOCATION_KEYWORDS or 
                        next_word_lower in self.EXCLUDED_WORDS):
                        break
                    
                    # Collect if it's a valid word
                    if len(next_word) > 2:
                        location_parts.append(next_word)
                
                if location_parts:
                    location_name = ' '.join(location_parts)
                    # Capitalize first letter of each word for better matching
                    location_title = ' '.join(word.capitalize() for word in location_parts)
                    return location_title
        
        # Second, check for capitalized sequences
        capitalized_sequences = []
        current_sequence = []
        
        for word in words:
            clean_word = re.sub(r'[^\w\s]', '', word)
            if clean_word and clean_word[0].isupper() and len(clean_word) > 2:
                clean_word_lower = clean_word.lower()
                if clean_word_lower not in self.EXCLUDED_WORDS:
                    current_sequence.append(clean_word)
            else:
                if current_sequence:
                    capitalized_sequences.append(' '.join(current_sequence))
                    current_sequence = []
        
        if current_sequence:
            capitalized_sequences.append(' '.join(current_sequence))
        
        # Return capitalized sequences if location keywords are nearby
        for seq in capitalized_sequences:
            seq_lower = seq.lower()
            if seq_lower in self.EXCLUDED_WORDS:
                continue
            for keyword in self.LOCATION_KEYWORDS:
                if keyword in text_lower:
                    seq_pos = text_lower.find(seq_lower)
                    keyword_pos = text_lower.find(keyword)
                    if abs(seq_pos - keyword_pos) < 50:
                        return seq
        
        return None
    
    def has_location_context(self, text: str) -> bool:
        """
        Check if the text has location-related context.
        
        Args:
            text: User's question/prompt text
            
        Returns:
            bool: True if location context is detected
        """
        if not text:
            return False
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.LOCATION_KEYWORDS)

