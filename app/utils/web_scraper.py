"""
Web scraping utility for location-based queries.
Scrapes website content when FAQ data doesn't contain the answer.
"""
import logging
from typing import Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup
from app.config import get_settings

logger = logging.getLogger(__name__)


class WebScraper:
    """
    Web scraper for fetching location-specific information.
    Scrapes website content when FAQ data doesn't contain the answer.
    """
    
    def __init__(self):
        """Initialize the web scraper with settings."""
        self.settings = get_settings()
        self.base_url = getattr(self.settings, 'scrape_base_url', None)
        self.timeout = 15.0  # 15 seconds timeout for web requests
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    def _construct_url(self, location_name: str, question: Optional[str] = None) -> Optional[str]:
        """
        Construct URL for scraping based on location name.
        
        URL patterns supported:
        1. {base_url}/locations/{location-slug}
        2. {base_url}/{location-name}
        3. {base_url}/location/{location-name}
        4. Custom pattern from settings
        
        Args:
            location_name: Name of the location
            question: Optional question for context
            
        Returns:
            Optional[str]: Constructed URL or None if base_url not configured
        """
        if not self.base_url:
            logger.warning("Scrape base URL not configured")
            return None
        
        if not location_name:
            return None
        
        # Normalize location name for URL (lowercase, replace spaces with hyphens)
        location_slug = location_name.lower().replace(' ', '-').replace(',', '')
        
        # Get URL pattern from settings or use default
        url_pattern = getattr(self.settings, 'scrape_url_pattern', '{base_url}/locations/{location}')
        
        # Replace placeholders
        url = url_pattern.replace('{base_url}', self.base_url.rstrip('/'))
        url = url.replace('{location}', location_slug)
        url = url.replace('{location_name}', location_name.replace(' ', '-'))
        url = url.replace('{location-slug}', location_slug)
        
        return url
    
    async def scrape_location(self, location_name: str, question: Optional[str] = None) -> Optional[str]:
        """
        Scrape website content for a given location.
        
        Args:
            location_name: Name of the location to scrape
            question: Optional question for context (can be used to filter content)
            
        Returns:
            Optional[str]: Scraped content as text, None if scraping fails
        """
        if not self.base_url:
            logger.warning("Web scraping not configured (base_url not set)")
            return None
        
        url = self._construct_url(location_name, question)
        if not url:
            logger.warning(f"Could not construct URL for location '{location_name}'")
            return None
        
        try:
            logger.info(f"Scraping URL: {url}")
            
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract text content
            # Try to find main content area first
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda x: x and ('content' in x.lower() or 'main' in x.lower()))
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                # Fallback to body text
                text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit text length to avoid token limits (keep first 3000 characters)
            if len(text) > 3000:
                text = text[:3000] + "..."
            
            if text and len(text) > 50:  # Ensure we have meaningful content
                logger.info(f"Successfully scraped {len(text)} characters from {url}")
                return text
            else:
                logger.warning(f"Scraped content too short or empty from {url}")
                return None
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error scraping '{url}': {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error scraping '{url}': {str(e)}")
            return None
    
    async def scrape_and_extract_answer(self, location_name: str, question: str) -> Optional[str]:
        """
        Scrape website and extract relevant answer based on the question.
        
        Args:
            location_name: Name of the location
            question: User's question
            
        Returns:
            Optional[str]: Extracted answer or scraped content, None if scraping fails
        """
        scraped_content = await self.scrape_location(location_name, question)
        
        if not scraped_content:
            return None
        
        # If we have a specific question, try to find relevant sections
        # For now, return the scraped content
        # In the future, we could use NLP to extract more relevant sections
        
        # Format the response
        answer = f"Based on information from our website about {location_name}: {scraped_content}"
        
        return answer

