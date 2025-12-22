"""
Query engine for API-based data extraction.
Converts API responses into formatted answers for user queries.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class APIQueryEngine:
    """
    Query engine that processes API data and generates answers.
    """
    
    def __init__(self, api_client):
        """
        Initialize the API query engine.
        
        Args:
            api_client: DataAPIClient instance
        """
        self.api_client = api_client
    
    def _detect_intent(self, query: str) -> str:
        """
        Detect user intent from query to determine which API to call.
        
        Args:
            query: User query string
            
        Returns:
            str: Intent category (camps, programs, events, clubs, facility, general)
        """
        query_lower = query.lower()
        
        # Camp-related keywords
        if any(keyword in query_lower for keyword in ['camp', 'camps', 'upcoming camp', 'camp schedule']):
            return 'camps'
        
        # Event-related keywords
        if any(keyword in query_lower for keyword in ['event', 'events', 'upcoming event', 'upcoming events']):
            return 'events'
        
        # Club-related keywords
        if any(keyword in query_lower for keyword in ['club', 'clubs']):
            return 'clubs'
        
        # Program-related keywords (but not events)
        if any(keyword in query_lower for keyword in ['program', 'programs', 'create', 'academy', 'academies', 'jr']):
            return 'programs'
        
        # Facility/location info
        if any(keyword in query_lower for keyword in ['facility', 'location', 'address', 'contact', 'info', 'about']):
            return 'facility'
        
        return 'general'
    
    def _format_camp(self, camp: Dict[str, Any]) -> str:
        """Format a single camp into readable text."""
        parts = []
        
        if camp.get('title') or camp.get('name'):
            parts.append(f"Camp: {camp.get('title') or camp.get('name')}")
        
        if camp.get('age'):
            parts.append(f"Age Range: {camp.get('age')}")
        
        if camp.get('description'):
            parts.append(f"Description: {camp.get('description')}")
        
        if camp.get('price'):
            price = camp.get('price')
            if isinstance(price, (int, float)):
                parts.append(f"Price: ${price:.0f}")
            else:
                parts.append(f"Price: {price}")
        
        # Format dates
        start_dt_str = camp.get('startDateTime') or camp.get('startDate')
        end_dt_str = camp.get('endDateTime') or camp.get('endDate')
        
        if start_dt_str and end_dt_str:
            try:
                start_dt = datetime.fromisoformat(start_dt_str.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_dt_str.replace('Z', '+00:00'))
                
                if start_dt.date() == end_dt.date():
                    parts.append(f"Date: {start_dt.strftime('%b %d, %Y')}")
                else:
                    parts.append(f"Duration: {start_dt.strftime('%b %d')} - {end_dt.strftime('%b %d, %Y')}")
                
                if start_dt.time() != end_dt.time():
                    parts.append(f"Schedule: {start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}")
            except (ValueError, AttributeError):
                pass
        
        return ". ".join(parts) if parts else ""
    
    def _format_program(self, program: Dict[str, Any]) -> str:
        """Format a single program into readable text."""
        parts = []
        
        # Program name/title
        program_name = program.get('name') or program.get('title') or program.get('programName')
        if program_name:
            parts.append(f"Program: {program_name}")
        
        # Age range
        age_range = program.get('ageRange') or program.get('age') or program.get('ageGroup')
        if age_range:
            parts.append(f"Age Range: {age_range}")
        
        # Description
        description = program.get('description') or program.get('programDescription') or program.get('overview')
        if description:
            parts.append(f"Description: {description}")
        
        # Additional details
        if program.get('duration'):
            parts.append(f"Duration: {program.get('duration')}")
        
        if program.get('schedule'):
            parts.append(f"Schedule: {program.get('schedule')}")
        
        if program.get('price'):
            price = program.get('price')
            if isinstance(price, (int, float)):
                parts.append(f"Price: ${price:.0f}")
            else:
                parts.append(f"Price: {price}")
        
        return ". ".join(parts) if parts else ""
    
    def _format_event(self, event: Dict[str, Any]) -> str:
        """Format a single event into readable text."""
        parts = []
        
        if event.get('name') or event.get('title'):
            parts.append(f"Event: {event.get('name') or event.get('title')}")
        
        if event.get('description'):
            parts.append(f"Description: {event.get('description')}")
        
        # Format dates
        start_dt_str = event.get('startDateTime') or event.get('startDate')
        end_dt_str = event.get('endDateTime') or event.get('endDate')
        
        if start_dt_str:
            try:
                start_dt = datetime.fromisoformat(start_dt_str.replace('Z', '+00:00'))
                parts.append(f"Date: {start_dt.strftime('%b %d, %Y')}")
            except (ValueError, AttributeError):
                pass
        
        return ". ".join(parts) if parts else ""
    
    def _format_club(self, club: Dict[str, Any]) -> str:
        """Format a single club into readable text."""
        parts = []
        
        if club.get('name') or club.get('title'):
            parts.append(f"Club: {club.get('name') or club.get('title')}")
        
        if club.get('description'):
            parts.append(f"Description: {club.get('description')}")
        
        if club.get('ageRange') or club.get('age'):
            parts.append(f"Age Range: {club.get('ageRange') or club.get('age')}")
        
        return ". ".join(parts) if parts else ""
    
    async def answer_query(self, query: str, location_slug: str) -> Dict[str, Any]:
        """
        Answer a query using API data.
        
        Args:
            query: User query string
            location_slug: Location slug (e.g., 'tx-alamo-ranch')
            
        Returns:
            Dict[str, Any]: Answer with status and formatted text
        """
        try:
            # Import normalize function
            from app.utils.data_api_client import normalize_location_slug
            
            # Normalize location slug: remove 'cn-' prefix but keep state prefix (tx-, etc.)
            location_slug_clean = normalize_location_slug(location_slug)
            
            # Detect intent
            intent = self._detect_intent(query)
            logger.info(f"Detected intent: {intent} for query: {query}")
            
            # Fetch relevant data based on intent - only call the specific API needed
            if intent == 'camps':
                # Check if query mentions specific week/year for byweek endpoint
                import re
                year_match = re.search(r'\b(20\d{2})\b', query)
                week_match = re.search(r'\bweek\s+(\d+)\b', query, re.IGNORECASE)
                
                year = int(year_match.group(1)) if year_match else None
                week = int(week_match.group(1)) if week_match else None
                
                camps = await self.api_client.get_camps(location_slug_clean, year=year, week=week)
                if camps:
                    formatted_camps = [self._format_camp(camp) for camp in camps if self._format_camp(camp)]
                    answer = "\n\n".join(formatted_camps)
                    return {
                        "status": "success",
                        "answer": answer,
                        "data_type": "camps",
                        "count": len(camps)
                    }
                else:
                    return {
                        "status": "no_data",
                        "answer": "I couldn't find any upcoming camps for this location.",
                        "data_type": "camps",
                        "count": 0
                    }
            
            elif intent == 'events':
                # Events might be in facility data or separate endpoint
                # For now, check facility data
                facility_data = await self.api_client.get_facility_info(location_slug_clean)
                if facility_data:
                    # Check if events are in facility data
                    events = facility_data.get('events', []) or facility_data.get('upcomingEvents', [])
                    if events:
                        formatted_events = [self._format_event(event) for event in events if self._format_event(event)]
                        answer = "\n\n".join(formatted_events)
                        return {
                            "status": "success",
                            "answer": answer,
                            "data_type": "events",
                            "count": len(events)
                        }
                
                return {
                    "status": "no_data",
                    "answer": "I couldn't find any events for this location.",
                    "data_type": "events",
                    "count": 0
                }
            
            elif intent == 'clubs':
                # Clubs might be in facility data
                facility_data = await self.api_client.get_facility_info(location_slug_clean)
                if facility_data:
                    clubs = facility_data.get('clubs', [])
                    if clubs:
                        formatted_clubs = [self._format_club(club) for club in clubs if self._format_club(club)]
                        answer = "\n\n".join(formatted_clubs)
                        return {
                            "status": "success",
                            "answer": answer,
                            "data_type": "clubs",
                            "count": len(clubs)
                        }
                
                return {
                    "status": "no_data",
                    "answer": "I couldn't find any clubs for this location.",
                    "data_type": "clubs",
                    "count": 0
                }
            
            elif intent == 'programs':
                # Check if query is specifically about CREATE
                query_lower = query.lower()
                is_create_query = 'create' in query_lower
                
                # Get programs from API
                programs = await self.api_client.get_programs(location_slug_clean)
                
                if programs:
                    # If query is about CREATE, filter for CREATE program only
                    if is_create_query:
                        create_programs = [
                            prog for prog in programs 
                            if 'create' in (prog.get('name', '') or '').lower() or 
                               'create' in (prog.get('title', '') or '').lower() or
                               'create' in (prog.get('programType', '') or '').lower() or
                               'create' in (prog.get('type', '') or '').lower()
                        ]
                        if create_programs:
                            formatted_programs = [self._format_program(prog) for prog in create_programs if self._format_program(prog)]
                            answer = "\n\n".join(formatted_programs)
                            return {
                                "status": "success",
                                "answer": answer,
                                "data_type": "programs",
                                "count": len(create_programs)
                            }
                        else:
                            return {
                                "status": "no_data",
                                "answer": "I couldn't find CREATE program information for this location.",
                                "data_type": "programs",
                                "count": 0
                            }
                    else:
                        # Return all programs
                        formatted_programs = [self._format_program(prog) for prog in programs if self._format_program(prog)]
                        answer = "\n\n".join(formatted_programs)
                        return {
                            "status": "success",
                            "answer": answer,
                            "data_type": "programs",
                            "count": len(programs)
                        }
                
                return {
                    "status": "no_data",
                    "answer": "I couldn't find any programs for this location.",
                    "data_type": "programs",
                    "count": 0
                }
            
            elif intent == 'facility':
                # Get facility information
                facility_data = await self.api_client.get_facility_info(location_slug_clean)
                if facility_data:
                    # Format facility info
                    parts = []
                    if facility_data.get('name'):
                        parts.append(f"Facility: {facility_data['name']}")
                    if facility_data.get('address'):
                        parts.append(f"Address: {facility_data['address']}")
                    if facility_data.get('phone'):
                        parts.append(f"Phone: {facility_data['phone']}")
                    if facility_data.get('email'):
                        parts.append(f"Email: {facility_data['email']}")
                    if facility_data.get('description'):
                        parts.append(f"Description: {facility_data['description']}")
                    
                    if parts:
                        return {
                            "status": "success",
                            "answer": "\n".join(parts),
                            "data_type": "facility",
                            "count": 1
                        }
                
                return {
                    "status": "no_data",
                    "answer": "I couldn't find facility information for this location.",
                    "data_type": "facility",
                    "count": 0
                }
            
            # For general queries, try camps first (most common)
            camps = await self.api_client.get_camps(location_slug_clean)
            if camps:
                formatted_camps = [self._format_camp(camp) for camp in camps[:5] if self._format_camp(camp)]  # Limit to 5
                answer = "UPCOMING CAMPS:\n\n" + "\n\n".join(formatted_camps)
                return {
                    "status": "success",
                    "answer": answer,
                    "data_type": "general",
                    "count": len(camps)
                }
            
            return {
                "status": "no_data",
                "answer": "I couldn't find any data for this location. Please check the location and try again.",
                "data_type": "general",
                "count": 0
            }
                
        except Exception as e:
            logger.error(f"Error answering query with API: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "answer": f"I encountered an error processing your query: {str(e)}",
                "data_type": "error",
                "count": 0
            }

