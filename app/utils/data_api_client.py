"""
API-based data extraction client for Tier 3.
Replaces web scraping with direct API calls for better performance and reliability.
"""
import logging
import asyncio
import re
from typing import Dict, List, Optional, Any
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


def normalize_location_slug(location_slug: str) -> str:
    """
    Normalize location slug for API calls.
    Removes 'cn-' prefix but keeps state prefix (tx-, ca-, ny-, etc.).
    
    Args:
        location_slug: Location slug (e.g., 'cn-tx-alamo-ranch', 'tx-alamo-ranch', 'alamo-ranch')
        
    Returns:
        str: Normalized location slug with 'cn-' removed but state prefix kept
        
    Examples:
        normalize_location_slug('cn-tx-alamo-ranch') -> 'tx-alamo-ranch'
        normalize_location_slug('cn-ca-los-angeles') -> 'ca-los-angeles'
        normalize_location_slug('tx-alamo-ranch') -> 'tx-alamo-ranch' (no change)
        normalize_location_slug('alamo-ranch') -> 'alamo-ranch' (no change)
    """
    if not location_slug:
        return location_slug
    
    # Remove 'cn-' prefix if present, but keep state prefix (tx-, ca-, etc.)
    slug = location_slug.replace('cn-', '') if location_slug.startswith('cn-') else location_slug
    
    return slug


