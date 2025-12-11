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
    
    async def get_location_slug(self, location_name: str) -> Optional[str]:
        """
        Get location slug from location name using the first API.
        
        Args:
            location_name: Name of the location (e.g., "New York", "London")
            
        Returns:
            Optional[str]: Location slug if found, None otherwise
        """
        if not self.slug_api_url:
            logger.warning("Location slug API URL not configured")
            return None
        
        if not location_name:
            return None
        
        try:
            # Prepare request
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                # Or if API key is passed as query param:
                # headers["X-API-Key"] = self.api_key
            params = {"location": location_name}
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
                
                if isinstance(data, dict):
                    # Dictionary response
                    slug = data.get("slug") or data.get("data", {}).get("slug")
                    # Also check nested structures
                    if not slug and "data" in data and isinstance(data["data"], dict):
                        slug = data["data"].get("slug")
                elif isinstance(data, list) and len(data) > 0:
                    # List response - check first item
                    first_item = data[0]
                    if isinstance(first_item, dict):
                        slug = first_item.get("slug")
                    elif isinstance(first_item, str):
                        # If list contains strings, use first one as slug
                        slug = first_item
                
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
    
    async def get_location_data(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get location-specific data using the slug from the second API.
        
        Args:
            slug: Location slug obtained from the first API
            
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
            
            # Replace {slug} placeholder in URL if present, or append slug
            url = self.location_data_api_url
            if "{slug}" in url:
                url = url.replace("{slug}", slug)
            else:
                # Append slug to URL or add as query param
                if "?" in url:
                    url = f"{url}&slug={slug}"
                else:
                    url = f"{url}?slug={slug}"
            
            params = {}
            if self.api_key and "?" in url:
                params["api_key"] = self.api_key
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=headers,
                    params=params if params else None
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
    
    async def get_location_info(self, location_name: str) -> Optional[Dict[str, Any]]:
        """
        Complete flow: Get slug from location name, then get location data.
        
        Args:
            location_name: Name of the location
            
        Returns:
            Optional[Dict[str, Any]]: Location data if found, None otherwise
        """
        slug = await self.get_location_slug(location_name)
        if not slug:
            return None
        
        location_data = await self.get_location_data(slug)
        return location_data

