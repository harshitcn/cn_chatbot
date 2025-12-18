"""
Dynamic web scraper that extracts all content from a website as text chunks.
No hardcoded keywords or categories - extracts everything.
"""
import logging
import re
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class DynamicScraper:
    """
    Fully dynamic web scraper that extracts all meaningful content as text chunks.
    No hardcoded keywords, categories, or logic - extracts everything from the page.
    """
    
    def __init__(self, timeout: int = 15, user_agent: Optional[str] = None):
        """
        Initialize the scraper.
        
        Args:
            timeout: Request timeout in seconds (default: 15)
            user_agent: Custom user agent string (default: standard browser)
        """
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
    
    def fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Optional[str]: HTML content or None if fetch fails
        """
        try:
            logger.info(f"Fetching HTML from: {url}")
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML string into BeautifulSoup object.
        
        Args:
            html: HTML content string
            
        Returns:
            BeautifulSoup: Parsed soup object
        """
        return BeautifulSoup(html, 'html.parser')
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """
        Remove unwanted elements from the soup (scripts, styles, nav, etc.).
        Keeps all content elements.
        """
        unwanted_tags = [
            "script", "style", "nav", "footer", "header", "form", "button",
            "input", "select", "textarea", "noscript", "iframe", "svg",
            "meta", "link", "base"
        ]
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove elements with common UI classes/IDs
        unwanted_selectors = [
            'nav', 'navigation', 'menu', 'sidebar', 'footer', 'header',
            'form', 'button', 'modal', 'popup', 'cookie', 'consent',
            'social', 'share', 'search', 'filter', 'pagination', 'breadcrumb'
        ]
        for selector in unwanted_selectors:
            for element in soup.find_all(class_=lambda x: x and selector in str(x).lower()):
                element.decompose()
            for element in soup.find_all(id=lambda x: x and selector in str(x).lower()):
                element.decompose()
    
    def _extract_text_content(self, element: Tag) -> str:
        """
        Extract clean text content from an element.
        
        Args:
            element: BeautifulSoup Tag element
            
        Returns:
            str: Clean text content
        """
        if not element:
            return ""
        text = element.get_text(separator=' ', strip=True)
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _is_meaningful_text(self, text: str, min_length: int = 20) -> bool:
        """
        Check if text is meaningful (not just UI noise).
        
        Args:
            text: Text to check
            min_length: Minimum length to consider meaningful
            
        Returns:
            bool: True if text is meaningful
        """
        if not text or len(text) < min_length:
            return False
        
        # Skip very short all-caps text (likely UI labels)
        if text.isupper() and len(text) < 50:
            return False
        
        # Skip common UI noise patterns
        ui_noise = [
            'field is required', 'required', 'submit', 'click', 'close', 'icon',
            'find location', 'change location', 'locations near you',
            'cookie', 'follow us', 'social', 'share', 'back to site',
            'hamburger', 'ninja icon', 'location icon', 'no location selected'
        ]
        text_lower = text.lower()
        if any(noise in text_lower for noise in ui_noise):
            return False
        
        return True
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract all headings (h1-h6) as chunks.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List[Dict[str, Any]]: List of heading chunks
        """
        chunks = []
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = self._extract_text_content(heading)
            if self._is_meaningful_text(text):
                chunks.append({
                    'text': text,
                    'type': 'heading',
                    'tag': heading.name,
                    'metadata': {}
                })
        return chunks
    
    def _extract_paragraphs(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract all paragraphs as chunks.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List[Dict[str, Any]]: List of paragraph chunks
        """
        chunks = []
        for para in soup.find_all('p'):
            text = self._extract_text_content(para)
            if self._is_meaningful_text(text):
                chunks.append({
                    'text': text,
                    'type': 'paragraph',
                    'metadata': {}
                })
        return chunks
    
    def _extract_list_items(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract all list items as chunks.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List[Dict[str, Any]]: List of list item chunks
        """
        chunks = []
        for li in soup.find_all('li'):
            text = self._extract_text_content(li)
            if self._is_meaningful_text(text):
                chunks.append({
                    'text': text,
                    'type': 'list_item',
                    'metadata': {}
                })
        return chunks
    
    def _extract_cards_and_sections(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract content from cards, sections, articles, and divs.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List[Dict[str, Any]]: List of card/section chunks
        """
        chunks = []
        
        # Find all potential content containers
        containers = soup.find_all(['section', 'article', 'div'], 
                                  class_=lambda x: x and isinstance(x, (list, str)))
        
        for container in containers:
            # Skip if container is too small or likely UI element
            container_text = self._extract_text_content(container)
            if not self._is_meaningful_text(container_text, min_length=30):
                continue
            
            # Try to find a title/heading within the container
            title = None
            title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if title_elem:
                title = self._extract_text_content(title_elem)
            
            # Extract main content (excluding nested containers)
            content_parts = []
            for child in container.children:
                if isinstance(child, Tag):
                    # Skip nested containers
                    if child.name in ['section', 'article', 'div']:
                        continue
                    child_text = self._extract_text_content(child)
                    if child_text and len(child_text) > 20:
                        content_parts.append(child_text)
            
            # Combine content
            if content_parts:
                combined_text = ' '.join(content_parts)
            else:
                combined_text = container_text
            
            if self._is_meaningful_text(combined_text, min_length=30):
                chunk = {
                    'text': combined_text,
                    'type': 'card_section',
                    'metadata': {}
                }
                if title:
                    chunk['metadata']['title'] = title
                chunks.append(chunk)
        
        return chunks
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract data from tables as text chunks.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List[Dict[str, Any]]: List of table chunks
        """
        chunks = []
        for table in soup.find_all('table'):
            table_data = []
            
            # Extract headers
            headers = []
            for th in table.find_all('th'):
                header_text = self._extract_text_content(th)
                if header_text:
                    headers.append(header_text)
            
            # Extract rows
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = [self._extract_text_content(cell) for cell in cells if self._extract_text_content(cell)]
                if row_data:
                    table_data.append(row_data)
            
            # Convert table to readable text
            if headers or table_data:
                table_text_parts = []
                if headers:
                    table_text_parts.append(f"Headers: {', '.join(headers)}")
                for row in table_data[:20]:  # Limit to first 20 rows
                    table_text_parts.append(f"Row: {', '.join(row)}")
                
                table_text = ' '.join(table_text_parts)
                if self._is_meaningful_text(table_text):
                    chunks.append({
                        'text': table_text,
                        'type': 'table',
                        'metadata': {'headers': headers}
                    })
        
        return chunks
    
    def _extract_all_text_chunks(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract all meaningful text chunks from the page.
        Combines headings, paragraphs, lists, cards, sections, and tables.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List[Dict[str, Any]]: List of all text chunks
        """
        all_chunks = []
        
        # Extract different types of content
        all_chunks.extend(self._extract_headings(soup))
        all_chunks.extend(self._extract_paragraphs(soup))
        all_chunks.extend(self._extract_list_items(soup))
        all_chunks.extend(self._extract_cards_and_sections(soup))
        all_chunks.extend(self._extract_tables(soup))
        
        # Remove duplicates (same text)
        seen_texts = set()
        unique_chunks = []
        for chunk in all_chunks:
            text_normalized = chunk['text'].lower().strip()
            if text_normalized not in seen_texts and len(text_normalized) > 10:
                seen_texts.add(text_normalized)
                unique_chunks.append(chunk)
        
        return unique_chunks
    
    def scrape(self, url: str) -> List[Dict[str, Any]]:
        """
        Main scraping method that extracts all content as text chunks.
        
        Args:
            url: URL to scrape
            
        Returns:
            List[Dict[str, Any]]: List of text chunks with structure:
                {
                    'text': str,  # The actual text content
                    'type': str,  # 'heading', 'paragraph', 'list_item', 'card_section', 'table'
                    'metadata': dict  # Additional metadata (e.g., title, headers)
                }
        """
        html = self.fetch_html(url)
        if not html:
            logger.error(f"Failed to fetch HTML from {url}")
            return []
        
        soup = self.parse_html(html)
        self._remove_unwanted_elements(soup)
        
        # Extract all text chunks
        chunks = self._extract_all_text_chunks(soup)
        
        logger.info(f"Successfully scraped {url}: extracted {len(chunks)} text chunks")
        
        return chunks

