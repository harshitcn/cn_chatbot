"""
Query engine with intent detection and structured data querying.
Detects user intent (camps/programs/additional) and queries only relevant structured data.
"""
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class StructuredQueryEngine:
    """
    Query engine that detects intent and queries structured data.
    Returns clean, structured answers without noise.
    """
    
    def __init__(self):
        """Initialize the query engine."""
        pass
    
    def detect_intent(self, query: str) -> str:
        """
        Detect user intent from query.
        
        Returns:
            'camps', 'programs', 'additional_programs', or 'general'
        """
        query_lower = query.lower()
        
        # Camp-related keywords
        camp_keywords = ['camp', 'camps', 'summer camp', 'winter camp']
        if any(keyword in query_lower for keyword in camp_keywords):
            return 'camps'
        
        # Additional programs keywords
        additional_keywords = [
            'additional', 'other program', 'parent', 'birthday', 'party',
            'night out', 'parents night', 'home school', 'homeschool'
        ]
        if any(keyword in query_lower for keyword in additional_keywords):
            return 'additional_programs'
        
        # Programs keywords
        program_keywords = ['program', 'programs', 'core program', 'academy', 'create', 'jr']
        if any(keyword in query_lower for keyword in program_keywords):
            return 'programs'
        
        # Default to general
        return 'general'
    
    def _format_camps_answer(self, camps_data: Dict[str, Any], location: Optional[str] = None) -> Dict[str, Any]:
        """Format camps data into structured answer."""
        answer = {
            "category": "camps",
            "location": location or "TX – Alamo Ranch",
            "overview": camps_data.get("overview", {}),
            "highlights": [],
            "items": []
        }
        
        # Extract highlights from overview
        overview = camps_data.get("overview", {})
        if overview.get("summary"):
            # Extract key points from summary (first 2-3 sentences)
            sentences = overview["summary"].split('. ')
            answer["highlights"] = [s.strip() + '.' for s in sentences[:3] if s.strip()]
        
        # Format camp items
        camps = camps_data.get("camps", [])
        for camp in camps:
            item = {
                "name": camp.get("name", "Camp"),
                "age_range": camp.get("age_range"),
                "description": camp.get("description"),
                "duration": camp.get("duration"),
                "schedule": camp.get("schedule")
            }
            # Remove None values
            item = {k: v for k, v in item.items() if v is not None}
            answer["items"].append(item)
        
        return answer
    
    def _format_programs_answer(self, programs_data: Dict[str, Any], location: Optional[str] = None) -> Dict[str, Any]:
        """Format programs data into structured answer."""
        answer = {
            "category": "programs",
            "location": location or "TX – Alamo Ranch",
            "overview": programs_data.get("overview", {}),
            "highlights": [],
            "items": []
        }
        
        overview = programs_data.get("overview", {})
        if overview.get("summary"):
            sentences = overview["summary"].split('. ')
            answer["highlights"] = [s.strip() + '.' for s in sentences[:3] if s.strip()]
        
        programs = programs_data.get("programs", [])
        for program in programs:
            item = {
                "name": program.get("name", "Program"),
                "age_range": program.get("age_range"),
                "description": program.get("description")
            }
            item = {k: v for k, v in item.items() if v is not None}
            answer["items"].append(item)
        
        return answer
    
    def _format_additional_programs_answer(self, additional_data: Dict[str, Any], location: Optional[str] = None) -> Dict[str, Any]:
        """Format additional programs data into structured answer."""
        answer = {
            "category": "additional_programs",
            "location": location or "TX – Alamo Ranch",
            "overview": additional_data.get("overview", {}),
            "highlights": [],
            "items": []
        }
        
        overview = additional_data.get("overview", {})
        if overview.get("summary"):
            sentences = overview["summary"].split('. ')
            answer["highlights"] = [s.strip() + '.' for s in sentences[:3] if s.strip()]
        
        programs = additional_data.get("programs", [])
        for program in programs:
            item = {
                "name": program.get("name", "Program"),
                "age_range": program.get("age_range"),
                "description": program.get("description")
            }
            item = {k: v for k, v in item.items() if v is not None}
            answer["items"].append(item)
        
        return answer
    
    def _format_general_answer(self, all_data: Dict[str, Any], location: Optional[str] = None) -> Dict[str, Any]:
        """Format general answer when intent is unclear."""
        # Try to provide a summary of all categories
        answer = {
            "category": "general",
            "location": location or "TX – Alamo Ranch",
            "overview": {},
            "highlights": [],
            "items": []
        }
        
        # Combine highlights from all sections
        highlights = []
        for category in ['camps', 'programs', 'additional_programs']:
            category_data = all_data.get(category, {})
            overview = category_data.get("overview", {})
            if overview.get("summary"):
                highlights.append(overview["summary"][:200])
        
        answer["highlights"] = highlights[:3]
        
        return answer
    
    def answer_query(
        self,
        query: str,
        structured_data: Dict[str, Any],
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a query using structured data.
        
        Args:
            query: User query string
            structured_data: Structured data from scraper
            location: Optional location string
            
        Returns:
            Dict with structured answer
        """
        try:
            # Detect intent
            intent = self.detect_intent(query)
            logger.info(f"Detected intent: {intent} for query: {query}")
            
            # Format answer based on intent
            if intent == 'camps':
                camps_data = structured_data.get("camps", {})
                if camps_data.get("camps"):
                    return {
                        "status": "success",
                        "query": query,
                        "answer": self._format_camps_answer(camps_data, location)
                    }
                else:
                    return {
                        "status": "no_results",
                        "query": query,
                        "answer": {
                            "category": "camps",
                            "location": location or "TX – Alamo Ranch",
                            "message": "No camp information found."
                        }
                    }
            
            elif intent == 'programs':
                programs_data = structured_data.get("programs", {})
                if programs_data.get("programs"):
                    return {
                        "status": "success",
                        "query": query,
                        "answer": self._format_programs_answer(programs_data, location)
                    }
                else:
                    return {
                        "status": "no_results",
                        "query": query,
                        "answer": {
                            "category": "programs",
                            "location": location or "TX – Alamo Ranch",
                            "message": "No program information found."
                        }
                    }
            
            elif intent == 'additional_programs':
                additional_data = structured_data.get("additional_programs", {})
                if additional_data.get("programs"):
                    return {
                        "status": "success",
                        "query": query,
                        "answer": self._format_additional_programs_answer(additional_data, location)
                    }
                else:
                    return {
                        "status": "no_results",
                        "query": query,
                        "answer": {
                            "category": "additional_programs",
                            "location": location or "TX – Alamo Ranch",
                            "message": "No additional program information found."
                        }
                    }
            
            else:  # general
                return {
                    "status": "success",
                    "query": query,
                    "answer": self._format_general_answer(structured_data, location)
                }
        
        except Exception as e:
            logger.error(f"Error answering query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "query": query,
                "answer": {
                    "category": "error",
                    "message": "I'm sorry, I encountered an error processing your query."
                }
            }
