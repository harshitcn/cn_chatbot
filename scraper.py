"""
Structured web scraper for HubSpot pages.
Extracts camps, programs, and additional programs using actual DOM structure.
"""
import logging
import re
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class HubSpotScraper:
    """
    Structured scraper for HubSpot pages.
    Uses actual DOM structure to extract camps, programs, and additional programs.
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
        """Remove unwanted elements: scripts, styles, nav, footer, header, testimonials."""
        unwanted_tags = [
            "script", "style", "nav", "footer", "header", "form", "button",
            "input", "select", "textarea", "noscript", "iframe", "svg",
            "meta", "link", "base"
        ]
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove testimonials section
        for elem in soup.find_all(string=re.compile(r'testimonial|hear from parent', re.IGNORECASE)):
            parent = elem.find_parent(['section', 'div', 'article'])
            if parent:
                parent.decompose()
        
        # Remove elements with testimonial classes
        for elem in soup.find_all(class_=lambda x: x and 'testimonial' in str(x).lower()):
            elem.decompose()
    
    def _extract_text_content(self, element: Tag) -> str:
        """Extract clean text content from an element."""
        if not element:
            return ""
        text = element.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_age_range(self, text: str) -> Optional[str]:
        """Extract age range from text."""
        patterns = [
            r'ages?\s+(\d+)\s*(?:to|-|–|—)\s*(\d+)',  # Ages 5-12, Ages 5 to 12
            r'ages?\s+(\d+)\+',  # Ages 8+
            r'ages?\s+(\d+)',  # Ages 8
            r'\((\d+)\+?\)',  # (8+)
            r'\((\d+)\s*(?:to|-|–|—)\s*(\d+)\)',  # (5-7)
            r'(\d+)\s*(?:to|-|–|—)\s*(\d+)\s*years?',  # 5-12 years
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.lastindex == 2:
                    return f"{match.group(1)}-{match.group(2)}"
                else:
                    return f"{match.group(1)}+" if '+' in match.group(0) else match.group(1)
        return None
    
    def _extract_price(self, text: str) -> Optional[str]:
        """Extract price from text."""
        match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', text)
        if match:
            return f"${match.group(1)}"
        return None
    
    def _extract_camps_from_camps_page(self, base_url: str) -> Dict[str, Any]:
        """Extract camps from the /camps page."""
        camps_url = f"{base_url.rstrip('/')}/camps"
        html = self.fetch_html(camps_url)
        if not html:
            return {"overview": {}, "camps": []}
        
        soup = self.parse_html(html)
        self._remove_unwanted_elements(soup)
        
        camps_data = {
            "overview": {
                "headline": None,
                "age_range": None,
                "summary": None
            },
            "camps": []
        }
        
        # Find main camps section - look for heading "CAMPS"
        main_section = None
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = self._extract_text_content(heading)
            if 'camp' in heading_text.lower() and heading.name == 'h1':
                # Found main camps heading
                main_section = heading.find_parent(['section', 'article', 'div'])
                if not main_section:
                    main_section = heading.parent
                
                # Extract overview
                camps_data["overview"]["headline"] = heading_text
                
                # Look for age range near heading
                age_elem = heading.find_next(string=re.compile(r'ages?\s+\d+', re.IGNORECASE))
                if age_elem:
                    age_text = age_elem.strip() if isinstance(age_elem, str) else self._extract_text_content(age_elem.parent)
                    age_range = self._extract_age_range(age_text)
                    if age_range:
                        camps_data["overview"]["age_range"] = age_range
                
                # Find summary paragraph
                para = heading.find_next('p')
                if para:
                    summary = self._extract_text_content(para)
                    if len(summary) > 50:
                        camps_data["overview"]["summary"] = summary
                        if not camps_data["overview"]["age_range"]:
                            age_range = self._extract_age_range(summary)
                            if age_range:
                                camps_data["overview"]["age_range"] = age_range
                break
        
        # Extract individual camp cards
        # Look for section with "UPCOMING CAMPS FOR YOU" or camp cards
        camps_section = None
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = self._extract_text_content(heading)
            if 'upcoming' in heading_text.lower() or 'camps for you' in heading_text.lower():
                # Find parent container
                camps_section = heading.find_parent(['section', 'article', 'div'])
                if not camps_section:
                    # Look for next sibling container
                    next_elem = heading.find_next(['section', 'article', 'div'])
                    if next_elem:
                        camps_section = next_elem
                break
        
        if camps_section:
            # Extract camp cards - they're in nested div structures
            camp_cards = []
            
            # Find all h4 headings (camp names are typically h4)
            for heading in camps_section.find_all(['h3', 'h4']):
                heading_text = self._extract_text_content(heading)
                
                # Skip section headings
                if any(word in heading_text.lower() for word in ['upcoming', 'camps for you', 'section', 'heading', 'check out']):
                    continue
                
                # This looks like a camp name
                camp_item = {
                    "name": heading_text,
                    "age_range": None,
                    "description": None,
                    "price": None,
                    "duration": None,
                    "schedule": None,
                    "location": "TX – Alamo Ranch"
                }
                
                # Find the card container - go up to find parent div that contains this camp
                card_container = heading.find_parent(['div', 'section', 'article'])
                
                # Look for age range before the heading (in previous siblings)
                prev_elem = heading.find_previous(string=re.compile(r'ages?\s+\d+', re.IGNORECASE))
                if prev_elem:
                    age_text = prev_elem.strip() if isinstance(prev_elem, str) else self._extract_text_content(prev_elem.parent)
                    age_range = self._extract_age_range(age_text)
                    if age_range:
                        camp_item["age_range"] = age_range
                
                # Also check heading text itself for age range
                if not camp_item["age_range"]:
                    age_range = self._extract_age_range(heading_text)
                    if age_range:
                        camp_item["age_range"] = age_range
                
                if card_container:
                    card_text = self._extract_text_content(card_container)
                    
                    # Extract age range from card if not found
                    if not camp_item["age_range"]:
                        age_range = self._extract_age_range(card_text)
                        if age_range:
                            camp_item["age_range"] = age_range
                    
                    # Extract price - look for $XXX pattern
                    price = self._extract_price(card_text)
                    if price:
                        camp_item["price"] = price
                    
                    # Extract description (paragraph after heading)
                    para = heading.find_next('p')
                    if para:
                        desc = self._extract_text_content(para)
                        # Filter out very short or generic descriptions
                        if len(desc) > 30 and not any(word in desc.lower() for word in ['view camp', 'enroll', 'learn more']):
                            camp_item["description"] = desc
                    
                    # Extract dates - look for patterns like "Dec 22nd - Dec 22nd"
                    date_patterns = [
                        r'([A-Z][a-z]+\s+\d+(?:st|nd|rd|th)?)\s*-\s*([A-Z][a-z]+\s+\d+(?:st|nd|rd|th)?)',
                        r'(\d{1,2}/\d{1,2})\s*-\s*(\d{1,2}/\d{1,2})',
                    ]
                    for pattern in date_patterns:
                        date_match = re.search(pattern, card_text)
                        if date_match:
                            camp_item["duration"] = f"{date_match.group(1)} - {date_match.group(2)}"
                            break
                    
                    # Extract times - look for "12:00 AM - 3:00 AM" pattern
                    time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s*-\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))', card_text)
                    if time_match:
                        camp_item["schedule"] = f"{time_match.group(1)} - {time_match.group(2)}"
                    
                    # Only add if we have at least name and some other info
                    if camp_item["name"] and len(camp_item["name"]) > 3:
                        # Remove None values
                        camp_item = {k: v for k, v in camp_item.items() if v is not None}
                        camp_cards.append(camp_item)
            
            # Remove duplicates based on name
            seen_names = set()
            unique_camps = []
            for camp in camp_cards:
                name_key = camp.get("name", "").lower()
                if name_key and name_key not in seen_names:
                    seen_names.add(name_key)
                    unique_camps.append(camp)
            
            camps_data["camps"] = unique_camps
        
        return camps_data
    
    def _extract_programs_from_main_page(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract programs section from main page."""
        programs_data = {
            "overview": {
                "headline": None,
                "summary": None
            },
            "programs": []
        }
        
        # Find "YEAR ROUND programs" section
        programs_section = None
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = self._extract_text_content(heading)
            if 'year round' in heading_text.lower() or 'program' in heading_text.lower():
                # Found programs section
                programs_section = heading.find_parent(['section', 'article', 'div'])
                if not programs_section:
                    programs_section = heading.parent
                
                programs_data["overview"]["headline"] = heading_text
                break
        
        if not programs_section:
            logger.warning("Could not find programs section")
            return programs_data
        
        # Extract individual programs (CREATE, JR, ACADEMIES)
        # Look for program cards - they have headings like "CREATE", "JR", "ACADEMIES"
        program_names = ['CREATE', 'JR', 'ACADEMIES']
        
        for heading in programs_section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = self._extract_text_content(heading)
            
            # Check if this is a program name
            if heading_text.upper() in program_names or any(name.lower() in heading_text.lower() for name in program_names):
                program_item = {
                    "name": heading_text,
                    "age_range": None,
                    "description": None
                }
                
                # Find parent container
                card_container = heading.find_parent(['div', 'section', 'article'])
                if card_container:
                    card_text = self._extract_text_content(card_container)
                    
                    # Extract age range (look for "AGES X TO Y" near heading)
                    age_elem = heading.find_previous(string=re.compile(r'ages?\s+\d+', re.IGNORECASE))
                    if not age_elem:
                        age_elem = heading.find_next(string=re.compile(r'ages?\s+\d+', re.IGNORECASE))
                    
                    if age_elem:
                        age_text = age_elem.strip() if isinstance(age_elem, str) else self._extract_text_content(age_elem.parent)
                        age_range = self._extract_age_range(age_text)
                        if age_range:
                            program_item["age_range"] = age_range
                    else:
                        # Try from card text
                        age_range = self._extract_age_range(card_text)
                        if age_range:
                            program_item["age_range"] = age_range
                    
                    # Extract description (paragraph after heading)
                    para = heading.find_next('p')
                    if para:
                        desc = self._extract_text_content(para)
                        if len(desc) > 20:
                            program_item["description"] = desc
                    
                    if program_item["name"] and (program_item["description"] or program_item["age_range"]):
                        programs_data["programs"].append(program_item)
        
        return programs_data
    
    def _extract_additional_programs_from_main_page(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract additional programs section from main page."""
        additional_data = {
            "overview": {
                "headline": None,
                "summary": None
            },
            "programs": []
        }
        
        # Find "OUR OTHER programs" section
        additional_section = None
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = self._extract_text_content(heading)
            if 'other program' in heading_text.lower() or 'additional' in heading_text.lower():
                additional_section = heading.find_parent(['section', 'article', 'div'])
                if not additional_section:
                    additional_section = heading.parent
                
                additional_data["overview"]["headline"] = heading_text
                break
        
        if not additional_section:
            logger.warning("Could not find additional programs section")
            return additional_data
        
        # Extract individual additional programs
        # Look for headings: PARENT'S NIGHT OUT, BIRTHDAY PARTIES, CLUBS, HOME SCHOOLING, AFTER SCHOOL programs
        program_keywords = ['parent', 'birthday', 'party', 'club', 'home school', 'after school']
        
        for heading in additional_section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = self._extract_text_content(heading)
            
            # Check if this is an additional program
            if any(keyword in heading_text.lower() for keyword in program_keywords):
                program_item = {
                    "name": heading_text,
                    "age_range": None,
                    "description": None
                }
                
                # Find parent container
                card_container = heading.find_parent(['div', 'section', 'article'])
                if card_container:
                    # Look for description (might be in sibling or parent)
                    para = heading.find_next('p')
                    if para:
                        desc = self._extract_text_content(para)
                        if len(desc) > 10:
                            program_item["description"] = desc
                    
                    # Extract age range if present
                    card_text = self._extract_text_content(card_container)
                    age_range = self._extract_age_range(card_text)
                    if age_range:
                        program_item["age_range"] = age_range
                    
                    if program_item["name"]:
                        additional_data["programs"].append(program_item)
        
        return additional_data
    
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Main scraping method that extracts structured data.
        
        Args:
            url: Base URL (e.g., https://codeninjas-39646145.hs-sites.com/tx-alamo-ranch/)
        
        Returns:
            Dict with keys: 'camps', 'programs', 'additional_programs'
        """
        # Extract camps from /camps page
        camps_data = self._extract_camps_from_camps_page(url)
        
        # Extract programs and additional programs from main page
        html = self.fetch_html(url)
        if not html:
            logger.error(f"Failed to fetch HTML from {url}")
            return {
                "camps": camps_data,
                "programs": {"overview": {}, "programs": []},
                "additional_programs": {"overview": {}, "programs": []}
            }
        
        soup = self.parse_html(html)
        self._remove_unwanted_elements(soup)
        
        programs_data = self._extract_programs_from_main_page(soup)
        additional_data = self._extract_additional_programs_from_main_page(soup)
        
        result = {
            "camps": camps_data,
            "programs": programs_data,
            "additional_programs": additional_data
        }
        
        total_camps = len(camps_data.get('camps', []))
        total_programs = len(programs_data.get('programs', []))
        total_additional = len(additional_data.get('programs', []))
        
        logger.info(f"Scraped {url}: "
                   f"{total_camps} camps, "
                   f"{total_programs} programs, "
                   f"{total_additional} additional programs")
        
        # Debug: print sample extracted data
        if total_camps > 0:
            logger.info(f"Sample camp: {camps_data['camps'][0]}")
        if total_programs > 0:
            logger.info(f"Sample program: {programs_data['programs'][0]}")
        if total_additional > 0:
            logger.info(f"Sample additional program: {additional_data['programs'][0]}")
        
        return result
