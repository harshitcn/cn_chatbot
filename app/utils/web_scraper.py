"""
Web scraping utility for location-based queries.
Scrapes website content when FAQ data doesn't contain the answer.
"""
import logging
import re
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
        base_url = getattr(self.settings, 'scrape_base_url', None)
        # Strip whitespace and newlines from base_url
        self.base_url = base_url.strip() if base_url else None
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
        
        # Remove "cn-" prefix if present (e.g., "cn-tx-alamo-ranch" -> "tx-alamo-ranch")
        if location_slug.startswith('cn-'):
            location_slug = location_slug[3:]  # Remove "cn-" prefix
            logger.info(f"Removed 'cn-' prefix from location slug: '{location_name}' -> '{location_slug}'")
        
        # Get URL pattern from settings or use default
        # Default pattern: {base_url}/{location-slug} (e.g., https://codeninjas-39646145.hs-sites.com/tx-alamo-ranch)
        url_pattern = getattr(self.settings, 'scrape_url_pattern', '{base_url}/{location-slug}')
        
        # Ensure base_url is clean (no trailing slashes, whitespace, or newlines)
        clean_base_url = self.base_url.rstrip('/').rstrip()
        
        # Replace placeholders
        url = url_pattern.replace('{base_url}', clean_base_url)
        url = url.replace('{location}', location_slug)
        url = url.replace('{location_name}', location_name.replace(' ', '-'))
        url = url.replace('{location-slug}', location_slug)
        
        # Final cleanup - remove any whitespace or newlines
        url = url.strip()
        
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
            
            # Remove unwanted elements (scripts, styles, navigation, forms, buttons, etc.)
            unwanted_tags = ["script", "style", "nav", "footer", "header", "form", "button", 
                           "input", "select", "textarea", "noscript", "iframe", "svg"]
            for tag in unwanted_tags:
                for element in soup.find_all(tag):
                    element.decompose()
            
            # Remove elements with common UI classes/IDs
            unwanted_selectors = [
                'nav', 'navigation', 'menu', 'sidebar', 'footer', 'header',
                'form', 'button', 'modal', 'popup', 'cookie', 'consent',
                'social', 'share', 'search', 'filter', 'pagination'
            ]
            for selector in unwanted_selectors:
                for element in soup.find_all(class_=lambda x: x and selector in str(x).lower()):
                    element.decompose()
                for element in soup.find_all(id=lambda x: x and selector in str(x).lower()):
                    element.decompose()
            
            # Extract text content from main content areas
            main_content = (soup.find('main') or 
                          soup.find('article') or 
                          soup.find('div', class_=lambda x: x and any(keyword in str(x).lower() 
                                                                      for keyword in ['content', 'main', 'body', 'page'])))
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                # Fallback to body, but remove more unwanted elements
                body = soup.find('body')
                if body:
                    # Remove common UI elements from body
                    for element in body.find_all(['div', 'section'], class_=lambda x: x and any(
                        keyword in str(x).lower() for keyword in ['nav', 'menu', 'footer', 'header', 'form', 'modal']
                    )):
                        element.decompose()
                    text = body.get_text(separator=' ', strip=True)
                else:
                    text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text - remove excessive whitespace and common UI text
            lines = []
            skip_patterns = [
                'field is required', 'required', 'submit', 'click', 'close', 'icon',
                'find location', 'change location', 'locations near you', 'enroll now',
                'learn more', 'request info', 'send question', 'your information',
                'first name', 'last name', 'email', 'phone number', 'agree to',
                'terms and conditions', 'privacy policy', 'cookie', 'follow us',
                'social', 'share', 'back to site', 'thanks!', 'got any questions'
            ]
            
            for line in text.splitlines():
                line = line.strip()
                if not line or len(line) < 3:
                    continue
                # Skip lines that are clearly UI elements
                if any(pattern in line.lower() for pattern in skip_patterns):
                    continue
                # Skip lines that are all caps and short (likely UI labels)
                if line.isupper() and len(line) < 50:
                    continue
                lines.append(line)
            
            # Join lines and clean up
            text = ' '.join(lines)
            # Remove multiple spaces
            text = re.sub(r'\s+', ' ', text)
            
            # Limit text length to avoid token limits (keep first 4000 characters)
            if len(text) > 4000:
                text = text[:4000] + "..."
            
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
    
    def _extract_relevant_content(self, content: str, question: str) -> str:
        """
        Extract and format content relevant to the user's question.
        
        Args:
            content: Scraped content
            question: User's question
        
        Returns:
            str: Formatted, relevant content
        """
        question_lower = question.lower()
        content_lower = content.lower()
        
        # Extract keywords from question
        question_words = set(word for word in question_lower.split() if len(word) > 3)
        
        # Find relevant sections based on question type
        relevant_sections = []
        sentences = content.split('. ')
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            # Check if sentence contains question keywords or related terms
            sentence_words = set(sentence_lower.split())
            common_words = question_words & sentence_words
            
            # For program-related questions
            if any(word in question_lower for word in ['program', 'offer', 'course', 'class', 'learn', 'teach']):
                if any(word in sentence_lower for word in ['program', 'create', 'jr', 'camp', 'academy', 
                                                          'ages', 'learn', 'coding', 'robotics', 'game', 
                                                          'curriculum', 'ninja', 'sensei']):
                    relevant_sections.append(sentence.strip())
            
            # For general questions, include sentences with keyword matches
            elif len(common_words) >= 1:
                relevant_sections.append(sentence.strip())
        
        # If we found relevant sections, use them; otherwise use the full content
        if relevant_sections:
            # Remove duplicates while preserving order
            seen = set()
            unique_sections = []
            for section in relevant_sections:
                if section not in seen and len(section) > 20:
                    seen.add(section)
                    unique_sections.append(section)
            
            if unique_sections:
                # Take top 5-8 most relevant sections
                formatted_content = '. '.join(unique_sections[:8])
                if not formatted_content.endswith('.'):
                    formatted_content += '.'
                return formatted_content
        
        # Fallback: return first meaningful part of content
        return content[:1500] if len(content) > 1500 else content
    
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
        
        # Extract relevant content based on the question
        relevant_content = self._extract_relevant_content(scraped_content, question)
        
        # Format the response in a user-friendly way
        # Remove location slug prefix for display
        display_location = location_name.replace('cn-', '') if location_name.startswith('cn-') else location_name
        display_location = display_location.replace('-', ' ').title()
        
        # Format based on question type
        question_lower = question.lower()
        
        # For program-related questions, format as a structured list
        if any(word in question_lower for word in ['program', 'offer', 'course', 'class', 'what do you']):
            # Try to extract program names and descriptions
            programs = []
            content_lower = relevant_content.lower()
            
            # Look for program mentions
            if 'create' in content_lower:
                programs.append("CODE NINJAS CREATE - Our best-selling program for ages 8-14")
            if 'jr' in content_lower or 'jr.' in content_lower:
                programs.append("CODE NINJAS JR - Designed for ages 5-7, no reading required")
            if 'camp' in content_lower:
                programs.append("CODE NINJAS CAMPS - Fun learning adventures for ages 5-14")
            if 'academy' in content_lower or 'academies' in content_lower:
                programs.append("CODE NINJAS ACADEMIES - Multi-week modules in Robotics, AI and more")
            
            if programs:
                answer = f"At Code Ninjas {display_location}, we offer the following programs:\n\n"
                answer += "\n".join(f"• {program}" for program in programs)
                answer += f"\n\n{relevant_content[:500]}"
            else:
                answer = f"At Code Ninjas {display_location}, we offer:\n\n{relevant_content}"
        else:
            # For other questions, use a simple format
            answer = f"At Code Ninjas {display_location}:\n\n{relevant_content}"
        
        return answer
    
    async def scrape_general_query(self, question: str) -> Optional[str]:
        """
        Scrape website for general queries (not location-specific).
        Attempts to find relevant information based on the question.
        
        Args:
            question: User's question
        
        Returns:
            Optional[str]: Extracted answer or scraped content, None if scraping fails
        """
        if not self.base_url:
            logger.warning("Web scraping not configured (base_url not set)")
            return None
        
        # Try to construct a search URL or use base URL with search
        # This is a generic implementation - can be customized based on website structure
        try:
            # Option 1: Try base URL with search path
            # Ensure base_url is clean (no trailing slashes, whitespace, or newlines)
            clean_base_url = self.base_url.rstrip('/').rstrip()
            search_urls = [
                f"{clean_base_url}/search?q={question.replace(' ', '+')}",
                f"{clean_base_url}/faq",
                f"{clean_base_url}/support",
                clean_base_url  # Fallback to base URL
            ]
            
            for url in search_urls:
                try:
                    logger.info(f"Attempting to scrape: {url}")
                    
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
                    main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda x: x and ('content' in x.lower() or 'main' in x.lower() or 'faq' in x.lower()))
                    
                    if main_content:
                        text = main_content.get_text(separator=' ', strip=True)
                    else:
                        text = soup.get_text(separator=' ', strip=True)
                    
                    # Clean up text
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    # Try to find relevant sections based on question keywords
                    question_lower = question.lower()
                    question_words = set(question_lower.split())
                    
                    # Look for paragraphs or sections that contain question keywords
                    relevant_sections = []
                    for tag in soup.find_all(['p', 'div', 'section', 'article']):
                        tag_text = tag.get_text(separator=' ', strip=True).lower()
                        if tag_text and len(tag_text) > 20:  # Meaningful content
                            tag_words = set(tag_text.split())
                            common_words = question_words & tag_words
                            if len(common_words) >= 2:  # At least 2 common words
                                relevant_sections.append(tag.get_text(separator=' ', strip=True))
                    
                    # Use relevant sections if found, otherwise use full text
                    if relevant_sections:
                        text = ' '.join(relevant_sections[:3])  # Take top 3 relevant sections
                    
                    # Limit text length
                    if len(text) > 2000:
                        text = text[:2000] + "..."
                    
                    if text and len(text) > 50:
                        logger.info(f"Successfully scraped {len(text)} characters from {url}")
                        return f"Based on information from our website: {text}"
                    
                except httpx.HTTPError as e:
                    logger.debug(f"HTTP error scraping '{url}': {str(e)}, trying next URL...")
                    continue
                except Exception as e:
                    logger.debug(f"Error scraping '{url}': {str(e)}, trying next URL...")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error in general web scraping: {str(e)}")
            return None

