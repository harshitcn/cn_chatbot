"""
Main chatbot orchestrator that coordinates scraper, cleaner, embeddings, and query engine.
This is the main interface for the dynamic scraping chatbot system.
"""
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from scraper import DynamicScraper
from cleaner import TextCleaner
from embeddings import load_or_build_vector_store, get_embeddings
from query_engine import DynamicQueryEngine

from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)


class DynamicChatbot:
    """
    Main chatbot class that orchestrates scraping, cleaning, embedding, and query answering.
    Fully dynamic - no hardcoded keywords or categories.
    """
    
    def __init__(
        self, 
        base_url: Optional[str] = None,
        vector_store_path: Optional[str] = None,
        use_cache: bool = True
    ):
        """
        Initialize the dynamic chatbot.
        
        Args:
            base_url: Optional base URL for scraping
            vector_store_path: Optional path to save/load vector store
            use_cache: Whether to use cached vector store if available
        """
        self.scraper = DynamicScraper()
        self.cleaner = TextCleaner()
        self.base_url = base_url
        self.vector_store_path = vector_store_path
        self.use_cache = use_cache
        self._vector_store: Optional[FAISS] = None
        self._chunks: List[Dict[str, Any]] = []
        self._query_engine: Optional[DynamicQueryEngine] = None
    
    def scrape_and_prepare(self, url: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape website, clean chunks, and prepare vector store.
        
        Args:
            url: URL to scrape (uses base_url if not provided)
            
        Returns:
            List[Dict[str, Any]]: List of cleaned text chunks
        """
        # Determine URL
        if not url:
            if not self.base_url:
                raise ValueError("No URL provided and base_url not set")
            url = self.base_url
        
        logger.info(f"Scraping website: {url}")
        
        # Scrape
        raw_chunks = self.scraper.scrape(url)
        
        if not raw_chunks:
            logger.warning(f"No chunks extracted from {url}")
            return []
        
        # Clean chunks
        cleaned_chunks = self.cleaner.clean_chunks(raw_chunks)
        
        self._chunks = cleaned_chunks
        
        logger.info(f"Prepared {len(cleaned_chunks)} cleaned chunks")
        
        return cleaned_chunks
    
    def build_vector_store(self, chunks: Optional[List[Dict[str, Any]]] = None) -> FAISS:
        """
        Build or load vector store from chunks.
        
        Args:
            chunks: Optional list of chunks (uses self._chunks if not provided)
            
        Returns:
            FAISS: Vector store
        """
        if chunks is None:
            chunks = self._chunks
        
        if not chunks:
            raise ValueError("No chunks available. Call scrape_and_prepare() first.")
        
        logger.info(f"Building vector store from {len(chunks)} chunks")
        
        # Load or build vector store
        self._vector_store = load_or_build_vector_store(
            chunks,
            vector_store_path=self.vector_store_path if self.use_cache else None
        )
        
        # Initialize query engine
        self._query_engine = DynamicQueryEngine(
            vector_store=self._vector_store,
            embeddings=get_embeddings()
        )
        
        return self._vector_store
    
    def answer_query(
        self, 
        query: str,
        url: Optional[str] = None,
        top_k: int = 15,  # Increased for more comprehensive answers
        similarity_threshold: float = 0.2  # Lower threshold to get more matches
    ) -> Dict[str, Any]:
        """
        Answer a user query by scraping (if needed) and using semantic search.
        
        Args:
            query: User query string
            url: Optional URL to scrape (uses base_url if not provided)
            top_k: Number of top chunks to retrieve
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            Dict[str, Any]: Structured response with answer
        """
        try:
            # Scrape and prepare if needed
            if not self._chunks or url:
                self.scrape_and_prepare(url)
            
            # Build vector store if needed
            if not self._vector_store or not self._query_engine:
                self.build_vector_store()
            
            # Answer query using semantic search
            response = self._query_engine.answer_query(
                query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error in answer_query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "query": query,
                "chunks": [],
                "formatted": f"I'm sorry, I encountered an error processing your query: {str(e)}"
            }
    
    def get_chunks(self) -> List[Dict[str, Any]]:
        """
        Get the current list of chunks.
        
        Returns:
            List[Dict[str, Any]]: List of text chunks
        """
        return self._chunks
    
    def clear_cache(self) -> None:
        """Clear cached vector store and chunks."""
        self._vector_store = None
        self._chunks = []
        self._query_engine = None
        logger.info("Cache cleared")


def answer_query(
    query: str, 
    url: str,
    vector_store_path: Optional[str] = None,
    top_k: int = 5,
    similarity_threshold: float = 0.3
) -> Dict[str, Any]:
    """
    Convenience function to answer a query using the dynamic chatbot.
    
    Args:
        query: User query string
        url: URL to scrape
        vector_store_path: Optional path to save/load vector store
        top_k: Number of top chunks to retrieve
        similarity_threshold: Minimum similarity score (0-1)
        
    Returns:
        Dict[str, Any]: Structured response with answer
        
    Example:
        >>> response = answer_query("What camps do you offer?", url="https://example.com")
        >>> print(response['formatted'])
    """
    chatbot = DynamicChatbot(base_url=url, vector_store_path=vector_store_path)
    return chatbot.answer_query(query, top_k=top_k, similarity_threshold=similarity_threshold)

