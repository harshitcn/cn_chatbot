"""
Main chatbot orchestrator for structured scraping and querying.
Coordinates scraper and query engine to provide clean, structured answers.
"""
import logging
from typing import Dict, Any, Optional

from scraper import HubSpotScraper
from query_engine import StructuredQueryEngine

logger = logging.getLogger(__name__)


class StructuredChatbot:
    """
    Main chatbot class that orchestrates structured scraping and query answering.
    Returns clean, structured JSON responses.
    """
    
    def __init__(self, base_url: Optional[str] = None, use_cache: bool = True):
        """
        Initialize the structured chatbot.
        
        Args:
            base_url: Optional base URL for scraping
            use_cache: Whether to cache scraped data (not implemented yet)
        """
        self.scraper = HubSpotScraper()
        self.query_engine = StructuredQueryEngine()
        self.base_url = base_url
        self.use_cache = use_cache
        self._cached_data: Dict[str, Dict[str, Any]] = {}
    
    def scrape_website(self, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape website and return structured data.
        
        Args:
            url: URL to scrape (uses base_url if not provided)
            
        Returns:
            Dict with structured data: 'camps', 'programs', 'additional_programs'
        """
        if not url:
            if not self.base_url:
                raise ValueError("No URL provided and base_url not set")
            url = self.base_url
        
        # Check cache
        if self.use_cache and url in self._cached_data:
            logger.info(f"Using cached data for {url}")
            return self._cached_data[url]
        
        logger.info(f"Scraping website: {url}")
        structured_data = self.scraper.scrape(url)
        
        # Cache
        if self.use_cache:
            self._cached_data[url] = structured_data
        
        return structured_data
    
    def answer_query(
        self,
        query: str,
        url: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a user query using structured data.
        
        Args:
            query: User query string
            url: Optional URL to scrape (uses base_url if not provided)
            location: Optional location string (e.g., "cn-tx-alamo-ranch")
            
        Returns:
            Dict with structured answer
        """
        try:
            # Scrape website if needed
            structured_data = self.scrape_website(url)
            
            # Extract location from location string if provided
            location_display = None
            if location:
                # Convert "cn-tx-alamo-ranch" to "TX – Alamo Ranch"
                location_parts = location.replace('cn-', '').split('-')
                if len(location_parts) >= 2:
                    state = location_parts[0].upper()
                    city_parts = location_parts[1:]
                    city = ' '.join(word.capitalize() for word in city_parts)
                    location_display = f"{state} – {city}"
                else:
                    location_display = location.replace('-', ' ').title()
            
            # Answer query using structured data
            response = self.query_engine.answer_query(query, structured_data, location_display)
            
            return response
        
        except Exception as e:
            logger.error(f"Error in answer_query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "query": query,
                "answer": {
                    "category": "error",
                    "message": f"I'm sorry, I encountered an error processing your query: {str(e)}"
                }
            }
    
    def clear_cache(self) -> None:
        """Clear cached scraped data."""
        self._cached_data.clear()
        logger.info("Cache cleared")


def answer_query(
    query: str,
    url: str,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to answer a query using the structured chatbot.
    
    Args:
        query: User query string
        url: URL to scrape
        location: Optional location string
        
    Returns:
        Dict with structured answer
        
    Example:
        >>> response = answer_query("Know more about CAMPS", 
        ...                        url="https://codeninjas-39646145.hs-sites.com/tx-alamo-ranch/",
        ...                        location="cn-tx-alamo-ranch")
        >>> print(response['answer']['items'])
    """
    chatbot = StructuredChatbot(base_url=url)
    return chatbot.answer_query(query, location=location)
