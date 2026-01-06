"""
Service for fetching and managing center data from APIs.
"""
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from app.config import get_settings
from app.database import get_db_session, Center
from app.utils.location_api import LocationAPIClient

logger = logging.getLogger(__name__)


class CenterService:
    """Service for fetching and managing center data."""
    
    def __init__(self):
        """Initialize the center service."""
        self.settings = get_settings()
        self.location_api_client = LocationAPIClient()
        self.timeout = 30.0  # 30 seconds timeout for fetching all centers
    
    async def fetch_all_center_slugs(self) -> List[str]:
        """
        Fetch list of all center slugs from LOCATION_SLUG_API_URL.
        
        Returns:
            List[str]: List of center slugs
        """
        if not self.settings.location_slug_api_url:
            logger.warning("LOCATION_SLUG_API_URL not configured")
            return []
        
        try:
            headers = {}
            if self.settings.location_api_key:
                headers["Authorization"] = f"Bearer {self.settings.location_api_key}"
            
            params = {}
            if self.settings.location_api_key and "?" in self.settings.location_slug_api_url:
                params["api_key"] = self.settings.location_api_key
            
            logger.info(f"Fetching center slugs from {self.settings.location_slug_api_url}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.settings.location_slug_api_url,
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
            
            # Extract slugs from response
            slugs = []
            
            if isinstance(data, list):
                # If response is a list, extract slug from each item
                for item in data:
                    if isinstance(item, dict):
                        slug = item.get("slug") or item.get("location_slug") or item.get("id")
                        if slug:
                            slugs.append(str(slug))
                    elif isinstance(item, str):
                        slugs.append(item)
            elif isinstance(data, dict):
                # If response is a dict, check common fields
                if "data" in data and isinstance(data["data"], list):
                    for item in data["data"]:
                        if isinstance(item, dict):
                            slug = item.get("slug") or item.get("location_slug") or item.get("id")
                            if slug:
                                slugs.append(str(slug))
                        elif isinstance(item, str):
                            slugs.append(item)
                elif "slugs" in data and isinstance(data["slugs"], list):
                    slugs = [str(s) for s in data["slugs"]]
                elif "results" in data and isinstance(data["results"], list):
                    for item in data["results"]:
                        if isinstance(item, dict):
                            slug = item.get("slug") or item.get("location_slug") or item.get("id")
                            if slug:
                                slugs.append(str(slug))
                        elif isinstance(item, str):
                            slugs.append(item)
                else:
                    # Try to get slug directly from dict
                    slug = data.get("slug") or data.get("location_slug")
                    if slug:
                        slugs.append(str(slug))
            
            logger.info(f"Fetched {len(slugs)} center slugs from API")
            return slugs
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching center slugs: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching center slugs: {str(e)}", exc_info=True)
            return []
    
    async def fetch_center_details(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Fetch center details using LOCATION_DATA_API_URL for a given slug.
        
        Args:
            slug: Center slug
            
        Returns:
            Optional[Dict[str, Any]]: Center details or None if failed
        """
        if not self.settings.location_data_api_url:
            logger.warning("LOCATION_DATA_API_URL not configured")
            return None
        
        try:
            # Use the location API client to get location data
            location_data = await self.location_api_client.get_location_data(slug)
            
            if location_data:
                logger.info(f"Successfully fetched details for slug: {slug}")
                return location_data
            else:
                logger.warning(f"No data returned for slug: {slug}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching center details for slug '{slug}': {str(e)}", exc_info=True)
            return None
    
    def extract_center_info(self, slug: str, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract center information from location data.
        
        Args:
            slug: Center slug
            location_data: Location data from API
            
        Returns:
            Dict[str, Any]: Extracted center information
        """
        # Extract common fields from location data
        center_info = {
            "slug": slug,
            "center_id": location_data.get("id") or location_data.get("facilityId") or location_data.get("centerId") or slug,
            "center_name": location_data.get("name") or location_data.get("centerName") or location_data.get("facilityName") or slug,
            "zip_code": location_data.get("zipCode") or location_data.get("zip_code") or location_data.get("postalCode"),
            "city": location_data.get("city") or location_data.get("cityName"),
            "state": location_data.get("state") or location_data.get("stateCode"),
            "country": location_data.get("country") or "USA",
            "radius": location_data.get("radius") or 5,
            "owner_email": location_data.get("ownerEmail") or location_data.get("owner_email") or location_data.get("email"),
            "location_data": json.dumps(location_data) if location_data else None
        }
        
        return center_info
    
    async def sync_centers_from_api(self) -> int:
        """
        Sync all centers from APIs to database.
        Fetches all slugs, then fetches details for each, and stores in database.
        In stage environment, limits to first N centers based on TEST_MODE_LIMIT_CENTERS setting.
        
        Returns:
            int: Number of centers synced
        """
        logger.info("Starting center sync from APIs...")
        
        # Fetch all center slugs
        slugs = await self.fetch_all_center_slugs()
        if not slugs:
            logger.warning("No center slugs found from API")
            return 0
        
        # Limit slugs in stage environment for testing
        original_count = len(slugs)
        if self.settings.app_env == "stage" and self.settings.test_mode_limit_centers > 0:
            slugs = slugs[:self.settings.test_mode_limit_centers]
            logger.info(f"Stage environment: Limiting sync to first {len(slugs)} centers (out of {original_count} total slugs)")
        
        logger.info(f"Processing {len(slugs)} center slugs, fetching details...")
        
        # Fetch details for each center
        synced_count = 0
        db = get_db_session()
        
        try:
            for slug in slugs:
                try:
                    # Fetch center details
                    location_data = await self.fetch_center_details(slug)
                    if not location_data:
                        logger.warning(f"Skipping slug '{slug}': no data returned")
                        continue
                    
                    # Extract center information
                    center_info = self.extract_center_info(slug, location_data)
                    
                    # Check if center already exists
                    existing_center = db.query(Center).filter(Center.slug == slug).first()
                    
                    if existing_center:
                        # Update existing center
                        for key, value in center_info.items():
                            if key != "slug":  # Don't update slug
                                setattr(existing_center, key, value)
                        existing_center.updated_at = datetime.utcnow()
                        logger.info(f"Updated center: {center_info['center_name']} (slug: {slug})")
                    else:
                        # Create new center
                        new_center = Center(**center_info)
                        db.add(new_center)
                        logger.info(f"Added new center: {center_info['center_name']} (slug: {slug})")
                    
                    synced_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing slug '{slug}': {str(e)}", exc_info=True)
                    continue
            
            # Commit all changes
            db.commit()
            logger.info(f"Successfully synced {synced_count} centers to database")
            
        except Exception as e:
            logger.error(f"Error syncing centers: {str(e)}", exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()
        
        return synced_count
    
    def get_all_active_centers(self) -> List[Center]:
        """
        Get all active centers from database.
        
        Returns:
            List[Center]: List of active centers
        """
        db = get_db_session()
        try:
            centers = db.query(Center).filter(Center.is_active == True).all()
            return centers
        finally:
            db.close()
    
    def convert_center_to_center_info(self, center: Center) -> Dict[str, Any]:
        """
        Convert database Center model to CenterInfo dict for batch API.
        
        Args:
            center: Center database model
            
        Returns:
            Dict[str, Any]: CenterInfo dict
        """
        return {
            "center_id": center.center_id,
            "center_name": center.center_name,
            "zip_code": center.zip_code,
            "city": center.city,
            "state": center.state,
            "country": center.country or "USA",
            "radius": center.radius or 5,
            "owner_email": center.owner_email
        }
    
    async def fetch_centers_from_api(self) -> List[Dict[str, Any]]:
        """
        Fetch centers directly from APIs without storing in database.
        Returns list of CenterInfo dicts ready for batch processing.
        
        Returns:
            List[Dict[str, Any]]: List of CenterInfo dicts
        """
        logger.info("Fetching centers directly from APIs (no database sync)...")
        
        # Fetch all center slugs
        slugs = await self.fetch_all_center_slugs()
        if not slugs:
            logger.warning("No center slugs found from API")
            return []
        
        # Limit slugs in stage environment for testing
        original_count = len(slugs)
        if self.settings.app_env == "stage" and self.settings.test_mode_limit_centers > 0:
            slugs = slugs[:self.settings.test_mode_limit_centers]
            logger.info(f"Stage environment: Limiting to first {len(slugs)} centers (out of {original_count} total slugs)")
        
        logger.info(f"Processing {len(slugs)} center slugs, fetching details...")
        
        # Fetch details for each center and convert to CenterInfo format
        center_infos = []
        for slug in slugs:
            try:
                # Fetch center details
                location_data = await self.fetch_center_details(slug)
                if not location_data:
                    logger.warning(f"Skipping slug '{slug}': no data returned")
                    continue
                
                # Extract center information
                center_info = self.extract_center_info(slug, location_data)
                
                # Convert to CenterInfo format (same as database model)
                center_info_dict = {
                    "center_id": center_info.get("center_id", slug),
                    "center_name": center_info.get("center_name", slug),
                    "zip_code": center_info.get("zip_code"),
                    "city": center_info.get("city"),
                    "state": center_info.get("state"),
                    "country": center_info.get("country", "USA"),
                    "radius": center_info.get("radius", 5),
                    "owner_email": center_info.get("owner_email")
                }
                
                center_infos.append(center_info_dict)
                logger.info(f"Fetched center: {center_info_dict['center_name']} (slug: {slug})")
                
            except Exception as e:
                logger.error(f"Error processing slug '{slug}': {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Successfully fetched {len(center_infos)} centers from APIs")
        return center_infos

