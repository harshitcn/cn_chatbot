"""
Data cleaning and normalization module for text chunks.
Removes HTML, normalizes whitespace, standardizes formatting, converts keys to snake_case.
"""
import logging
import re
from typing import List, Dict, Any
from html import unescape

logger = logging.getLogger(__name__)


class TextCleaner:
    """
    Data cleaning and normalization utility for text chunks.
    Handles HTML tag removal, whitespace normalization, and formatting standardization.
    """
    
    def __init__(self):
        """Initialize the text cleaner."""
        pass
    
    def remove_html_tags(self, text: str) -> str:
        """
        Remove HTML tags from text.
        
        Args:
            text: Text that may contain HTML tags
            
        Returns:
            str: Clean text without HTML tags
        """
        if not text:
            return ""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        text = unescape(text)
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        Args:
            text: Text with potentially irregular whitespace
            
        Returns:
            str: Text with normalized whitespace
        """
        if not text:
            return ""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        # Remove newlines and tabs
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # Final cleanup
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def clean_text(self, text: str) -> str:
        """
        Comprehensive text cleaning: remove HTML, normalize whitespace.
        
        Args:
            text: Text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        text = self.remove_html_tags(text)
        text = self.normalize_whitespace(text)
        return text
    
    def to_snake_case(self, text: str) -> str:
        """
        Convert text to snake_case.
        
        Args:
            text: Text to convert
            
        Returns:
            str: Text in snake_case
        """
        if not text:
            return ""
        # Replace spaces and hyphens with underscores
        text = re.sub(r'[\s\-]+', '_', text)
        # Remove special characters
        text = re.sub(r'[^a-zA-Z0-9_]', '', text)
        # Convert to lowercase
        text = text.lower()
        # Remove multiple underscores
        text = re.sub(r'_+', '_', text)
        # Remove leading/trailing underscores
        text = text.strip('_')
        return text
    
    def clean_dict_keys(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert all dictionary keys to snake_case.
        
        Args:
            data: Dictionary with potentially non-snake_case keys
            
        Returns:
            Dict[str, Any]: Dictionary with snake_case keys
        """
        cleaned = {}
        for key, value in data.items():
            new_key = self.to_snake_case(key)
            if isinstance(value, dict):
                cleaned[new_key] = self.clean_dict_keys(value)
            elif isinstance(value, list):
                cleaned[new_key] = [
                    self.clean_dict_keys(item) if isinstance(item, dict) else item 
                    for item in value
                ]
            else:
                cleaned[new_key] = value
        return cleaned
    
    def clean_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean a single text chunk.
        
        Args:
            chunk: Text chunk dictionary
            
        Returns:
            Dict[str, Any]: Cleaned text chunk
        """
        cleaned_chunk = {}
        
        # Clean text content
        if 'text' in chunk:
            cleaned_chunk['text'] = self.clean_text(chunk['text'])
        
        # Preserve type
        if 'type' in chunk:
            cleaned_chunk['type'] = chunk['type']
        
        # Clean metadata
        if 'metadata' in chunk and isinstance(chunk['metadata'], dict):
            cleaned_chunk['metadata'] = {}
            for key, value in chunk['metadata'].items():
                if isinstance(value, str):
                    cleaned_chunk['metadata'][self.to_snake_case(key)] = self.clean_text(value)
                else:
                    cleaned_chunk['metadata'][self.to_snake_case(key)] = value
        
        return cleaned_chunk
    
    def clean_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean and normalize all text chunks.
        
        Args:
            chunks: List of text chunk dictionaries
            
        Returns:
            List[Dict[str, Any]]: List of cleaned and normalized chunks
        """
        cleaned_chunks = []
        
        for chunk in chunks:
            cleaned_chunk = self.clean_chunk(chunk)
            
            # Only keep chunks with meaningful text
            if cleaned_chunk.get('text') and len(cleaned_chunk['text'].strip()) > 10:
                cleaned_chunks.append(cleaned_chunk)
        
        logger.info(f"Cleaned {len(chunks)} chunks, kept {len(cleaned_chunks)} meaningful chunks")
        
        return cleaned_chunks

