"""API routes for Gmail integration."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import Outreach, Contact
from src.database.session import get_session
from src.services.gmail_service import gmail_service

router = APIRouter(prefix="/api/gmail", tags=["gmail"])


# =============================================================================
# Pydantic Models
# =============================================================================

class AuthCodeRequest(BaseModel):
    """Request to complete OAuth authentication."""
    code: str


class SendEmailRequest(BaseModel):
    """Request to send an email."""
    to: str
    subject: str
    body: str
    html_body: Optional[str] = None
    outreach_id: Optional[int] = None  # Link to existing outreach record
    contact_id: Optional[int] = None   # Create new outreach record for this contact


class LinkThreadRequest(BaseModel):
    """Request to link a Gmail thread to an outreach record."""
    thread_id: str
    message_id: Optional[str] = None


class EmailResponse(BaseModel):
    """Email message response."""
    id: str
    thread_id: Optional[str]
    from_address: str
    to_address: str
    subject: str
    date: str
    snippet: str
    body: Optional[str] = None


# =============================================================================
# Authentication Routes
# =============================================================================

@router.get("/status")
async def get_gmail_status():
    """Get Gmail integration status."""
    return {
        "configured": gmail_service.is_configured(),
        "authenticated": gmail_service.is_authenticated(),
        "message": _get_status_message()
    }


def _get_status_message() -> str:
    """Get a human-readable status message."""
    if not gmail_service.is_configured():
        return "Gmail credentials not configured. Add gmail_credentials.json to the data folder."
    if not gmail_service.is_authenticated():
        return "Gmail not authenticated. Click 'Connect Gmail' to authorize."
    return "Gmail connected and ready."


@router.get("/auth-url")
async def get_auth_url():
    """Get the OAuth2 authorization URL."""
    if not gmail_service.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Gmail credentials not configured. Add gmail_credentials.json to the data folder."
        )

    url = gmail_service.get_auth_url()
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate auth URL")

    return {"auth_url": url}


@router.post("/authenticate")
async def authenticate(request: AuthCodeRequest):
    """Complete OAuth authentication with authorization code."""
    success = gmail_service.authenticate_with_code(request.code)
    if not success:
        raise HTTPException(status_code=400, detail="Authentication failed. Invalid code.")

    return {"message": "Gmail connected successfully", "authenticated": True}


@router.post("/disconnect")
async def disconnect_gmail():
    """Disconnect Gmail integration."""
    gmail_service.revoke_access()
    return {"message": "Gmail disconnected", "authenticated": False}


# =============================================================================
# Email Routes
# =============================================================================

@router.post("/send")
async def send_email(
    request: SendEmailRequest,
    session: AsyncSession = Depends(get_session)
):
    """Send an email via Gmail and track the thread."""
    if not gmail_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Gmail not authenticated")

    result = gmail_service.send_email(
        to=request.to,
        subject=request.subject,
        body=request.body,
        html_body=request.html_body
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to send email")

    message_id = result.get('id')
    thread_id = result.get('threadId')
    outreach_id = None

    # Update existing outreach record if linked
    if request.outreach_id:
        query = select(Outreach).where(Outreach.id == request.outreach_id)
        outreach_result = await session.execute(query)
        outreach = outreach_result.scalar_one_or_none()

        if outreach:
            outreach.status = 'awaiting_response'
            outreach.date_sent = datetime.utcnow()
            outreach.gmail_message_id = message_id
            outreach.gmail_thread_id = thread_id
            await session.commit()
            outreach_id = outreach.id

    # Or create new outreach record if contact_id provided
    elif request.contact_id:
        new_outreach = Outreach(
            contact_id=request.contact_id,
            outreach_type='email',
            status='awaiting_response',
            subject=request.subject,
            content=request.body,
            date_sent=datetime.utcnow(),
            gmail_message_id=message_id,
            gmail_thread_id=thread_id
        )
        session.add(new_outreach)
        await session.commit()
        await session.refresh(new_outreach)
        outreach_id = new_outreach.id

    return {
        "message": "Email sent successfully",
        "message_id": message_id,
        "thread_id": thread_id,
        "outreach_id": outreach_id
    }


@router.get("/inbox")
async def get_inbox(
    query: Optional[str] = None,
    max_results: int = 20
):
    """Get inbox messages."""
    if not gmail_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Gmail not authenticated")

    search_query = query or "in:inbox"
    messages = gmail_service.get_messages(query=search_query, max_results=max_results)

    detailed = []
    for msg in messages[:max_results]:
        detail = gmail_service.get_message_detail(msg['id'])
        if detail:
            detailed.append({
                "id": detail['id'],
                "thread_id": detail.get('thread_id'),
                "from_address": detail.get('from', ''),
                "to_address": detail.get('to', ''),
                "subject": detail.get('subject', ''),
                "date": detail.get('date', ''),
                "snippet": detail.get('snippet', '')
            })

    return {"messages": detailed, "count": len(detailed)}


@router.get("/message/{message_id}")
async def get_message(message_id: str):
    """Get a specific email message."""
    if not gmail_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Gmail not authenticated")

    detail = gmail_service.get_message_detail(message_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Message not found")

    return {
        "id": detail['id'],
        "thread_id": detail.get('thread_id'),
        "from_address": detail.get('from', ''),
        "to_address": detail.get('to', ''),
        "subject": detail.get('subject', ''),
        "date": detail.get('date', ''),
        "body": detail.get('body', ''),
        "snippet": detail.get('snippet', '')
    }


@router.get("/responses")
async def check_responses(
    after_date: Optional[str] = None
):
    """
    Check for responses to outreach emails.

    Returns recent inbox messages that might be responses to our outreach.
    """
    if not gmail_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Gmail not authenticated")

    # Parse date if provided
    date_filter = None
    if after_date:
        try:
            date_filter = datetime.fromisoformat(after_date)
        except ValueError:
            pass

    # Search for responses related to Dan Brown art outreach
    # More specific keywords to avoid false positives like "Painting with a Twist"
    keywords = [
        "Dan Brown",
        "Dan Brown artist",
        "trompe l'oeil",
        "Pentagon September",
        "Army War College",
        "Rolling Stone portrait",
        "Paier College",
        "Peto Museum",
        "Susan Powell Fine Art"
    ]
    responses = gmail_service.search_responses(
        subject_keywords=keywords,
        after_date=date_filter
    )

    return {
        "responses": [
            {
                "id": r['id'],
                "from_address": r.get('from', ''),
                "subject": r.get('subject', ''),
                "date": r.get('date', ''),
                "snippet": r.get('snippet', '')
            }
            for r in responses
        ],
        "count": len(responses)
    }


@router.get("/sent")
async def get_sent_emails(
    after_date: Optional[str] = None,
    max_results: int = 30
):
    """Get sent emails related to outreach."""
    if not gmail_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Gmail not authenticated")

    date_filter = None
    if after_date:
        try:
            date_filter = datetime.fromisoformat(after_date)
        except ValueError:
            pass

    emails = gmail_service.get_sent_emails(
        after_date=date_filter,
        max_results=max_results
    )

    return {
        "emails": [
            {
                "id": e['id'],
                "to_address": e.get('to', ''),
                "subject": e.get('subject', ''),
                "date": e.get('date', ''),
                "snippet": e.get('snippet', '')
            }
            for e in emails
        ],
        "count": len(emails)
    }


@router.get("/thread/{thread_id}")
async def get_email_thread(thread_id: str):
    """Get all messages in a thread."""
    if not gmail_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Gmail not authenticated")

    messages = gmail_service.get_thread_messages(thread_id)

    return {
        "thread_id": thread_id,
        "messages": [
            {
                "id": msg['id'],
                "from_address": msg.get('from', ''),
                "to_address": msg.get('to', ''),
                "subject": msg.get('subject', ''),
                "date": msg.get('date', ''),
                "body": msg.get('body', ''),
                "snippet": msg.get('snippet', '')
            }
            for msg in messages
        ],
        "count": len(messages)
    }


# =============================================================================
# Sync with Outreach
# =============================================================================

@router.post("/sync-outreach/{outreach_id}")
async def sync_outreach_with_gmail(
    outreach_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Sync an outreach record with Gmail.

    If the outreach has a subject, search for matching emails in sent folder.
    """
    if not gmail_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Gmail not authenticated")

    # Get the outreach record
    query = select(Outreach).where(Outreach.id == outreach_id)
    result = await session.execute(query)
    outreach = result.scalar_one_or_none()

    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach record not found")

    if not outreach.subject:
        return {"message": "No subject to search for", "found": False}

    # Search for matching sent emails
    search_query = f'in:sent subject:"{outreach.subject}"'
    messages = gmail_service.get_messages(query=search_query, max_results=5)

    if messages:
        detail = gmail_service.get_message_detail(messages[0]['id'])
        if detail:
            # Update outreach with Gmail info
            outreach.date_sent = datetime.utcnow()  # Could parse from email date
            outreach.status = 'sent'
            await session.commit()

            return {
                "message": "Found matching email",
                "found": True,
                "email_id": detail['id'],
                "date": detail.get('date')
            }

    return {"message": "No matching email found", "found": False}


