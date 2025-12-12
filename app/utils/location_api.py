"""
Location API clients.
Handles API calls to fetch location slug and location data.
"""
import logging
from typing import Optional, Dict, Any
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


class LocationAPIClient:
    """
    Client for location APIs.
    Handles fetching location slug and location-specific data.
    """
    
    def __init__(self):
        """Initialize the location API client with settings."""
        self.settings = get_settings()
        self.slug_api_url = getattr(self.settings, 'location_slug_api_url', None)
        self.location_data_api_url = getattr(self.settings, 'location_data_api_url', None)
        self.api_key = getattr(self.settings, 'location_api_key', None)
        self.timeout = 10.0  # 10 seconds timeout
    
    async def get_location_slug(self, location_name: str, question: Optional[str] = None) -> Optional[str]:
        """
        Get location slug from location name using the first API.
        Optionally includes the full question/prompt for better context.
        
        Args:
            location_name: Name of the location (e.g., "New York", "London")
            question: Optional full question/prompt from the user
            
        Returns:
            Optional[str]: Location slug if found, None otherwise
        """
        if not self.slug_api_url:
            logger.warning("Location slug API URL not configured")
            return None
        
        if not location_name:
            return None
        
        try:
            # Prepare request - Use GET method for slug API
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                # Or if API key is passed as query param:
                # headers["X-API-Key"] = self.api_key
            
            # Use GET with query params
            params = {"location": location_name}
            # Include question/prompt if provided
            if question:
                params["question"] = question
                params["query"] = question  # Some APIs might use "query" instead
            if self.api_key and "?" in self.slug_api_url:
                # If API key should be in query params
                params["api_key"] = self.api_key
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.slug_api_url,
                    headers=headers,
                    params=params
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract slug from response
            # Handle both dict and list responses
            slug = None
            
            # Normalize location name to Camel Case (Title Case) for matching
            # "alamo ranch" -> "Alamo Ranch", "ALAMO RANCH" -> "Alamo Ranch"
            location_name_normalized = ' '.join(word.capitalize() for word in location_name.split())
            location_name_lower = location_name_normalized.lower()
            
            def normalize_name(name_str: str) -> str:
                """Normalize a name string to Camel Case for comparison."""
                if not name_str:
                    return ""
                return ' '.join(word.capitalize() for word in str(name_str).split())
            
            if isinstance(data, dict):
                # Dictionary response - check if name matches
                api_name = data.get("name", "")
                if api_name:
                    api_name_normalized = normalize_name(api_name)
                    # Check for exact match in Camel Case
                    if api_name_normalized == location_name_normalized or api_name_normalized.lower() == location_name_lower:
                        slug = data.get("slug")
                
                # Also check nested structures
                if not slug:
                    slug = data.get("slug") or data.get("data", {}).get("slug")
                if not slug and "data" in data and isinstance(data["data"], dict):
                    data_obj = data["data"]
                    api_name = data_obj.get("name", "")
                    if api_name:
                        api_name_normalized = normalize_name(api_name)
                        if api_name_normalized == location_name_normalized or api_name_normalized.lower() == location_name_lower:
                            slug = data_obj.get("slug")
                    if not slug:
                        slug = data_obj.get("slug")
            elif isinstance(data, list) and len(data) > 0:
                # List response - search for exact matching location name in "name" field
                for item in data:
                    if isinstance(item, dict):
                        # Check if the "name" field matches the location name (in Camel Case)
                        item_name = item.get("name", "")
                        if item_name:
                            item_name_normalized = normalize_name(item_name)
                            # Exact match in Camel Case or case-insensitive match
                            if (item_name_normalized == location_name_normalized or 
                                item_name_normalized.lower() == location_name_lower):
                                slug = item.get("slug")
                                if slug:
                                    logger.info(f"Matched location name '{item_name_normalized}' with '{location_name_normalized}', found slug: {slug}")
                                    break
                    elif isinstance(item, str):
                        # If list contains strings, normalize and compare
                        item_normalized = normalize_name(item)
                        if item_normalized == location_name_normalized or item_normalized.lower() == location_name_lower:
                            slug = item
                            logger.info(f"Matched location string '{item_normalized}' with '{location_name_normalized}', using as slug: {slug}")
                            break
                
                # Don't use fallback - only return slug if we found an exact match
                if not slug:
                    logger.warning(f"No exact match found for location '{location_name_normalized}' in API response. Available names: {[normalize_name(item.get('name', '')) if isinstance(item, dict) else normalize_name(str(item)) for item in data[:5]]}")
            
            if slug:
                logger.info(f"Found slug '{slug}' for location '{location_name}'")
                return slug
            else:
                logger.warning(f"No slug found in API response for '{location_name}'. Response type: {type(data).__name__}")
                return None
                    
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching location slug for '{location_name}': {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching location slug for '{location_name}': {str(e)}")
            return None
    
    async def get_location_data(self, slug: str, question: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get location-specific data using the slug from the second API.
        Optionally includes the full question/prompt for better context.
        
        Args:
            slug: Location slug obtained from the first API
            question: Optional full question/prompt from the user
            
        Returns:
            Optional[Dict[str, Any]]: Location data if found, None otherwise
        """
        if not self.location_data_api_url:
            logger.warning("Location data API URL not configured")
            return None
        
        if not slug:
            return None
        
        try:
            # Prepare request
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                # Or if API key is passed as query param:
                # headers["X-API-Key"] = self.api_key
            
            # Construct URL with /slug/{slug} format
            # Check if base URL already ends with /slug to avoid duplication
            url = self.location_data_api_url.rstrip('/')  # Remove trailing slash
            url_lower = url.lower()
            
            # If URL already ends with /slug, just append /{slug}
            # Otherwise, append /slug/{slug}
            if url_lower.endswith('/slug'):
                url = f"{url}/{slug}"
            else:
                url = f"{url}/slug/{slug}"
            
            # Use GET request for location data API - only pass slug, no question parameter
            params = None
            if self.api_key and "?" in url:
                params = {"api_key": self.api_key}
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=headers,
                    params=params
                )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Successfully fetched location data for slug '{slug}'")
            return data
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching location data for slug '{slug}': {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching location data for slug '{slug}': {str(e)}")
            return None
    
    async def get_location_info(self, location_name: str, question: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Complete flow: Get slug from location name (with question context), 
        then get location data using the slug (with question context).
        
        Args:
            location_name: Name of the location
            question: Optional full question/prompt from the user
            
        Returns:
            Optional[Dict[str, Any]]: Location data if found, None otherwise
        """
        logger.info(f"Fetching location slug for '{location_name}' with question context")
        slug = await self.get_location_slug(location_name, question)
        if not slug:
            logger.warning(f"No slug found for location '{location_name}'")
            return None
        
        logger.info(f"Found slug '{slug}', now fetching location data with question context")
        location_data = await self.get_location_data(slug, question)
        return location_data

