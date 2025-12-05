"""Email notification service."""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
import structlog

from config.settings import settings
from src.database import Artwork

logger = structlog.get_logger()


class EmailNotifier:
    """Sends email notifications when new artwork is discovered."""

    def __init__(self) -> None:
        self.logger = logger.bind(component="email_notifier")

    async def send_new_artwork_notification(self, artwork: Artwork) -> bool:
        """
        Send an email notification about a newly discovered artwork.

        Args:
            artwork: The artwork that was discovered

        Returns:
            True if sent successfully, False otherwise
        """
        if not all([settings.smtp_host, settings.smtp_username, settings.notification_email]):
            self.logger.warning("Email not configured, skipping notification")
            return False

        subject = f"New Dan Brown Artwork Found: {artwork.title[:50]}"

        body = self._build_email_body(artwork)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_username
        msg["To"] = settings.notification_email

        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(self._build_html_body(artwork), "html"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                start_tls=True,
            )
            self.logger.info(
                "Notification sent",
                artwork_id=artwork.id,
                recipient=settings.notification_email,
            )
            return True
        except Exception as e:
            self.logger.error(
                "Failed to send notification",
                artwork_id=artwork.id,
                error=str(e),
            )
            return False

    def _build_email_body(self, artwork: Artwork) -> str:
        """Build plain text email body."""
        return f"""
New Dan Brown Artwork Found!

Title: {artwork.title}

Platform: {artwork.source_platform}
Price: {artwork.price or 'Not listed'} {artwork.currency}
Location: {artwork.location or 'Unknown'}

Confidence Score: {artwork.confidence_score:.1f}

View Listing: {artwork.source_url}

Description:
{artwork.description or 'No description available'}

---
Dan Brown Art Tracker
        """.strip()

    def _build_html_body(self, artwork: Artwork) -> str:
        """Build HTML email body."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Georgia, serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .details {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .details dt {{ font-weight: bold; color: #555; }}
        .details dd {{ margin: 0 0 10px 0; }}
        .confidence {{ font-size: 1.2em; color: #27ae60; }}
        a.button {{ display: inline-block; background: #3498db; color: white; padding: 10px 20px;
                   text-decoration: none; border-radius: 5px; margin-top: 15px; }}
        .description {{ background: #fff; border-left: 3px solid #3498db; padding: 10px 15px;
                       margin: 20px 0; font-style: italic; }}
        .footer {{ color: #888; font-size: 0.9em; margin-top: 30px; padding-top: 20px;
                  border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <h1>New Dan Brown Artwork Found</h1>

    <h2>{artwork.title}</h2>

    <dl class="details">
        <dt>Platform</dt>
        <dd>{artwork.source_platform}</dd>

        <dt>Price</dt>
        <dd>{artwork.price or 'Not listed'} {artwork.currency}</dd>

        <dt>Location</dt>
        <dd>{artwork.location or 'Unknown'}</dd>

        <dt>Confidence Score</dt>
        <dd class="confidence">{artwork.confidence_score:.1f}</dd>
    </dl>

    <a href="{artwork.source_url}" class="button">View Listing</a>

    <div class="description">
        <strong>Description:</strong><br>
        {artwork.description or 'No description available'}
    </div>

    <div class="footer">
        Dan Brown Art Tracker<br>
        Tracking artwork by Dan Brown (1949-2022)
    </div>
</body>
</html>
        """.strip()
