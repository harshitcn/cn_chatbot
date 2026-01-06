"""
CSV generator for event discovery reports.
Generates CSV files with events data and includes disclaimer.
"""
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from app.models import EventItem

logger = logging.getLogger(__name__)


class CSVGenerator:
    """
    Generator for CSV event reports.
    Creates properly formatted CSV files with UTF-8 encoding.
    """
    
    def __init__(self, base_path: str = "data/events"):
        """
        Initialize CSV generator.
        
        Args:
            base_path: Base directory for storing CSV files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize center name for use in filename."""
        # Remove or replace invalid filename characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        # Remove leading/trailing spaces and dots
        name = name.strip('. ')
        return name
    
    def generate_csv(
        self,
        events: List[EventItem],
        center_name: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate CSV file from events list.
        
        Args:
            events: List of EventItem objects
            center_name: Name of the center (used in filename)
            output_path: Optional custom output path. If not provided, generates path.
            
        Returns:
            str: Path to the generated CSV file
        """
        # Create date-based subdirectory
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_dir = self.base_path / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        if output_path:
            csv_path = Path(output_path)
        else:
            sanitized_name = self._sanitize_filename(center_name)
            timestamp = datetime.now().strftime("%Y-%m-%d")
            filename = f"Events_{sanitized_name}_{timestamp}.csv"
            csv_path = date_dir / filename
        
        # Ensure parent directory exists
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Write CSV file with UTF-8 encoding
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                # Define CSV columns
                fieldnames = [
                    'Event Name',
                    'Event Date',
                    'Event Website / URL',
                    'Location',
                    'Organizer Contact Information',
                    'Fees (if any)',
                    'Notes'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                # Write event rows
                for event in events:
                    writer.writerow({
                        'Event Name': event.event_name or '',
                        'Event Date': event.event_date or '',
                        'Event Website / URL': event.website_url or '',
                        'Location': event.location or '',
                        'Organizer Contact Information': event.organizer_contact or '',
                        'Fees (if any)': event.fees or '',
                        'Notes': event.notes or ''
                    })
            
            logger.info(f"Generated CSV file: {csv_path} with {len(events)} events")
            return str(csv_path)
            
        except Exception as e:
            logger.error(f"Error generating CSV file: {str(e)}", exc_info=True)
            raise
    
    def generate_fallback_csv(
        self,
        center_name: str,
        message: str = "No events found or AI failed for this run."
    ) -> str:
        """
        Generate an empty CSV with headers only when no events are found or AI fails.
        This ensures emails are always sent with a CSV file, even when there's no data.
        
        Args:
            center_name: Name of the center
            message: Message for logging (not included in CSV)
            
        Returns:
            str: Path to the generated CSV file
        """
        # Create date-based subdirectory
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_dir = self.base_path / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        sanitized_name = self._sanitize_filename(center_name)
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = f"Events_{sanitized_name}_{timestamp}.csv"
        csv_path = date_dir / filename
        
        try:
            # Write CSV file with UTF-8 encoding - headers only, no data rows
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                # Define CSV columns (same as generate_csv)
                fieldnames = [
                    'Event Name',
                    'Event Date',
                    'Event Website / URL',
                    'Location',
                    'Organizer Contact Information',
                    'Fees (if any)',
                    'Notes'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                # No data rows - just headers

            logger.info(f"Generated empty CSV file with headers only: {csv_path} (Reason: {message})")
            return str(csv_path)
            
        except Exception as e:
            logger.error(f"Error generating fallback CSV file: {str(e)}", exc_info=True)
            raise
    
    def generate_empty_csv(self, center_name: str) -> str:
        """
        Generate an empty CSV with headers only (alias for generate_fallback_csv).
        This is a convenience method for generating empty CSVs.
        
        Args:
            center_name: Name of the center
            
        Returns:
            str: Path to the generated CSV file
        """
        return self.generate_fallback_csv(center_name, "No events data available")

