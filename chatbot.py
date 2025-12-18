"""
Main chatbot orchestrator for dynamic scraping and semantic search.
Coordinates scraper and query engine to provide answers for any query.
"""
import logging
from typing import Dict, Any, Optional, List

from scraper import DynamicScraper
from query_engine import DynamicQueryEngine
from embeddings import load_or_build_vector_store

logger = logging.getLogger(__name__)


class DynamicChatbot:
    """
    Fully dynamic chatbot using semantic search.
    Works for any query without hard-coded categories.
    """
    
    def __init__(self, base_url: Optional[str] = None, use_cache: bool = True):
        """
        Initialize the dynamic chatbot.
        
        Args:
            base_url: Optional base URL for scraping
            use_cache: Whether to cache scraped chunks and vector store
        """
        self.scraper = DynamicScraper()
        self.query_engine: Optional[DynamicQueryEngine] = None
        self.base_url = base_url
        self.use_cache = use_cache
        self._cached_chunks: Dict[str, List[Dict[str, Any]]] = {}
        self._current_url: Optional[str] = None
        self._current_chunks: List[Dict[str, Any]] = []
    
    def scrape_website(self, url: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape website and return all content as chunks.
        
        Args:
            url: URL to scrape (uses base_url if not provided)
            
        Returns:
            List of chunk dictionaries
        """
        if not url:
            if not self.base_url:
                raise ValueError("No URL provided and base_url not set")
            url = self.base_url
        
        # Check cache
        if self.use_cache and url in self._cached_chunks:
            logger.info(f"Using cached chunks for {url}")
            chunks = self._cached_chunks[url]
            self._current_url = url
            self._current_chunks = chunks
            return chunks
        
        logger.info(f"Scraping website: {url}")
        chunks = self.scraper.scrape(url)
        
        # Cache
        if self.use_cache:
            self._cached_chunks[url] = chunks
        
        self._current_url = url
        self._current_chunks = chunks
        
        logger.info(f"Scraped {len(chunks)} chunks from {url}")
        return chunks
    
    def _ensure_vector_store(self) -> None:
        """Ensure vector store is built for current chunks."""
        if not self._current_chunks:
            raise ValueError("No chunks available. Call scrape_website() first.")
        
        if self.query_engine is None or self.query_engine.vector_store is None:
            logger.info("Building vector store from chunks...")
            self.query_engine = DynamicQueryEngine(chunks=self._current_chunks)
            logger.info(f"Vector store built with {len(self._current_chunks)} chunks")
    
    def answer_query(
        self,
        query: str,
        url: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a user query using semantic search.
        
        Args:
            query: User query string
            url: Optional URL to scrape (uses base_url if not provided)
            location: Optional location string (for display purposes)
            
        Returns:
            Dict with answer and sources
        """
        try:
            # Scrape website if needed or if URL changed
            if url and url != self._current_url:
                self.scrape_website(url)
            elif not self._current_chunks:
                self.scrape_website(url)
            
            # Ensure vector store is built
            self._ensure_vector_store()
            
            # Answer query using semantic search
            response = self.query_engine.answer_query(query, top_k=5)
            
            # Add location info if provided
            if location and response.get("status") == "success":
                # Format location for display
                location_display = self._format_location(location)
                if location_display:
                    response["location"] = location_display
            
            return response
        
        except Exception as e:
            logger.error(f"Error in answer_query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "query": query,
                "answer": f"I'm sorry, I encountered an error processing your query: {str(e)}",
                "sources": []
            }
    
    def _format_location(self, location: str) -> str:
        """Format location string for display."""
        if not location:
            return None
        
        # Convert "cn-tx-alamo-ranch" to "TX – Alamo Ranch"
        location_clean = location.replace('cn-', '')
        parts = location_clean.split('-')
        
        if len(parts) >= 2:
            state = parts[0].upper()
            city_parts = parts[1:]
            city = ' '.join(word.capitalize() for word in city_parts)
            return f"{state} – {city}"
        else:
            return location.replace('-', ' ').title()
    
    def clear_cache(self) -> None:
        """Clear cached scraped data."""
        self._cached_chunks.clear()
        self._current_chunks = []
        self._current_url = None
        self.query_engine = None
        logger.info("Cache cleared")
    
    def get_chunk_stats(self) -> Dict[str, Any]:
        """Get statistics about scraped chunks."""
        if not self._current_chunks:
            return {"total_chunks": 0, "sections": {}}
        
        sections = {}
        for chunk in self._current_chunks:
            section = chunk.get("section", "Unknown")
            sections[section] = sections.get(section, 0) + 1
        
        return {
            "total_chunks": len(self._current_chunks),
            "sections": sections,
            "url": self._current_url
        }


def answer_query(
    query: str,
    url: str,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to answer a query using the dynamic chatbot.
    
    Args:
        query: User query string
        url: URL to scrape
        location: Optional location string
        
    Returns:
        Dict with answer and sources
        
    Example:
        >>> response = answer_query("Know more about camps", 
        ...                        url="https://codeninjas-39646145.hs-sites.com/tx-alamo-ranch/",
        ...                        location="cn-tx-alamo-ranch")
        >>> print(response['answer'])
    """
    chatbot = DynamicChatbot(base_url=url)
    return chatbot.answer_query(query, location=location)
