"""
Web search service using DuckDuckGo (free, no API key required).
Provides web search capabilities for OpenAI function calling.
"""
import logging
from typing import List, Dict, Any
from app.config import get_settings

logger = logging.getLogger(__name__)


class WebSearchService:
    """
    Service for performing web searches using DuckDuckGo.
    Free and doesn't require API keys.
    """
    
    def __init__(self):
        """Initialize web search service with settings."""
        self.settings = get_settings()
        self.enabled = bool(self.settings.web_search_enabled)
        
        if not self.enabled:
            logger.info("Web search is disabled in settings.")
        else:
            try:
                from duckduckgo_search import DDGS
                self.ddgs = DDGS()
                logger.info("Web search service initialized with DuckDuckGo (free, no API key required)")
            except ImportError:
                logger.error("duckduckgo-search package not installed. Install with: pip install duckduckgo-search")
                self.enabled = False
                self.ddgs = None
            except Exception as e:
                logger.error(f"Error initializing DuckDuckGo search: {str(e)}")
                self.enabled = False
                self.ddgs = None
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a web search using DuckDuckGo.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 10)
            
        Returns:
            List[Dict[str, Any]]: List of search results with title, url, content, etc.
        """
        if not self.enabled or not self.ddgs:
            logger.warning("Web search is not enabled or not properly initialized")
            return []
        
        try:
            logger.info(f"Performing web search: {query[:100]}...")
            
            # Use DuckDuckGo search (synchronous, but we'll run it in executor)
            import asyncio
            
            def perform_search():
                """Perform synchronous search in thread."""
                results = []
                try:
                    # Search for text results
                    search_results = list(self.ddgs.text(
                        keywords=query,
                        max_results=max_results,
                        region='us-en',
                        safesearch='moderate'
                    ))
                    
                    for result in search_results:
                        results.append({
                            "title": result.get("title", ""),
                            "url": result.get("href", ""),
                            "content": result.get("body", ""),
                            "score": 1.0
                        })
                except Exception as e:
                    logger.warning(f"Error in DuckDuckGo text search: {str(e)}")
                
                return results
            
            # Run synchronous search in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, perform_search)
            
            # Limit results
            results = results[:max_results]
            
            logger.info(f"Web search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error performing web search: {str(e)}", exc_info=True)
            return []
    
    def format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results as a string for inclusion in LLM context.
        
        Args:
            results: List of search result dictionaries
            
        Returns:
            str: Formatted string with search results
        """
        if not results:
            return "No search results found."
        
        formatted = "Web Search Results:\n\n"
        for i, result in enumerate(results, 1):
            formatted += f"Result {i}:\n"
            formatted += f"Title: {result.get('title', 'N/A')}\n"
            if result.get('url'):
                formatted += f"URL: {result.get('url')}\n"
            formatted += f"Content: {result.get('content', 'N/A')[:500]}...\n"
            formatted += "\n"
        
        return formatted

