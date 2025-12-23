"""
Event parser for extracting structured event data from LLM responses.
Handles various table formats (markdown, plaintext, etc.)
"""
import logging
import re
from typing import List, Optional
from app.models import EventItem

logger = logging.getLogger(__name__)


class EventParser:
    """
    Parser for extracting event data from LLM responses.
    Handles markdown tables, plaintext tables, and various formats.
    """
    
    def __init__(self):
        """Initialize the event parser."""
        self.expected_columns = [
            "event name", "event date", "website", "url", "location",
            "organizer", "contact", "fees", "notes"
        ]
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing extra whitespace."""
        return " ".join(text.split()).strip()
    
    def _extract_markdown_table(self, text: str) -> List[List[str]]:
        """Extract rows from markdown table format. Very permissive - keeps all rows."""
        rows = []
        lines = text.split("\n")
        in_table = False
        
        for line in lines:
            line = line.strip()
            # Check for markdown table separator (|---|---|)
            if re.match(r'^[\|\s\-\:]+$', line):
                in_table = True
                continue
            
            if in_table and line.startswith("|"):
                # Remove leading/trailing pipes and split
                # Keep ALL cells, even empty ones
                cells = [cell.strip() if cell else "" for cell in line.split("|")[1:-1]]
                # Accept all rows, even if all cells are empty
                rows.append(cells)
        
        return rows
    
    def _extract_plaintext_table(self, text: str) -> List[List[str]]:
        """Extract rows from plaintext table format. Very permissive - keeps all rows."""
        rows = []
        lines = text.split("\n")
        
        for line in lines:
            line = line.strip()
            # Be very permissive - only skip completely empty lines
            if not line:
                continue
            
            # Try to detect tab-separated or multiple-space-separated columns
            if "\t" in line:
                # Keep ALL cells, even empty ones
                cells = [cell.strip() if cell else "" for cell in line.split("\t")]
            else:
                # Try to split on multiple spaces (but preserve single spaces within cells)
                # Keep all cells, even empty ones
                split_cells = re.split(r'\s{2,}', line)
                cells = [c.strip() if c else "" for c in split_cells]
            
            # Accept ALL rows, even if empty (will be handled during parsing)
            rows.append(cells)
        
        return rows
    
    def _find_table_in_text(self, text: str) -> Optional[List[List[str]]]:
        """Find and extract table from text, trying multiple formats."""
        # Try markdown table first
        markdown_table = self._extract_markdown_table(text)
        if markdown_table and len(markdown_table) > 1:  # Has header + at least one row
            logger.info(f"Found markdown table with {len(markdown_table)} rows")
            return markdown_table
        
        # Try plaintext table
        plaintext_table = self._extract_plaintext_table(text)
        if plaintext_table and len(plaintext_table) > 1:
            logger.info(f"Found plaintext table with {len(plaintext_table)} rows")
            return plaintext_table
        
        # Try to find table-like structure with headers
        lines = text.split("\n")
        header_line = None
        header_idx = -1
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            # Look for header row with expected column names
            if any(col in line_lower for col in self.expected_columns):
                header_line = line
                header_idx = i
                break
        
        if header_line is not None:
            # Extract rows after header
            rows = []
            for line in lines[header_idx + 1:]:
                line = line.strip()
                # Be very permissive - only skip completely empty lines
                if not line:
                    continue
                
                # Try to parse as table row - keep ALL cells, even empty ones
                if "\t" in line:
                    cells = [cell.strip() if cell else "" for cell in line.split("\t")]
                elif "|" in line:
                    # Handle markdown-style pipe tables
                    cells = [cell.strip() if cell else "" for cell in line.split("|")]
                    # Remove empty first/last cells if pipe table (but keep empty middle cells)
                    if cells and not cells[0]:
                        cells = cells[1:]
                    if cells and not cells[-1]:
                        cells = cells[:-1]
                else:
                    # Try regex to split on multiple spaces (2 or more)
                    split_cells = re.split(r'\s{2,}', line)
                    cells = [c.strip() if c else "" for c in split_cells]
                
                # Accept ALL rows, even if all cells are empty (will be handled during parsing)
                rows.append(cells)
                logger.debug(f"Added row with {len(cells)} cells: {cells[0][:50] if cells and cells[0] else 'empty'}...")
            
            if rows:
                logger.info(f"Found table with header, extracted {len(rows)} rows")
                return rows
        
        # Last attempt: look for numbered or bulleted lists that might be events
        numbered_rows = []
        for line in lines:
            line = line.strip()
            # Look for lines starting with numbers or bullets (could be event listings)
            if re.match(r'^(\d+[\.\)]\s+|[-*•]\s+)', line):
                # Try to extract event info from this line
                content = re.sub(r'^(\d+[\.\)]\s+|[-*•]\s+)', '', line)
                if len(content) > 10:  # Meaningful content
                    # Try to split on common delimiters
                    parts = re.split(r'\s*[,;]\s*|\s+-\s+', content, maxsplit=3)
                    if len(parts) >= 1:
                        numbered_rows.append(parts)
        
        if numbered_rows and len(numbered_rows) >= 1:
            logger.info(f"Found {len(numbered_rows)} potential event entries in numbered/bullet format")
            return numbered_rows
        
        return None
    
    def _parse_row_to_event(self, row: List[str], header: Optional[List[str]] = None) -> Optional[EventItem]:
        """
        Parse a table row into an EventItem.
        Very permissive - accepts any row with at least one cell.
        
        Args:
            row: List of cell values
            header: Optional header row to map columns
            
        Returns:
            Optional[EventItem]: Parsed event or None only if completely empty
        """
        if not row or len(row) == 0:
            logger.debug("Skipping completely empty row")
            return None
        
        # Normalize row cells - keep all cells, even empty ones (will be None)
        normalized_row = []
        for cell in row:
            if cell is None:
                normalized_row.append("")
            else:
                normalized = self._normalize_text(str(cell))
                normalized_row.append(normalized)  # Keep even if empty string
        
        if not normalized_row:
            logger.debug(f"Skipping row with no cells: {row}")
            return None
        
        row = normalized_row
        logger.debug(f"Parsing row with {len(row)} cells: {row[:3]}...")  # Log first 3 cells
        
        if header:
            # Map columns by header - match each header cell accurately
            event_data = {}
            logger.debug(f"Header cells: {header}")
            logger.debug(f"Row cells: {row}")
            
            for i, header_cell in enumerate(header):
                if i < len(row):
                    header_lower = str(header_cell).lower().strip()
                    value = row[i] if i < len(row) else ""
                    
                    # Match headers more accurately - check for key terms in order of specificity
                    if ("event" in header_lower and "name" in header_lower) or header_lower == "name":
                        event_data["event_name"] = value
                        logger.debug(f"Mapped column {i} '{header_cell}' to event_name: {value[:50]}")
                    elif ("event" in header_lower and "date" in header_lower) or header_lower == "date":
                        event_data["event_date"] = value
                        logger.debug(f"Mapped column {i} '{header_cell}' to event_date: {value[:50]}")
                    elif ("website" in header_lower and "url" in header_lower) or "url" in header_lower or "website" in header_lower:
                        event_data["website_url"] = value
                        logger.debug(f"Mapped column {i} '{header_cell}' to website_url: {value[:50]}")
                    elif "location" in header_lower or "venue" in header_lower:
                        event_data["location"] = value
                        logger.debug(f"Mapped column {i} '{header_cell}' to location: {value[:50]}")
                    elif ("organizer" in header_lower and "contact" in header_lower) or "contact" in header_lower:
                        event_data["organizer_contact"] = value
                        logger.debug(f"Mapped column {i} '{header_cell}' to organizer_contact: {value[:50]}")
                    elif "fee" in header_lower or "cost" in header_lower or "price" in header_lower:
                        event_data["fees"] = value
                        logger.debug(f"Mapped column {i} '{header_cell}' to fees: {value[:50]}")
                    elif "note" in header_lower or "comment" in header_lower:
                        event_data["notes"] = value
                        logger.debug(f"Mapped column {i} '{header_cell}' to notes: {value[:50]}")
            
            # Fill in missing fields using position-based fallback
            # Standard order: Event Name, Event Date, Website/URL, Location, Contact, Fees, Notes
            if "event_name" not in event_data and len(row) > 0:
                event_data["event_name"] = row[0] if row[0] else ""
            if "event_date" not in event_data and len(row) > 1:
                event_data["event_date"] = row[1] if row[1] else ""
            if "website_url" not in event_data and len(row) > 2:
                event_data["website_url"] = row[2] if row[2] else ""
            if "location" not in event_data and len(row) > 3:
                event_data["location"] = row[3] if row[3] else ""
            if "organizer_contact" not in event_data and len(row) > 4:
                event_data["organizer_contact"] = row[4] if row[4] else ""
            if "fees" not in event_data and len(row) > 5:
                event_data["fees"] = row[5] if row[5] else ""
            if "notes" not in event_data and len(row) > 6:
                event_data["notes"] = row[6] if row[6] else ""
            
            # Ensure we have at least event name - use first cell if not found
            if "event_name" not in event_data or not event_data["event_name"]:
                logger.debug(f"No event_name found in parsed data. Available keys: {list(event_data.keys())}")
                # Always use first cell as event name if header mapping failed
                if row and len(row) > 0 and row[0]:
                    event_data["event_name"] = row[0]
                    logger.debug(f"Using first cell as event_name: {row[0]}")
                elif row and len(row) > 0:
                    event_data["event_name"] = "Unnamed Event"  # Default name if empty
                else:
                    event_data["event_name"] = "Unnamed Event"  # Fallback
            
            try:
                # Use empty string or None for missing fields - be very permissive
                event = EventItem(
                    event_name=event_data.get("event_name") or "Unnamed Event",
                    event_date=event_data.get("event_date") or None,
                    website_url=event_data.get("website_url") or None,
                    location=event_data.get("location") or None,
                    organizer_contact=event_data.get("organizer_contact") or None,
                    fees=event_data.get("fees") or None,
                    notes=event_data.get("notes") or None
                )
                logger.debug(f"Successfully created event: {event.event_name}")
                return event
            except Exception as e:
                logger.warning(f"Error creating EventItem: {str(e)}. Data: {event_data}")
                # Even on error, try to create with minimal data
                try:
                    event = EventItem(
                        event_name=event_data.get("event_name", "Unnamed Event") or "Unnamed Event",
                        event_date=None,
                        website_url=None,
                        location=None,
                        organizer_contact=None,
                        fees=None,
                        notes=None
                    )
                    logger.debug(f"Created event with minimal data: {event.event_name}")
                    return event
                except:
                    return None
        else:
            # Assume standard column order: Name, Date, URL, Location, Contact, Fees, Notes
            # Try to map by position, but be flexible
            event_name = ""
            event_date = ""
            website_url = None
            location = None
            organizer_contact = None
            fees = None
            notes = None
            
            # Try to intelligently assign columns based on content patterns
            for i, cell in enumerate(row):
                cell_str = str(cell).strip() if cell else ""
                if not cell_str:
                    continue
                
                # First non-empty cell is likely the event name
                if not event_name and cell_str:
                    event_name = cell_str
                    continue  # Move to next cell
                # Look for date patterns
                elif re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', cell_str, re.IGNORECASE):
                    if not event_date:
                        event_date = cell_str
                    else:
                        notes = (notes or "") + " " + cell_str if notes else cell_str
                # Look for URL patterns
                elif re.search(r'https?://|www\.', cell_str, re.IGNORECASE):
                    if not website_url:
                        website_url = cell_str
                    else:
                        notes = (notes or "") + " " + cell_str if notes else cell_str
                # Look for email or phone patterns
                elif re.search(r'@|\(\d{3}\)|\d{3}-\d{3}-\d{4}', cell_str):
                    if not organizer_contact:
                        organizer_contact = cell_str
                    else:
                        notes = (notes or "") + " " + cell_str if notes else cell_str
                # Look for fee/cost patterns
                elif re.search(r'\$|free|donation|fee|cost|price', cell_str, re.IGNORECASE):
                    if not fees:
                        fees = cell_str
                    else:
                        notes = (notes or "") + " " + cell_str if notes else cell_str
                # Otherwise, assign based on position if not set
                elif i == 1 and not event_date:
                    event_date = cell_str
                elif i == 2 and not website_url:
                    website_url = cell_str
                elif i == 3 and not location:
                    location = cell_str
                elif i == 4 and not organizer_contact:
                    organizer_contact = cell_str
                elif i == 5 and not fees:
                    fees = cell_str
                else:
                    # Append to notes
                    notes = (notes or "") + " " + cell_str if notes else cell_str
            
            # Clean up notes
            if notes:
                notes = notes.strip()
            
            # Always create an event, even if event_name is empty (use default)
            if not event_name or not event_name.strip():
                logger.debug(f"No event_name found in row, using default. First cell: {row[0] if row else 'N/A'}")
                event_name = "Unnamed Event"
            
            try:
                # Convert empty strings to None for optional fields
                event = EventItem(
                    event_name=event_name,
                    event_date=event_date if (event_date and event_date.strip()) else None,
                    website_url=website_url if (website_url and website_url.strip()) else None,
                    location=location if (location and location.strip()) else None,
                    organizer_contact=organizer_contact if (organizer_contact and organizer_contact.strip()) else None,
                    fees=fees if (fees and fees.strip()) else None,
                    notes=notes if (notes and notes.strip()) else None
                )
                logger.debug(f"Successfully created event from row: {event.event_name}")
                return event
            except Exception as e:
                logger.warning(f"Error creating EventItem from row: {str(e)}. Row: {row}")
                # Even on error, try to create with minimal data
                try:
                    event = EventItem(
                        event_name=event_name or "Unnamed Event",
                        event_date=None,
                        website_url=None,
                        location=None,
                        organizer_contact=None,
                        fees=None,
                        notes=None
                    )
                    logger.debug(f"Created event with minimal data after error: {event.event_name}")
                    return event
                except:
                    logger.error(f"Completely failed to create event from row: {row}")
                    return None
    
    def parse_ai_response(self, response: str) -> List[EventItem]:
        """
        Parse LLM response and extract event data.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            List[EventItem]: List of parsed events
        """
        if not response or not response.strip():
            logger.warning("Empty LLM response")
            return []
        
        events = []
        logger.debug(f"Parsing LLM response (length: {len(response)} chars)")
        
        # Try to extract table
        table_rows = self._find_table_in_text(response)
        
        if table_rows and len(table_rows) > 0:
            logger.info(f"Found table with {len(table_rows)} rows")
            # First row might be header
            header = None
            data_rows = table_rows
            # Check if first row looks like a header
            if len(table_rows) > 0:
                first_row_lower = " ".join([str(cell).lower() for cell in table_rows[0]])
                if any(col in first_row_lower for col in self.expected_columns):
                    header = table_rows[0]
                    data_rows = table_rows[1:]
                    logger.info("Using first row as header")
                else:
                    # Check if all rows have similar structure (might be data without header)
                    logger.info("First row doesn't look like header, treating all as data rows")
            
            # Parse each data row - be very permissive, don't skip any rows
            parsed_count = 0
            skipped_count = 0
            for idx, row in enumerate(data_rows):
                try:
                    if not row or len(row) == 0:
                        logger.debug(f"Skipping completely empty row {idx}")
                        skipped_count += 1
                        continue
                    
                    logger.debug(f"Attempting to parse row {idx+1}/{len(data_rows)}: {str(row[:3]) if len(row) >= 3 else row}...")
                    event = self._parse_row_to_event(row, header)
                    
                    # Accept ANY event that was created, even with minimal data
                    if event:
                        events.append(event)
                        parsed_count += 1
                        logger.debug(f"✓ Successfully parsed row {idx+1} as event: {event.event_name[:50]}")
                    else:
                        logger.warning(f"✗ Failed to parse row {idx+1}: No event created. Row: {str(row)[:200]}")
                        skipped_count += 1
                        # Try to create a minimal event even if parsing failed
                        if row and len(row) > 0:
                            try:
                                minimal_event = EventItem(
                                    event_name=row[0] if row[0] else "Unnamed Event",
                                    event_date=None,
                                    website_url=None,
                                    location=None,
                                    organizer_contact=None,
                                    fees=None,
                                    notes=" ".join(row[1:]) if len(row) > 1 else None
                                )
                                events.append(minimal_event)
                                parsed_count += 1
                                logger.info(f"Created minimal event from failed row {idx+1}: {minimal_event.event_name}")
                            except Exception as e2:
                                logger.error(f"Could not create even minimal event from row {idx+1}: {str(e2)}")
                                skipped_count += 1
                except Exception as e:
                    logger.error(f"Exception parsing row {idx}: {str(e)}. Row: {str(row)[:200]}", exc_info=True)
                    # Try to create minimal event even on exception
                    if row and len(row) > 0:
                        try:
                            minimal_event = EventItem(
                                event_name=row[0] if row[0] else "Unnamed Event",
                                event_date=None,
                                website_url=None,
                                location=None,
                                organizer_contact=None,
                                fees=None,
                                notes=" ".join(row[1:]) if len(row) > 1 else None
                            )
                            events.append(minimal_event)
                            parsed_count += 1
                            logger.info(f"Created minimal event from exception row {idx}: {minimal_event.event_name}")
                        except:
                            skipped_count += 1
                    else:
                        skipped_count += 1
                    continue
            
            logger.info(f"Parsing complete: {parsed_count} events parsed, {skipped_count} rows skipped from {len(data_rows)} total rows")
        
        # If no table found, try to extract events from text patterns
        if not events:
            logger.info("No table found, attempting to extract events from text patterns")
            # Look for event-like patterns in the text
            # This is a fallback for when AI doesn't return a table
            lines = response.split("\n")
            current_event = {}
            
            for line in lines:
                line = line.strip()
                if not line or len(line) < 5:
                    continue
                
                # Look for patterns like "Event: ...", "Name: ...", etc.
                if re.match(r'^(event|name):\s*(.+)', line, re.IGNORECASE):
                    if current_event.get("event_name"):
                        # Save previous event
                        try:
                            events.append(EventItem(**current_event))
                        except:
                            pass
                    current_event = {"event_name": re.sub(r'^(event|name):\s*', '', line, flags=re.IGNORECASE).strip()}
                elif "date:" in line.lower():
                    current_event["event_date"] = re.sub(r'^date:\s*', '', line, flags=re.IGNORECASE).strip()
                elif "url:" in line.lower() or "website:" in line.lower():
                    current_event["website_url"] = re.sub(r'^(url|website):\s*', '', line, flags=re.IGNORECASE).strip()
                elif "location:" in line.lower():
                    current_event["location"] = re.sub(r'^location:\s*', '', line, flags=re.IGNORECASE).strip()
                elif "contact:" in line.lower():
                    current_event["organizer_contact"] = re.sub(r'^contact:\s*', '', line, flags=re.IGNORECASE).strip()
                elif "fee:" in line.lower():
                    current_event["fees"] = re.sub(r'^fee:\s*', '', line, flags=re.IGNORECASE).strip()
            
            # Add last event if exists
            if current_event.get("event_name"):
                try:
                    events.append(EventItem(**current_event))
                except:
                    pass
        
        logger.info(f"Parsed {len(events)} events from LLM response")
        return events

