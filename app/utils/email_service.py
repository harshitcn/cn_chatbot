"""
Email service for distributing event discovery reports.
Supports SMTP and optional SendGrid integration.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List
from app.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending event discovery reports via email.
    Supports SMTP and can be extended for SendGrid.
    """
    
    def __init__(self):
        """Initialize email service with settings."""
        self.settings = get_settings()
        self.smtp_host = getattr(self.settings, 'email_smtp_host', None)
        self.smtp_port = getattr(self.settings, 'email_smtp_port', 587)
        self.smtp_user = getattr(self.settings, 'email_smtp_user', None)
        self.smtp_password = getattr(self.settings, 'email_smtp_password', None)
        self.email_from = getattr(self.settings, 'email_from', None)
        self.use_tls = getattr(self.settings, 'email_use_tls', True)
        
        # Check if email is configured
        self.enabled = bool(
            self.smtp_host and 
            self.smtp_user and 
            self.smtp_password and 
            self.email_from
        )
        
        if not self.enabled:
            logger.warning("Email service not fully configured. Email distribution will be disabled.")
            if not self.smtp_host:
                logger.warning("  - EMAIL_SMTP_HOST is not set or empty")
            if not self.smtp_user:
                logger.warning("  - EMAIL_SMTP_USER is not set or empty")
            if not self.smtp_password:
                logger.warning("  - EMAIL_SMTP_PASSWORD is not set or empty")
            if not self.email_from:
                logger.warning("  - EMAIL_FROM is not set or empty")
        else:
            logger.info(f"Email service configured: SMTP host={self.smtp_host}, port={self.smtp_port}, from={self.email_from}")
    
    def _create_email_body(
        self,
        center_name: str,
        event_count: int,
        radius: int,
        location: str
    ) -> str:
        """Create email body text."""
        body = f"""
Hello Code Ninjas {center_name} Team,

Your monthly local events discovery report is ready!

Summary:
- Center: {center_name}
- Location: {location}
- Search Radius: {radius} miles
- Events Found: {event_count}

The attached CSV file contains all discovered family-friendly community events in your area. 
These events represent opportunities where your center could set up a table, participate, 
or engage with families in the community.

Please review each event independently for accuracy, appropriateness, and suitability 
before deciding to participate.

DISCLAIMER:
Events listed here are sourced from publicly available online information.
Code Ninjas does not endorse or verify any event, organizer, venue, or activity.
Franchisees should independently evaluate the accuracy, appropriateness, and suitability 
of each event before participating.

Best regards,
CodeNinjas
"""
        return body.strip()
    
    def send_events_report(
        self,
        recipient_email: str,
        csv_path: str,
        center_name: str,
        event_count: int,
        radius: int,
        location: str,
        subject: Optional[str] = None
    ) -> bool:
        """
        Send event discovery report via email.
        
        Args:
            recipient_email: Email address of the recipient
            csv_path: Path to the CSV file to attach
            center_name: Name of the center
            event_count: Number of events found
            radius: Search radius used
            location: Location searched
            subject: Optional custom email subject
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not configured. Cannot send email.")
            return False
        
        if not recipient_email:
            logger.warning("No recipient email provided.")
            return False
        
        csv_file = Path(csv_path)
        if not csv_file.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = recipient_email
            msg['Subject'] = subject or f"Code Ninjas {center_name} - Local Events Report"
            
            # Add body
            body = self._create_email_body(center_name, event_count, radius, location)
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach CSV file
            with open(csv_file, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {csv_file.name}'
            )
            msg.attach(part)
            
            # Send email
            logger.info(f"Sending email to {recipient_email} via {self.smtp_host}:{self.smtp_port}...")
            
            if not self.smtp_host:
                logger.error("EMAIL_SMTP_HOST is not configured. Cannot send email.")
                return False
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Successfully sent email to {recipient_email}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error sending email to {recipient_email}: {error_msg}")
            
            # Provide helpful error messages for common issues
            if "getaddrinfo failed" in error_msg or "11001" in error_msg or "11002" in error_msg:
                logger.error(f"❌ Cannot resolve SMTP host '{self.smtp_host}'")
                logger.error(f"")
                logger.error(f"Please check your EMAIL_SMTP_HOST setting in your .env file:")
                logger.error(f"")
                logger.error(f"Common SMTP server settings:")
                logger.error(f"  Gmail:        EMAIL_SMTP_HOST=smtp.gmail.com")
                logger.error(f"  Outlook:      EMAIL_SMTP_HOST=smtp-mail.outlook.com")
                logger.error(f"  Office365:    EMAIL_SMTP_HOST=smtp.office365.com")
                logger.error(f"  Yahoo:        EMAIL_SMTP_HOST=smtp.mail.yahoo.com")
                logger.error(f"")
                logger.error(f"Current configuration:")
                logger.error(f"  EMAIL_SMTP_HOST: '{self.smtp_host}'")
                logger.error(f"  EMAIL_SMTP_PORT: {self.smtp_port}")
                logger.error(f"  EMAIL_SMTP_USER: '{self.smtp_user}'")
                logger.error(f"  EMAIL_FROM: '{self.email_from}'")
                logger.error(f"")
                logger.error(f"If EMAIL_SMTP_HOST is empty or None, add it to your .env file and restart the server.")
            elif "authentication" in error_msg.lower() or "535" in error_msg or "534" in error_msg:
                logger.error(f"❌ SMTP authentication failed")
                logger.error(f"Please check:")
                logger.error(f"  1. EMAIL_SMTP_USER is correct: '{self.smtp_user}'")
                logger.error(f"  2. EMAIL_SMTP_PASSWORD is correct")
                logger.error(f"  3. For Gmail, use an App Password (not your regular password)")
                logger.error(f"     Generate at: https://myaccount.google.com/apppasswords")
            elif "connection" in error_msg.lower() or "connect" in error_msg.lower() or "timeout" in error_msg.lower():
                logger.error(f"❌ Cannot connect to SMTP server")
                logger.error(f"Please check:")
                logger.error(f"  1. EMAIL_SMTP_HOST: '{self.smtp_host}'")
                logger.error(f"  2. EMAIL_SMTP_PORT: {self.smtp_port}")
                logger.error(f"  3. Firewall or network restrictions")
                logger.error(f"  4. Internet connection")
            else:
                logger.error(f"Full error details:", exc_info=True)
            
            return False
    
    def send_batch_reports(
        self,
        reports: List[dict]
    ) -> dict:
        """
        Send multiple event reports in batch.
        
        Args:
            reports: List of dicts with keys: recipient_email, csv_path, center_name, 
                    event_count, radius, location
            
        Returns:
            dict: Summary with success_count and failed_count
        """
        if not self.enabled:
            logger.warning("Email service not configured. Cannot send batch emails.")
            return {"success_count": 0, "failed_count": len(reports)}
        
        success_count = 0
        failed_count = 0
        
        for report in reports:
            success = self.send_events_report(
                recipient_email=report.get("recipient_email"),
                csv_path=report.get("csv_path"),
                center_name=report.get("center_name"),
                event_count=report.get("event_count", 0),
                radius=report.get("radius", 5),
                location=report.get("location", ""),
                subject=report.get("subject")
            )
            
            if success:
                success_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Batch email send complete: {success_count} succeeded, {failed_count} failed")
        return {
            "success_count": success_count,
            "failed_count": failed_count
        }

