"""
Fully dynamic web scraper for HubSpot pages.
Extracts ALL content as text chunks for semantic search - no hard-coded sections.
Works for any query by extracting everything and using semantic search.
"""
import logging
import re
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup, Tag, NavigableString

logger = logging.getLogger(__name__)


class DynamicScraper:
    """
    Fully dynamic scraper that extracts ALL content as chunks.
    No hard-coded selectors or section-specific logic.
    Works by extracting all text content and chunking it for semantic search.
    """
    
    def __init__(self, timeout: int = 15, user_agent: Optional[str] = None):
        """Initialize the scraper."""
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
        """Fetch HTML content from a URL."""
        try:
            logger.info(f"Fetching HTML from: {url}")
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML string into BeautifulSoup object."""
        return BeautifulSoup(html, 'html.parser')
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """
        Remove only truly non-content elements.
        Keep navigation, footer, buttons, etc. as they contain useful information.
        """
        # Remove only non-content elements
        unwanted_tags = [
            "script", "style", "noscript", "iframe", "svg",
            "meta", "link", "base"
        ]
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove control characters but keep punctuation
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        return text.strip()
    
    def _is_ui_element(self, text: str) -> bool:
        """
        Check if text is likely a UI element (button, form label, etc.) that should be filtered.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears to be a UI element
        """
        if not text:
            return True
        
        text_lower = text.lower().strip()
        
        # Common UI button/link text patterns
        ui_patterns = [
            r'^(learn more|enroll now|request info|show|click|submit|close|book|find|get started|sign up|register|view|see more|read more|continue|next|previous|back|home|menu|search|login|logout|contact|about|faq|blog|press|careers|franchising|locations|programs|partnership)$',
            r'^(first name|last name|email|phone|zip|question|message|name field|email field|phone field|zip field|question field|message field).*(required|field)',
            r'^(required|optional|field is required)',
            r'^(teams and conditions|terms and conditions|privacy policy|cookie policy)',
            r'^(us & canada|united kingdom|united states)',
            r'^(change location|find location|let us find|locations near you)',
            r'^(your information|your question|send question)',
            r'^(thanks!|thank you|success|error|loading|please wait)',
        ]
        
        for pattern in ui_patterns:
            if re.match(pattern, text_lower):
                return True
        
        # Very short text that's likely a button/link
        if len(text_lower) <= 3 and text_lower.isupper():
            return True
        
        # Text that's all uppercase and short (likely navigation)
        if len(text_lower) <= 15 and text.isupper() and not any(c.islower() for c in text):
            return True
        
        # Check if text is mostly navigation items (repeated patterns)
        navigation_keywords = ['programs', 'about', 'locations', 'partnership', 'franchising', 'blog', 'press', 'careers', 'faq', 'us & canada', 'united kingdom']
        nav_count = sum(1 for nav in navigation_keywords if nav in text_lower)
        if nav_count >= 3:  # If contains 3+ navigation keywords, likely navigation
            return True
        
        return False
    
    def _is_navigation_text(self, text: str) -> bool:
        """
        Check if text is navigation/menu text that should be filtered.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears to be navigation
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Patterns that indicate navigation text
        nav_patterns = [
            r'programs.*code ninjas.*create.*code ninjas.*academies.*code ninjas.*jr.*code ninjas.*camps',  # Program menu
            r'about.*about us.*our vision.*careers.*faq.*blog.*press.*partnership.*franchising',  # About menu
            r'us & canada.*united kingdom.*find location.*book free session',  # Location menu
            r'locations near you.*change location.*let us find',  # Location finder
        ]
        
        for pattern in nav_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # If text contains many program names in sequence (likely navigation)
        program_names = ['code ninjas create', 'code ninjas academies', 'code ninjas jr', 'code ninjas camps', 'additional programs']
        program_count = sum(1 for prog in program_names if prog in text_lower)
        if program_count >= 3:
            return True
        
        return False
    
    def _extract_text_from_element(self, element: Tag) -> str:
        """Extract clean text from an element."""
        if not element:
            return ""
        text = element.get_text(separator=' ', strip=True)
        return self._clean_text(text)
    
    def _identify_section_name(self, element: Tag) -> str:
        """
        Dynamically identify section name from element context.
        Looks for nearby headings, parent containers, or class names.
        """
        # First, look for a heading before this element (within reasonable distance)
        for heading in element.find_all_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], limit=5):
            heading_text = self._clean_text(heading.get_text())
            if heading_text and 5 <= len(heading_text) <= 100:
                return heading_text
        
        # Look for parent container with meaningful class/id
        parent = element.find_parent(['section', 'article', 'div', 'main', 'nav', 'footer', 'header'])
        max_depth = 7
        depth = 0
        
        while parent and depth < max_depth:
            # Check for meaningful class names
            classes = parent.get('class', [])
            for cls in classes:
                if isinstance(cls, str) and len(cls) > 3:
                    # Skip generic wrapper classes
                    generic_classes = {
                        'container', 'wrapper', 'content', 'main', 'body',
                        'row', 'col', 'grid', 'flex', 'section', 'div', 'hs_cos_wrapper'
                    }
                    cls_lower = cls.lower()
                    if cls_lower not in generic_classes and not cls_lower.startswith('hs_'):
                        # Extract meaningful part
                        cls_clean = cls.replace('-', ' ').replace('_', ' ').title()
                        return cls_clean
            
            # Check for meaningful id
            elem_id = parent.get('id', '')
            if elem_id and isinstance(elem_id, str) and len(elem_id) > 3:
                generic_ids = {'main', 'content', 'wrapper', 'container'}
                if elem_id.lower() not in generic_ids:
                    id_clean = elem_id.replace('-', ' ').replace('_', ' ').title()
                    return id_clean
            
            # Check for semantic tags
            if parent.name in ['nav', 'footer', 'header', 'article', 'aside']:
                return parent.name.title()
            
            parent = parent.find_parent(['section', 'article', 'div', 'main', 'nav', 'footer', 'header'])
            depth += 1
        
        return "General Content"
    
    def _split_into_chunks(
        self, 
        text: str, 
        min_chunk_size: int = 200, 
        max_chunk_size: int = 500
    ) -> List[str]:
        """
        Split text into chunks of appropriate size (200-500 characters).
        Tries to split at sentence boundaries.
        """
        if not text:
            return []
        
        text = text.strip()
        
        # If text is already within size, return as single chunk
        if len(text) <= max_chunk_size:
            if len(text) >= min_chunk_size:
                return [text]
            # If too small, return anyway (will be merged later if needed)
            return [text] if text else []
        
        chunks = []
        
        # Split by sentences (period, exclamation, question mark)
        sentences = re.split(r'([.!?]+(?:\s+|$))', text)
        
        # Recombine sentences with their punctuation
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                combined_sentences.append(sentences[i] + sentences[i + 1])
            else:
                combined_sentences.append(sentences[i])
        
        current_chunk = ""
        for sentence in combined_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if adding this sentence would exceed max size
            potential_chunk = (current_chunk + " " + sentence).strip() if current_chunk else sentence
            
            if len(potential_chunk) > max_chunk_size:
                # Current chunk is full, save it
                if len(current_chunk) >= min_chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = sentence
                else:
                    # Current chunk too small, add sentence anyway
                    current_chunk = potential_chunk
            else:
                current_chunk = potential_chunk
        
        # Add remaining chunk
        if current_chunk:
            if len(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk)
            elif chunks:
                # Merge small last chunk with previous
                chunks[-1] = (chunks[-1] + " " + current_chunk).strip()
            else:
                chunks.append(current_chunk)
        
        return chunks
    
    def _extract_all_content_elements(self, soup: BeautifulSoup) -> List[Tag]:
        """
        Extract ALL content-bearing elements from the page.
        Includes headings, paragraphs, lists, navigation, cards, footer, etc.
        """
        content_elements = []
        seen_texts = set()
        
        # Strategy 1: Extract semantic HTML elements (headings, paragraphs, lists, etc.)
        semantic_tags = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',  # Headings
            'p',  # Paragraphs
            'li',  # List items
            'td', 'th',  # Table cells
            'dd', 'dt',  # Definition lists
            'blockquote',  # Quotes
            'caption',  # Table captions
            'label',  # Form labels (may contain useful text)
            'span',  # Spans with text
            'a',  # Links (navigation, buttons, etc.)
            'button',  # Buttons
            'strong', 'b', 'em', 'i',  # Emphasis (may contain important info)
        ]
        
        for tag_name in semantic_tags:
            elements = soup.find_all(tag_name)
            for elem in elements:
                if not isinstance(elem, Tag):
                    continue
                
                text = self._extract_text_from_element(elem)
                if not text or len(text) < 5:
                    continue
                
                # Skip if we've seen this exact text
                text_hash = hashlib.md5(text.lower().encode()).hexdigest()
                if text_hash in seen_texts:
                    continue
                
                # Filter out UI elements
                if self._is_ui_element(text):
                    continue
                
                # For links and buttons, be more selective - only include if they have meaningful content
                if tag_name in ['a', 'button']:
                    # Skip very short links/buttons (likely navigation)
                    if len(text) < 5:
                        continue
                    # Skip common UI patterns
                    if self._is_ui_element(text):
                        continue
                    # Only include if it's a meaningful link/button (not just "LEARN MORE", etc.)
                    if len(text) >= 10 and not text.isupper():
                        seen_texts.add(text_hash)
                        content_elements.append(elem)
                else:
                    # For other elements, require more substantial text
                    if len(text) >= 15:  # Increased from 10 to filter more noise
                        seen_texts.add(text_hash)
                        content_elements.append(elem)
        
        # Strategy 2: Extract divs with substantial text content
        # HubSpot uses lots of nested divs
        all_divs = soup.find_all('div')
        for div in all_divs:
            if not isinstance(div, Tag):
                continue
            
            # Get direct text (not from children)
            direct_text_nodes = [
                str(child).strip() 
                for child in div.children 
                if isinstance(child, NavigableString) and child.strip()
            ]
            direct_text = ' '.join(direct_text_nodes)
            direct_text = self._clean_text(direct_text)
            
            # Get all text from this div
            all_text = self._extract_text_from_element(div)
            
            # Filter out UI elements and navigation
            if self._is_ui_element(all_text) or self._is_navigation_text(all_text):
                continue
            
            # Include if it has substantial text (50+ chars, increased from 30)
            if all_text and len(all_text) >= 50:
                # Check if this div contains semantic elements or has direct text
                has_semantic_children = div.find(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
                
                # Skip divs that are mostly navigation/UI
                # Check if it's mostly links/buttons
                links_buttons = div.find_all(['a', 'button'])
                if links_buttons and len(links_buttons) > len(div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])) * 2:
                    continue  # Too many links/buttons relative to content
                
                # Include if:
                # 1. Has semantic children (paragraphs, headings), OR
                # 2. Has substantial direct text (not just a wrapper)
                if has_semantic_children or (len(direct_text) >= 30):
                    # Skip if we've seen this text
                    text_hash = hashlib.md5(all_text.lower().encode()).hexdigest()
                    if text_hash not in seen_texts:
                        seen_texts.add(text_hash)
                        content_elements.append(div)
        
        # Strategy 3: Extract navigation and footer content (but be selective)
        # Skip most nav/footer/header as they're mostly UI elements
        # Only include if they have substantial unique content
        for nav in soup.find_all(['nav', 'footer', 'header']):
            if not isinstance(nav, Tag):
                continue
            text = self._extract_text_from_element(nav)
            # Filter out UI-heavy navigation
            if self._is_ui_element(text) or len(text) < 50:
                continue
            # Check if it's mostly links/buttons
            links_buttons = nav.find_all(['a', 'button'])
            content_elements_in_nav = nav.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
            if links_buttons and len(links_buttons) > len(content_elements_in_nav) * 3:
                continue  # Too many links relative to content
            text_hash = hashlib.md5(text.lower().encode()).hexdigest()
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                content_elements.append(nav)
        
        # Remove nested elements (if parent is already in list)
        unique_elements = []
        for elem in content_elements:
            is_nested = False
            for existing in unique_elements:
                # Check if elem is a descendant of existing
                parent = elem.find_parent()
                depth = 0
                while parent and depth < 10:
                    if parent == existing:
                        is_nested = True
                        break
                    parent = parent.find_parent()
                    depth += 1
                    if parent is None or parent.name == 'body' or parent.name == 'html':
                        break
            
            if not is_nested:
                unique_elements.append(elem)
        
        return unique_elements
    
    def _fetch_camps_from_api(self, location_slug: str) -> List[Dict[str, Any]]:
        """
        Fetch actual upcoming camps from the Code Ninjas API.
        
        Args:
            location_slug: Location slug (e.g., 'tx-alamo-ranch')
            
        Returns:
            List of camp dictionaries with structured data
        """
        camps_data = []
        
        try:
            # Step 1: Get facility profile to get facility ID
            profile_url = f"https://code-ninjas-public-api-uat.azurewebsites.net/api/v1/facility/profile/slug/{location_slug}"
            response = self.session.get(profile_url, timeout=self.timeout)
            response.raise_for_status()
            profile_data = response.json()
            facility_id = profile_data.get('facilityId')
            
            if not facility_id:
                logger.warning(f"Could not get facility ID for {location_slug}")
                return camps_data
            
            # Step 2: Get upcoming camps using facility ID
            camps_api_url = f"https://code-ninjas-public-api-uat.azurewebsites.net/api/v1/facility/camps/upcoming/{facility_id}"
            response = self.session.get(camps_api_url, timeout=self.timeout)
            response.raise_for_status()
            api_response_data = response.json()
            camps_list = api_response_data.get('camps', [])
            
            if not isinstance(camps_list, list):
                logger.warning(f"Unexpected camps API response format")
                return camps_data
            
            # Process API camps_list
            for api_camp in camps_list:
                camp_item = {
                    "name": api_camp.get("title", ""),
                    "age_range": self._extract_age_range(api_camp.get("age", "")),
                    "description": api_camp.get("description", ""),
                    "price": f"${api_camp.get('price'):.0f}" if api_camp.get('price') is not None else None,
                    "duration": None,
                    "schedule": None,
                    "dates": [],
                }
                
                # Format dates and times
                start_dt_str = api_camp.get("startDateTime")
                end_dt_str = api_camp.get("endDateTime")
                
                if start_dt_str and end_dt_str:
                    try:
                        start_dt = datetime.fromisoformat(start_dt_str.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end_dt_str.replace('Z', '+00:00'))
                        
                        camp_item["duration"] = f"{start_dt.strftime('%b %d')} - {end_dt.strftime('%b %d, %Y')}"
                        camp_item["schedule"] = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
                        camp_item["dates"] = [start_dt.strftime('%b %d, %Y'), end_dt.strftime('%b %d, %Y')]
                    except (ValueError, AttributeError) as ve:
                        logger.warning(f"Could not parse date/time for camp {camp_item['name']}: {ve}")
                
                # Remove None values
                camp_item = {k: v for k, v in camp_item.items() if v is not None and v != []}
                if camp_item.get("name"):  # Only add if has a name
                    camps_data.append(camp_item)
            
            logger.info(f"Fetched {len(camps_data)} camps from API for {location_slug}")
            
        except Exception as e:
            logger.error(f"Error fetching camps from API: {str(e)}")
        
        return camps_data
    
    def _extract_age_range(self, age_str: str) -> Optional[str]:
        """Extract age range from age string."""
        if not age_str:
            return None
        # Handle various formats like "5-7", "8+", etc.
        age_str = str(age_str).strip()
        if age_str:
            return age_str
        return None
    
    def scrape(self, url: str, location_slug: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape a URL and return ALL content as chunks.
        
        Args:
            url: URL to scrape
            location_slug: Optional location slug for API integration (e.g., 'tx-alamo-ranch')
            
        Returns:
            List of chunk dictionaries with metadata:
            {
                "chunk_id": "...",
                "url": "...",
                "section": "...",
                "text": "...",
                "metadata": {...}
            }
        """
        html = self.fetch_html(url)
        if not html:
            logger.warning(f"Could not fetch HTML from {url}")
            return []
        
        soup = self.parse_html(html)
        self._remove_unwanted_elements(soup)
        
        chunks = []
        content_elements = self._extract_all_content_elements(soup)
        
        logger.info(f"Found {len(content_elements)} content elements on {url}")
        
        for idx, element in enumerate(content_elements):
            text = self._extract_text_from_element(element)
            if not text or len(text) < 10:
                continue
            
            # Filter out UI elements
            if self._is_ui_element(text):
                continue
            
            # Identify section dynamically
            section = self._identify_section_name(element)
            
            # Split into chunks if needed (200-500 chars)
            text_chunks = self._split_into_chunks(text, min_chunk_size=200, max_chunk_size=500)
            
            # If text is too short, merge with previous chunk or keep as is
            if not text_chunks and text:
                text_chunks = [text]
            
            for chunk_idx, chunk_text in enumerate(text_chunks):
                if not chunk_text or len(chunk_text.strip()) < 20:
                    continue
                
                # Generate unique chunk ID
                chunk_id = hashlib.md5(
                    f"{url}_{idx}_{chunk_idx}_{chunk_text[:50]}".encode()
                ).hexdigest()
                
                chunk = {
                    "chunk_id": chunk_id,
                    "url": url,
                    "section": section,
                    "text": chunk_text.strip(),
                    "metadata": {
                        "element_type": element.name if isinstance(element, Tag) else "unknown",
                        "element_index": idx,
                        "chunk_index": chunk_idx,
                        "text_length": len(chunk_text),
                        "type": "text_content"
                    }
                }
                chunks.append(chunk)
        
        # Add camps data from API if location_slug is provided
        if location_slug:
            camps_data = self._fetch_camps_from_api(location_slug)
            for camp in camps_data:
                # Format camp as structured text chunk
                camp_text_parts = []
                if camp.get("name"):
                    camp_text_parts.append(f"Camp: {camp['name']}")
                if camp.get("age_range"):
                    camp_text_parts.append(f"Age Range: {camp['age_range']}")
                if camp.get("description"):
                    camp_text_parts.append(f"Description: {camp['description']}")
                if camp.get("price"):
                    camp_text_parts.append(f"Price: {camp['price']}")
                if camp.get("duration"):
                    camp_text_parts.append(f"Duration: {camp['duration']}")
                if camp.get("schedule"):
                    camp_text_parts.append(f"Schedule: {camp['schedule']}")
                
                if camp_text_parts:
                    camp_text = ". ".join(camp_text_parts)
                    chunk_id = hashlib.md5(f"camp_{location_slug}_{camp.get('name', '')}".encode()).hexdigest()
                    chunks.append({
                        "chunk_id": chunk_id,
                        "url": url,
                        "section": "UPCOMING CAMPS",
                        "text": camp_text,
                        "metadata": {
                            "element_type": "api_data",
                            "type": "camp",
                            "camp_data": camp
                        }
                    })
        
        # Deduplicate chunks (remove exact duplicates)
        seen_chunks = set()
        unique_chunks = []
        for chunk in chunks:
            text_hash = hashlib.md5(chunk["text"].lower().encode()).hexdigest()
            if text_hash not in seen_chunks:
                seen_chunks.add(text_hash)
                unique_chunks.append(chunk)
        
        logger.info(f"Extracted {len(unique_chunks)} unique chunks from {url}")
        
        # Log sample chunks for validation
        if unique_chunks:
            logger.info(f"Sample chunk 1: {unique_chunks[0].get('text', '')[:150]}...")
            logger.info(f"Sample section 1: {unique_chunks[0].get('section', 'Unknown')}")
            if len(unique_chunks) > 1:
                logger.info(f"Sample chunk 2: {unique_chunks[1].get('text', '')[:150]}...")
                logger.info(f"Sample section 2: {unique_chunks[1].get('section', 'Unknown')}")
        
        return unique_chunks
