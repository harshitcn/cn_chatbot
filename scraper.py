"""
Structured web scraper that extracts camps, programs, and additional programs as structured data.
Targets specific sections and avoids generic content.
"""
import logging
import re
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class StructuredScraper:
    """
    Structured web scraper that extracts camps, programs, and additional programs
    as structured Python objects, avoiding generic content.
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
        """Remove unwanted elements: scripts, styles, nav, footer, header, etc."""
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
            'social', 'share', 'search', 'filter', 'pagination', 'breadcrumb',
            'testimonial', 'review', 'quote'  # Remove testimonials
        ]
        for selector in unwanted_selectors:
            for element in soup.find_all(class_=lambda x: x and selector in str(x).lower()):
                element.decompose()
            for element in soup.find_all(id=lambda x: x and selector in str(x).lower()):
                element.decompose()
    
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
            r'ages?\s+(\d+)\s*(?:to|-|–|—)\s*(\d+)',  # Ages 5-12
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
    
    def _find_section_by_heading(self, soup: BeautifulSoup, heading_keywords: List[str]) -> Optional[Tag]:
        """
        Find a section by looking for headings containing specific keywords.
        Returns the section container that follows the heading.
        Improved to be more flexible and find sections in different structures.
        """
        # Try multiple strategies to find the section
        
        # Strategy 1: Find heading with keywords
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = self._extract_text_content(heading).lower()
            if any(keyword.lower() in heading_text for keyword in heading_keywords):
                # Find the parent container
                parent = heading.parent
                depth = 0
                while parent and parent.name not in ['section', 'article', 'div', 'body'] and depth < 5:
                    parent = parent.parent
                    depth += 1
                
                if parent and parent.name != 'body':
                    # Check if this container has substantial content
                    text = self._extract_text_content(parent)
                    if len(text) > 50:
                        return parent
                
                # Strategy 1a: Look for next sibling
                next_sibling = heading.find_next_sibling(['section', 'article', 'div'])
                if next_sibling:
                    text = self._extract_text_content(next_sibling)
                    if len(text) > 50:
                        return next_sibling
                
                # Strategy 1b: Look for next element (any tag)
                next_elem = heading.find_next(['section', 'article', 'div'])
                if next_elem and next_elem != heading:
                    text = self._extract_text_content(next_elem)
                    if len(text) > 50:
                        return next_elem
                
                # Strategy 1c: Get parent and include following siblings
                if parent and parent.name != 'body':
                    # Create a wrapper that includes parent and its following siblings
                    return parent
        
        # Strategy 2: Search by class/id containing keywords
        for keyword in heading_keywords:
            # Look for elements with class or id containing the keyword
            elements = soup.find_all(class_=lambda x: x and keyword.lower() in str(x).lower())
            elements.extend(soup.find_all(id=lambda x: x and keyword.lower() in str(x).lower()))
            
            for elem in elements:
                if elem.name in ['section', 'article', 'div']:
                    text = self._extract_text_content(elem)
                    if len(text) > 50:
                        return elem
        
        # Strategy 3: Find sections/articles/divs with substantial content containing keywords
        for container in soup.find_all(['section', 'article', 'div']):
            container_text = self._extract_text_content(container).lower()
            if len(container_text) > 100:  # Substantial content
                if any(keyword.lower() in container_text for keyword in heading_keywords):
                    # Check if it has a heading with the keyword
                    heading = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    if heading:
                        heading_text = self._extract_text_content(heading).lower()
                        if any(keyword.lower() in heading_text for keyword in heading_keywords):
                            return container
        
        return None
    
    def _extract_camps_section(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract camps section with structured data."""
        camps_data = {
            "overview": {
                "headline": None,
                "age_range": None,
                "summary": None
            },
            "camps": []
        }
        
        # Find camps section
        camps_section = self._find_section_by_heading(soup, ['camp', 'camps'])
        
        if not camps_section:
            logger.warning("Could not find camps section by heading, trying fallback method")
            # Fallback: search entire page for camp-related content
            # Look for any section/div that contains camp-related text
            for container in soup.find_all(['section', 'article', 'div']):
                container_text = self._extract_text_content(container).lower()
                if 'camp' in container_text and len(container_text) > 100:
                    # Check if it has substantial content and isn't just navigation
                    if not any(word in container_text for word in ['navigation', 'menu', 'footer', 'header']):
                        camps_section = container
                        logger.info(f"Found camps section via fallback: {container.name} with {len(container_text)} chars")
                        break
        
        if not camps_section:
            logger.warning("Could not find camps section even with fallback")
            return camps_data
        
        # Extract overview from heading and first paragraph
        heading = camps_section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if heading:
            camps_data["overview"]["headline"] = self._extract_text_content(heading)
            heading_text = self._extract_text_content(heading)
            age_range = self._extract_age_range(heading_text)
            if age_range:
                camps_data["overview"]["age_range"] = age_range
        
        # Find summary paragraph
        first_para = camps_section.find('p')
        if first_para:
            summary = self._extract_text_content(first_para)
            if len(summary) > 50:  # Meaningful summary
                camps_data["overview"]["summary"] = summary
                age_range = self._extract_age_range(summary)
                if age_range and not camps_data["overview"]["age_range"]:
                    camps_data["overview"]["age_range"] = age_range
        
        # Extract individual camp items
        # Look for list items, divs with camp names, or structured content
        camp_items = []
        
        # Method 1: List items
        for li in camps_section.find_all('li'):
            li_text = self._extract_text_content(li)
            if len(li_text) > 15:  # Lowered threshold
                camp_item = {
                    "name": None,
                    "age_range": None,
                    "description": li_text,
                    "duration": None,
                    "schedule": None,
                    "location": "TX – Alamo Ranch"
                }
                
                # Extract age range
                age_range = self._extract_age_range(li_text)
                if age_range:
                    camp_item["age_range"] = age_range
                
                # Try to extract name (text before age range or first sentence)
                if age_range:
                    name_match = re.search(r'(.+?)(?:\(|ages?|\d+)', li_text, re.IGNORECASE)
                    if name_match:
                        camp_item["name"] = name_match.group(1).strip(' .,!?;:')
                else:
                    # First sentence as name
                    first_sentence = re.split(r'[.!?]', li_text)[0]
                    if len(first_sentence) > 5 and len(first_sentence) < 150:  # Increased max length
                        camp_item["name"] = first_sentence.strip()
                
                camp_items.append(camp_item)
        
        # Method 1b: Paragraphs that might be camp items
        for para in camps_section.find_all('p'):
            para_text = self._extract_text_content(para)
            # Check if paragraph looks like a camp item (has age range or is short/structured)
            age_range = self._extract_age_range(para_text)
            if age_range or (len(para_text) > 20 and len(para_text) < 300):
                camp_item = {
                    "name": None,
                    "age_range": age_range,
                    "description": para_text,
                    "duration": None,
                    "schedule": None,
                    "location": "TX – Alamo Ranch"
                }
                
                if age_range:
                    name_match = re.search(r'(.+?)(?:\(|ages?|\d+)', para_text, re.IGNORECASE)
                    if name_match:
                        camp_item["name"] = name_match.group(1).strip(' .,!?;:')
                else:
                    first_sentence = re.split(r'[.!?]', para_text)[0]
                    if len(first_sentence) > 5 and len(first_sentence) < 100:
                        camp_item["name"] = first_sentence.strip()
                
                camp_items.append(camp_item)
        
        # Method 2: Divs/sections that look like camp cards
        for div in camps_section.find_all(['div', 'section', 'article']):
            div_text = self._extract_text_content(div)
            # More lenient size check
            if len(div_text) > 20 and len(div_text) < 800:
                # Check if it has a heading (likely a camp name)
                heading = div.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if heading:
                    heading_text = self._extract_text_content(heading)
                    # Check if this looks like a camp item (not a section heading)
                    if len(heading_text) < 150 and not any(word in heading_text.lower() for word in ['section', 'overview', 'about', 'camp', 'camps']):
                        camp_item = {
                            "name": heading_text,
                            "age_range": None,
                            "description": None,
                            "duration": None,
                            "schedule": None,
                            "location": "TX – Alamo Ranch"
                        }
                        
                        # Extract description (paragraphs in this div)
                        paras = div.find_all('p')
                        if paras:
                            descriptions = [self._extract_text_content(p) for p in paras if len(self._extract_text_content(p)) > 10]
                            if descriptions:
                                camp_item["description"] = ' '.join(descriptions)
                        else:
                            # Use div text excluding heading
                            desc_text = div_text.replace(heading_text, '').strip()
                            if desc_text and len(desc_text) > 10:
                                camp_item["description"] = desc_text
                        
                        # Extract age range
                        full_text = div_text
                        age_range = self._extract_age_range(full_text)
                        if age_range:
                            camp_item["age_range"] = age_range
                        
                        if camp_item["description"] or camp_item["name"]:
                            camp_items.append(camp_item)
        
        # Method 3: If no items found, try extracting from all text in section
        # Split by sentences/patterns that might indicate separate camps
        if not camp_items:
            section_text = self._extract_text_content(camps_section)
            # Look for patterns like "Camp Name (8+)" or "Camp Name. Description"
            # Split by patterns that indicate new items
            item_patterns = [
                r'([A-Z][^.!?]*(?:\([0-9]|ages?|\d+)[^.!?]*[.!?])',  # Text with age info ending in punctuation
                r'([A-Z][^.!?]{20,200}[.!?])',  # Substantial sentences
            ]
            
            for pattern in item_patterns:
                matches = re.finditer(pattern, section_text)
                for match in matches:
                    item_text = match.group(1).strip()
                    if len(item_text) > 20:
                        camp_item = {
                            "name": None,
                            "age_range": None,
                            "description": item_text,
                            "duration": None,
                            "schedule": None,
                            "location": "TX – Alamo Ranch"
                        }
                        
                        age_range = self._extract_age_range(item_text)
                        if age_range:
                            camp_item["age_range"] = age_range
                            name_match = re.search(r'(.+?)(?:\(|ages?|\d+)', item_text, re.IGNORECASE)
                            if name_match:
                                camp_item["name"] = name_match.group(1).strip(' .,!?;:')
                        
                        if not camp_item["name"]:
                            first_sentence = re.split(r'[.!?]', item_text)[0]
                            if len(first_sentence) > 5:
                                camp_item["name"] = first_sentence.strip()
                        
                        camp_items.append(camp_item)
                
                if camp_items:
                    break
        
        # Remove duplicates based on name
        seen_names = set()
        unique_camps = []
        for camp in camp_items:
            name_key = (camp.get("name") or "").lower()
            if name_key and name_key not in seen_names:
                seen_names.add(name_key)
                unique_camps.append(camp)
            elif not name_key:  # Keep items without names if they have descriptions
                unique_camps.append(camp)
        
        camps_data["camps"] = unique_camps
        
        return camps_data
    
    def _extract_programs_section(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract programs section with structured data."""
        programs_data = {
            "overview": {
                "headline": None,
                "summary": None
            },
            "programs": []
        }
        
        # Find programs section
        programs_section = self._find_section_by_heading(soup, ['program', 'programs', 'core program'])
        
        if not programs_section:
            logger.warning("Could not find programs section by heading, trying fallback method")
            # Fallback: search entire page
            for container in soup.find_all(['section', 'article', 'div']):
                container_text = self._extract_text_content(container).lower()
                if ('program' in container_text or 'academy' in container_text or 'create' in container_text) and len(container_text) > 100:
                    if not any(word in container_text for word in ['navigation', 'menu', 'footer', 'header', 'camp']):
                        programs_section = container
                        logger.info(f"Found programs section via fallback: {container.name}")
                        break
        
        if not programs_section:
            logger.warning("Could not find programs section even with fallback")
            return programs_data
        
        # Extract overview
        heading = programs_section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if heading:
            programs_data["overview"]["headline"] = self._extract_text_content(heading)
        
        first_para = programs_section.find('p')
        if first_para:
            summary = self._extract_text_content(first_para)
            if len(summary) > 50:
                programs_data["overview"]["summary"] = summary
        
        # Extract individual programs (similar to camps)
        program_items = []
        
        for li in programs_section.find_all('li'):
            li_text = self._extract_text_content(li)
            if len(li_text) > 20:
                program_item = {
                    "name": None,
                    "age_range": None,
                    "description": li_text
                }
                
                age_range = self._extract_age_range(li_text)
                if age_range:
                    program_item["age_range"] = age_range
                
                # Extract name
                if age_range:
                    name_match = re.search(r'(.+?)(?:\(|ages?|\d+)', li_text, re.IGNORECASE)
                    if name_match:
                        program_item["name"] = name_match.group(1).strip(' .,!?;:')
                else:
                    first_sentence = re.split(r'[.!?]', li_text)[0]
                    if len(first_sentence) > 5 and len(first_sentence) < 100:
                        program_item["name"] = first_sentence.strip()
                
                program_items.append(program_item)
        
        # Also check divs/sections
        for div in programs_section.find_all(['div', 'section', 'article']):
            div_text = self._extract_text_content(div)
            if 30 < len(div_text) < 500:
                heading = div.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if heading:
                    heading_text = self._extract_text_content(heading)
                    if len(heading_text) < 100:
                        program_item = {
                            "name": heading_text,
                            "age_range": None,
                            "description": None
                        }
                        
                        paras = div.find_all('p')
                        if paras:
                            program_item["description"] = ' '.join([self._extract_text_content(p) for p in paras])
                        else:
                            desc_text = div_text.replace(heading_text, '').strip()
                            if desc_text:
                                program_item["description"] = desc_text
                        
                        age_range = self._extract_age_range(div_text)
                        if age_range:
                            program_item["age_range"] = age_range
                        
                        if program_item["description"] or program_item["name"]:
                            program_items.append(program_item)
        
        # Remove duplicates
        seen_names = set()
        unique_programs = []
        for program in program_items:
            name_key = (program.get("name") or "").lower()
            if name_key and name_key not in seen_names:
                seen_names.add(name_key)
                unique_programs.append(program)
            elif not name_key:
                unique_programs.append(program)
        
        programs_data["programs"] = unique_programs
        
        return programs_data
    
    def _extract_additional_programs_section(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract additional/other programs section."""
        additional_data = {
            "overview": {
                "headline": None,
                "summary": None
            },
            "programs": []
        }
        
        # Find additional programs section
        additional_section = self._find_section_by_heading(
            soup, 
            ['additional', 'other program', 'parent', 'birthday', 'party', 'night out']
        )
        
        if not additional_section:
            logger.warning("Could not find additional programs section by heading, trying fallback method")
            # Fallback: search entire page
            for container in soup.find_all(['section', 'article', 'div']):
                container_text = self._extract_text_content(container).lower()
                if any(keyword in container_text for keyword in ['parent', 'birthday', 'party', 'night out', 'additional']) and len(container_text) > 100:
                    if not any(word in container_text for word in ['navigation', 'menu', 'footer', 'header']):
                        additional_section = container
                        logger.info(f"Found additional programs section via fallback: {container.name}")
                        break
        
        if not additional_section:
            logger.warning("Could not find additional programs section even with fallback")
            return additional_data
        
        # Extract overview
        heading = additional_section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if heading:
            additional_data["overview"]["headline"] = self._extract_text_content(heading)
        
        first_para = additional_section.find('p')
        if first_para:
            summary = self._extract_text_content(first_para)
            if len(summary) > 50:
                additional_data["overview"]["summary"] = summary
        
        # Extract programs (same logic as programs section)
        program_items = []
        
        for li in additional_section.find_all('li'):
            li_text = self._extract_text_content(li)
            if len(li_text) > 20:
                program_item = {
                    "name": None,
                    "age_range": None,
                    "description": li_text
                }
                
                age_range = self._extract_age_range(li_text)
                if age_range:
                    program_item["age_range"] = age_range
                
                if age_range:
                    name_match = re.search(r'(.+?)(?:\(|ages?|\d+)', li_text, re.IGNORECASE)
                    if name_match:
                        program_item["name"] = name_match.group(1).strip(' .,!?;:')
                else:
                    first_sentence = re.split(r'[.!?]', li_text)[0]
                    if len(first_sentence) > 5 and len(first_sentence) < 100:
                        program_item["name"] = first_sentence.strip()
                
                program_items.append(program_item)
        
        for div in additional_section.find_all(['div', 'section', 'article']):
            div_text = self._extract_text_content(div)
            if 30 < len(div_text) < 500:
                heading = div.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if heading:
                    heading_text = self._extract_text_content(heading)
                    if len(heading_text) < 100:
                        program_item = {
                            "name": heading_text,
                            "age_range": None,
                            "description": None
                        }
                        
                        paras = div.find_all('p')
                        if paras:
                            program_item["description"] = ' '.join([self._extract_text_content(p) for p in paras])
                        else:
                            desc_text = div_text.replace(heading_text, '').strip()
                            if desc_text:
                                program_item["description"] = desc_text
                        
                        age_range = self._extract_age_range(div_text)
                        if age_range:
                            program_item["age_range"] = age_range
                        
                        if program_item["description"] or program_item["name"]:
                            program_items.append(program_item)
        
        # Remove duplicates
        seen_names = set()
        unique_programs = []
        for program in program_items:
            name_key = (program.get("name") or "").lower()
            if name_key and name_key not in seen_names:
                seen_names.add(name_key)
                unique_programs.append(program)
            elif not name_key:
                unique_programs.append(program)
        
        additional_data["programs"] = unique_programs
        
        return additional_data
    
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Main scraping method that extracts structured data.
        
        Returns:
            Dict with keys: 'camps', 'programs', 'additional_programs'
        """
        html = self.fetch_html(url)
        if not html:
            logger.error(f"Failed to fetch HTML from {url}")
            return {
                "camps": {"overview": {}, "camps": []},
                "programs": {"overview": {}, "programs": []},
                "additional_programs": {"overview": {}, "programs": []}
            }
        
        soup = self.parse_html(html)
        self._remove_unwanted_elements(soup)
        
        # Extract structured data for each category
        camps_data = self._extract_camps_section(soup)
        programs_data = self._extract_programs_section(soup)
        additional_data = self._extract_additional_programs_section(soup)
        
        result = {
            "camps": camps_data,
            "programs": programs_data,
            "additional_programs": additional_data
        }
        
        total_camps = len(camps_data['camps'])
        total_programs = len(programs_data['programs'])
        total_additional = len(additional_data['programs'])
        
        logger.info(f"Scraped {url}: "
                   f"{total_camps} camps, "
                   f"{total_programs} programs, "
                   f"{total_additional} additional programs")
        
        # Debug: log if we found sections but no items
        if total_camps == 0:
            logger.warning("Found camps section but extracted 0 camp items - may need to adjust extraction logic")
        if total_programs == 0:
            logger.warning("Found programs section but extracted 0 program items - may need to adjust extraction logic")
        if total_additional == 0:
            logger.warning("Found additional programs section but extracted 0 items - may need to adjust extraction logic")
        
        return result