# =============================================================================
# Thread Tracking
# =============================================================================

@router.post("/link-thread/{outreach_id}")
async def link_thread_to_outreach(
    outreach_id: int,
    request: LinkThreadRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Manually link a Gmail thread to an outreach record.

    Use this to track replies from previously sent emails.
    """
    if not gmail_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Gmail not authenticated")

    # Get the outreach record
    query = select(Outreach).where(Outreach.id == outreach_id)
    result = await session.execute(query)
    outreach = result.scalar_one_or_none()

    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach record not found")

    # Verify the thread exists
    messages = gmail_service.get_thread_messages(request.thread_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Gmail thread not found")

    # Update outreach with thread info
    outreach.gmail_thread_id = request.thread_id
    if request.message_id:
        outreach.gmail_message_id = request.message_id
    elif messages:
        # Use the first message ID if not provided
        outreach.gmail_message_id = messages[0].get('id')

    await session.commit()

    return {
        "message": "Thread linked successfully",
        "outreach_id": outreach_id,
        "thread_id": request.thread_id,
        "message_count": len(messages)
    }


@router.get("/tracked-threads")
async def get_tracked_threads(
    session: AsyncSession = Depends(get_session)
):
    """
    Get all outreach records that have Gmail threads linked.

    Returns outreach records with their thread status.
    """
    if not gmail_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Gmail not authenticated")

    # Get outreach records with gmail_thread_id
    query = (
        select(Outreach)
        .options(selectinload(Outreach.contact))
        .where(Outreach.gmail_thread_id.isnot(None))
        .order_by(Outreach.created_at.desc())
    )
    result = await session.execute(query)
    outreach_records = result.scalars().all()

    tracked = []
    for outreach in outreach_records:
        # Get latest thread info from Gmail
        messages = gmail_service.get_thread_messages(outreach.gmail_thread_id)
        reply_count = len(messages) - 1 if messages else 0  # Exclude original message

        tracked.append({
            "outreach_id": outreach.id,
            "contact_name": outreach.contact.name if outreach.contact else None,
            "contact_email": outreach.contact.email if outreach.contact else None,
            "subject": outreach.subject,
            "date_sent": outreach.date_sent.isoformat() if outreach.date_sent else None,
            "status": outreach.status,
            "thread_id": outreach.gmail_thread_id,
            "message_count": len(messages),
            "reply_count": reply_count,
            "has_new_replies": reply_count > 0 and not outreach.response_received
        })

    return {
        "tracked_threads": tracked,
        "count": len(tracked)
    }


@router.get("/check-replies/{outreach_id}")
async def check_replies_for_outreach(
    outreach_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Check for new replies to a specific outreach thread.

    Returns all messages in the thread.
    """
    if not gmail_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Gmail not authenticated")

    # Get the outreach record
    query = (
        select(Outreach)
        .options(selectinload(Outreach.contact))
        .where(Outreach.id == outreach_id)
    )
    result = await session.execute(query)
    outreach = result.scalar_one_or_none()

    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach record not found")

    if not outreach.gmail_thread_id:
        return {
            "message": "No Gmail thread linked to this outreach",
            "has_thread": False
        }

    # Get thread messages
    messages = gmail_service.get_thread_messages(outreach.gmail_thread_id)

    # Identify which are replies (not from us)
    # Simple heuristic: messages not matching our sent message ID are replies
    replies = [
        {
            "id": msg['id'],
            "from_address": msg.get('from', ''),
            "to_address": msg.get('to', ''),
            "subject": msg.get('subject', ''),
            "date": msg.get('date', ''),
            "body": msg.get('body', ''),
            "snippet": msg.get('snippet', ''),
            "is_reply": msg['id'] != outreach.gmail_message_id
        }
        for msg in messages
    ]

    return {
        "outreach_id": outreach_id,
        "contact_name": outreach.contact.name if outreach.contact else None,
        "subject": outreach.subject,
        "thread_id": outreach.gmail_thread_id,
        "messages": replies,
        "total_messages": len(messages),
        "reply_count": sum(1 for r in replies if r['is_reply']),
        "has_thread": True
    }


@router.post("/check-all-replies")
async def check_all_tracked_replies(
    session: AsyncSession = Depends(get_session)
):
    """
    Check for new replies across all tracked outreach threads.

    Updates outreach records that have new responses.
    """
    if not gmail_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Gmail not authenticated")

    # Get all outreach with threads that haven't been marked as responded
    query = (
        select(Outreach)
        .options(selectinload(Outreach.contact))
        .where(
            Outreach.gmail_thread_id.isnot(None),
            Outreach.response_received == False
        )
    )
    result = await session.execute(query)
    outreach_records = result.scalars().all()

    new_replies = []
    for outreach in outreach_records:
        messages = gmail_service.get_thread_messages(outreach.gmail_thread_id)

        # Check if there are replies (more than just our sent message)
        if len(messages) > 1:
            # Find the latest reply that isn't our sent message
            for msg in reversed(messages):
                if msg['id'] != outreach.gmail_message_id:
                    new_replies.append({
                        "outreach_id": outreach.id,
                        "contact_name": outreach.contact.name if outreach.contact else None,
                        "subject": outreach.subject,
                        "reply_from": msg.get('from', ''),
                        "reply_date": msg.get('date', ''),
                        "reply_snippet": msg.get('snippet', '')
                    })
                    break

    return {
        "new_replies": new_replies,
        "count": len(new_replies),
        "checked": len(outreach_records)
    }