class DataAPIClient:
    """
    Client for fetching data from various APIs for Tier 3.
    Handles camps, programs, events, and other location-specific data.
    """
    
    def __init__(self):
        """Initialize the data API client with settings from environment."""
        self.settings = get_settings()
        self.timeout = 15.0  # 15 seconds timeout
        # Load from config (which loads from .env files)
        self.api_key = self.settings.data_api_key or None
        self.base_api_url = self.settings.data_api_base_url or 'https://services.codeninjas.com/api/v1'
        
        # Specific API endpoints
        self.facility_api = f"{self.base_api_url}/facility"
        self.facility_profile_api = f"{self.base_api_url}/facility/profile/slug"
        self.facility_camps_upcoming_api = f"{self.base_api_url}/facility/camps/upcoming"
        self.facility_camps_byweek_api = f"{self.base_api_url}/facility/camps"
        self.facility_programs_api = f"{self.base_api_url}/facility/programs"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def get_facility_data(self, location_slug: str) -> Optional[Dict[str, Any]]:
        """
        Get facility data from location slug using the facility API.
        
        Args:
            location_slug: Location slug (e.g., 'cn-tx-alamo-ranch', 'tx-alamo-ranch')
            
        Returns:
            Optional[Dict[str, Any]]: Facility data including facilityGUID/facilityId
        """
        if not location_slug:
            return None
        
        # Normalize location slug: remove 'cn-' prefix but keep state prefix (tx-, etc.)
        normalized_slug = normalize_location_slug(location_slug)
        
        # Use the normalized slug (with state prefix kept)
        slug = normalized_slug
        
        try:
            # Try facility/profile/slug endpoint first
            url = f"{self.facility_profile_api}/{slug}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Found facility data for location '{slug}'")
                return data
                    
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error fetching facility data from profile API for '{slug}': {str(e)}, trying facility API...")
            # Fallback to facility API
            try:
                url = f"{self.facility_api}/{slug}"
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=self._get_headers())
                    response.raise_for_status()
                    data = response.json()
                    logger.info(f"Found facility data from facility API for location '{slug}'")
                    return data
            except Exception as e2:
                logger.error(f"Error fetching facility data from facility API for '{slug}': {str(e2)}")
                return None
        except Exception as e:
            logger.error(f"Error fetching facility data for '{slug}': {str(e)}")
            return None
    
    def _extract_facility_guid(self, facility_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract facility GUID from facility data.
        
        Args:
            facility_data: Facility data dictionary
            
        Returns:
            Optional[str]: Facility GUID if found
        """
        if not facility_data:
            return None
        
        # Try different possible field names
        guid = (facility_data.get('facilityGUID') or 
                facility_data.get('facilityId') or 
                facility_data.get('id') or
                facility_data.get('guid'))
        
        if guid:
            return str(guid)
        return None
    
    async def get_camps(self, location_slug: str, year: Optional[int] = None, week: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get camps for a location.
        If year and week are provided, uses byweek endpoint, otherwise uses upcoming endpoint.
        
        Args:
            location_slug: Location slug (e.g., 'tx-alamo-ranch')
            year: Optional year for byweek endpoint
            week: Optional week number for byweek endpoint
            
        Returns:
            List[Dict[str, Any]]: List of camp data
        """
        # Get facility data first
        facility_data = await self.get_facility_data(location_slug)
        if not facility_data:
            return []
        
        facility_guid = self._extract_facility_guid(facility_data)
        if not facility_guid:
            logger.warning(f"No facility GUID found for location '{location_slug}'")
            return []
        
        try:
            # Use byweek endpoint if year and week provided, otherwise use upcoming
            if year and week:
                url = f"{self.facility_camps_byweek_api}/{facility_guid}/byweek/{year}/{week}"
            else:
                url = f"{self.facility_camps_upcoming_api}/{facility_guid}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                
                # Handle different response formats
                camps = []
                if isinstance(data, dict):
                    camps = data.get('camps', []) or data.get('data', []) or data.get('items', [])
                elif isinstance(data, list):
                    camps = data
                
                logger.info(f"Found {len(camps)} camps for location '{location_slug}'")
                return camps
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching camps for '{location_slug}': {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching camps for '{location_slug}': {str(e)}")
            return []
    
    async def get_programs(self, location_slug: str) -> List[Dict[str, Any]]:
        """
        Get programs for a location.
        
        Args:
            location_slug: Location slug (e.g., 'tx-alamo-ranch')
            
        Returns:
            List[Dict[str, Any]]: List of program data
        """
        # Get facility data first
        facility_data = await self.get_facility_data(location_slug)
        if not facility_data:
            return []
        
        facility_guid = self._extract_facility_guid(facility_data)
        if not facility_guid:
            logger.warning(f"No facility GUID found for location '{location_slug}'")
            # Fallback: try to get programs from facility data directly
            programs = facility_data.get('programs', []) or facility_data.get('availablePrograms', [])
            if programs:
                logger.info(f"Found {len(programs)} programs in facility data for location '{location_slug}'")
                return programs
            return []
        
        try:
            # Try programs API endpoint
            url = f"{self.facility_programs_api}/{facility_guid}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                
                # Handle different response formats
                programs = []
                if isinstance(data, dict):
                    programs = data.get('programs', []) or data.get('data', []) or data.get('items', [])
                elif isinstance(data, list):
                    programs = data
                
                logger.info(f"Found {len(programs)} programs for location '{location_slug}'")
                return programs
                
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error fetching programs API for '{location_slug}': {str(e)}, trying facility data...")
            # Fallback: try to get programs from facility data
            programs = facility_data.get('programs', []) or facility_data.get('availablePrograms', [])
            if programs:
                logger.info(f"Found {len(programs)} programs in facility data for location '{location_slug}'")
                return programs
            return []
        except Exception as e:
            logger.error(f"Error fetching programs for '{location_slug}': {str(e)}")
            # Fallback: try to get programs from facility data
            programs = facility_data.get('programs', []) or facility_data.get('availablePrograms', [])
            if programs:
                logger.info(f"Found {len(programs)} programs in facility data for location '{location_slug}'")
                return programs
            return []
    
    async def get_facility_info(self, location_slug: str) -> Optional[Dict[str, Any]]:
        """
        Get facility information (can include programs, events, etc. in the response).
        
        Args:
            location_slug: Location slug (e.g., 'tx-alamo-ranch')
            
        Returns:
            Optional[Dict[str, Any]]: Facility information
        """
        return await self.get_facility_data(location_slug)

