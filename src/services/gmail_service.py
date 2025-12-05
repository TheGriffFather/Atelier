"""Gmail API integration service for outreach email management."""

import base64
import json
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import structlog

logger = structlog.get_logger()

# Gmail API scopes - read and send emails
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

# Paths for credentials
DATA_DIR = Path(__file__).parent.parent.parent / "data"
CREDENTIALS_FILE = DATA_DIR / "gmail_credentials.json"
TOKEN_FILE = DATA_DIR / "gmail_token.json"


class GmailService:
    """Service for interacting with Gmail API."""

    def __init__(self):
        self.service = None
        self.credentials = None
        self._initialized = False

    def is_configured(self) -> bool:
        """Check if Gmail credentials are configured."""
        return CREDENTIALS_FILE.exists()

    def is_authenticated(self) -> bool:
        """Check if we have valid authentication."""
        if not TOKEN_FILE.exists():
            return False
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            # If token expired but we have refresh token, refresh it
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            return creds and creds.valid
        except Exception:
            return False

    def get_auth_url(self) -> Optional[str]:
        """Get the OAuth2 authorization URL for user authentication."""
        if not self.is_configured():
            logger.error("Gmail credentials not configured")
            return None

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            # Use localhost redirect - works for desktop apps
            flow.redirect_uri = 'http://localhost:8080/'

            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            return auth_url
        except Exception as e:
            logger.error("Failed to generate auth URL", error=str(e))
            return None

    def authenticate_with_code(self, auth_code: str) -> bool:
        """Complete authentication with the authorization code."""
        if not self.is_configured():
            return False

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            flow.redirect_uri = 'http://localhost:8080/'
            flow.fetch_token(code=auth_code)

            creds = flow.credentials

            # Save the credentials
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

            self.credentials = creds
            self._build_service()
            logger.info("Gmail authentication successful")
            return True
        except Exception as e:
            logger.error("Gmail authentication failed", error=str(e))
            return False

    def _load_credentials(self) -> bool:
        """Load and refresh credentials."""
        if not TOKEN_FILE.exists():
            return False

        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())

            if creds and creds.valid:
                self.credentials = creds
                return True
            return False
        except Exception as e:
            logger.error("Failed to load credentials", error=str(e))
            return False

    def _build_service(self):
        """Build the Gmail API service."""
        if self.credentials:
            self.service = build('gmail', 'v1', credentials=self.credentials)
            self._initialized = True

    def initialize(self) -> bool:
        """Initialize the Gmail service."""
        if self._initialized and self.service:
            return True

        if self._load_credentials():
            self._build_service()
            return True
        return False

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> Optional[dict]:
        """
        Send an email via Gmail API.

        Returns the sent message info or None on failure.
        """
        if not self.initialize():
            logger.error("Gmail service not initialized")
            return None

        try:
            if html_body:
                message = MIMEMultipart('alternative')
                message['to'] = to
                message['subject'] = subject

                text_part = MIMEText(body, 'plain')
                html_part = MIMEText(html_body, 'html')

                message.attach(text_part)
                message.attach(html_part)
            else:
                message = MIMEText(body)
                message['to'] = to
                message['subject'] = subject

            # Encode the message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send via API
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()

            logger.info("Email sent successfully", to=to, message_id=result.get('id'))
            return result
        except HttpError as e:
            logger.error("Failed to send email", error=str(e), to=to)
            return None
        except Exception as e:
            logger.error("Unexpected error sending email", error=str(e))
            return None

    def get_messages(
        self,
        query: str = "",
        max_results: int = 20
    ) -> list[dict]:
        """
        Get messages matching a query.

        Query examples:
        - "from:someone@example.com"
        - "subject:Dan Brown Art"
        - "after:2024/01/01"
        """
        if not self.initialize():
            return []

        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            return messages
        except Exception as e:
            logger.error("Failed to get messages", error=str(e))
            return []

    def get_message_detail(self, message_id: str) -> Optional[dict]:
        """Get full details of a specific message."""
        if not self.initialize():
            return None

        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Parse headers
            headers = {}
            for header in message.get('payload', {}).get('headers', []):
                headers[header['name'].lower()] = header['value']

            # Get body
            body = self._get_message_body(message.get('payload', {}))

            return {
                'id': message['id'],
                'thread_id': message.get('threadId'),
                'from': headers.get('from', ''),
                'to': headers.get('to', ''),
                'subject': headers.get('subject', ''),
                'date': headers.get('date', ''),
                'body': body,
                'snippet': message.get('snippet', ''),
                'labels': message.get('labelIds', [])
            }
        except Exception as e:
            logger.error("Failed to get message detail", error=str(e), message_id=message_id)
            return None

    def _get_message_body(self, payload: dict) -> str:
        """Extract message body from payload."""
        body = ""

        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    if part.get('body', {}).get('data'):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif 'parts' in part:
                    body = self._get_message_body(part)
                    if body:
                        break

        return body

    def search_responses(
        self,
        subject_keywords: list[str],
        after_date: Optional[datetime] = None
    ) -> list[dict]:
        """
        Search for email responses related to outreach.

        Looks for replies to emails we sent about Dan Brown art.
        Searches both subject and body content.
        """
        query_parts = []

        # Search for replies (in:inbox, not from us)
        query_parts.append("in:inbox")

        # Add keywords - search in subject OR body
        if subject_keywords:
            # Build OR query that searches subject and body
            keyword_clauses = []
            for kw in subject_keywords:
                # subject:keyword OR "keyword" (body search)
                keyword_clauses.append(f'subject:"{kw}"')
                keyword_clauses.append(f'"{kw}"')
            keyword_query = " OR ".join(keyword_clauses)
            query_parts.append(f"({keyword_query})")

        # Add date filter
        if after_date:
            query_parts.append(f"after:{after_date.strftime('%Y/%m/%d')}")

        query = " ".join(query_parts)
        messages = self.get_messages(query=query, max_results=50)

        # Get full details for each message
        detailed = []
        for msg in messages:
            detail = self.get_message_detail(msg['id'])
            if detail:
                detailed.append(detail)

        return detailed

    def get_sent_emails(
        self,
        after_date: Optional[datetime] = None,
        max_results: int = 50
    ) -> list[dict]:
        """Get emails we've sent related to Dan Brown outreach."""
        query_parts = ["in:sent"]

        if after_date:
            query_parts.append(f"after:{after_date.strftime('%Y/%m/%d')}")

        # Look for Dan Brown related emails - specific outreach keywords
        # These should match the contacts/organizations we're reaching out to
        keywords = [
            "Dan Brown artist",
            "Dan Brown 1949",
            "Dan Brown catalogue",
            "trompe l'oeil",
            "Peto Museum",
            "Paier College",
            "Army War College",
            "Pentagon 9/11",
            "Rolling Stone portrait",
            "Susan Powell Fine Art",
            "Alumni Archive Inquiry",
            "Archival Image Request"
        ]
        keyword_clauses = []
        for kw in keywords:
            keyword_clauses.append(f'subject:"{kw}"')
            keyword_clauses.append(f'"{kw}"')
        query_parts.append(f"({' OR '.join(keyword_clauses)})")

        query = " ".join(query_parts)
        messages = self.get_messages(query=query, max_results=max_results)

        detailed = []
        for msg in messages:
            detail = self.get_message_detail(msg['id'])
            if detail:
                detailed.append(detail)

        return detailed

    def get_thread_messages(self, thread_id: str) -> list[dict]:
        """Get all messages in a thread."""
        if not self.initialize():
            return []

        try:
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id,
                format='full'
            ).execute()

            messages = []
            for msg in thread.get('messages', []):
                # Parse headers
                headers = {}
                for header in msg.get('payload', {}).get('headers', []):
                    headers[header['name'].lower()] = header['value']

                # Get body
                body = self._get_message_body(msg.get('payload', {}))

                messages.append({
                    'id': msg['id'],
                    'thread_id': msg.get('threadId'),
                    'from': headers.get('from', ''),
                    'to': headers.get('to', ''),
                    'subject': headers.get('subject', ''),
                    'date': headers.get('date', ''),
                    'body': body,
                    'snippet': msg.get('snippet', ''),
                    'labels': msg.get('labelIds', [])
                })

            return messages
        except Exception as e:
            logger.error("Failed to get thread", error=str(e), thread_id=thread_id)
            return []

    def revoke_access(self) -> bool:
        """Revoke Gmail access and delete stored credentials."""
        try:
            if TOKEN_FILE.exists():
                TOKEN_FILE.unlink()
            self.service = None
            self.credentials = None
            self._initialized = False
            logger.info("Gmail access revoked")
            return True
        except Exception as e:
            logger.error("Failed to revoke access", error=str(e))
            return False


# Singleton instance
gmail_service = GmailService()
