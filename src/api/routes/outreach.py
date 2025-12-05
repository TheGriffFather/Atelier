"""API routes for outreach tracking."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import (
    Contact, Outreach, ContactType, OutreachType, OutreachStatus,
    ResearchLead, LeadStatus, LeadPriority, LeadCategory
)
from src.database.session import get_session

router = APIRouter(prefix="/api/outreach", tags=["outreach"])


# =============================================================================
# Pydantic Models
# =============================================================================

class ContactCreate(BaseModel):
    """Create a new contact."""
    name: str
    organization: Optional[str] = None
    contact_type: str = ContactType.OTHER.value
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "USA"
    connection_notes: Optional[str] = None
    target_artworks: Optional[str] = None
    priority: int = 3
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    """Update an existing contact."""
    name: Optional[str] = None
    organization: Optional[str] = None
    contact_type: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    connection_notes: Optional[str] = None
    target_artworks: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class OutreachCreate(BaseModel):
    """Create a new outreach record."""
    contact_id: int
    outreach_type: str = OutreachType.EMAIL.value
    status: str = OutreachStatus.DRAFT.value
    subject: Optional[str] = None
    content: Optional[str] = None
    template_used: Optional[str] = None
    date_sent: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    requesting_images: bool = False
    requesting_metadata: bool = False
    requesting_provenance: bool = False
    requesting_attribution: bool = False
    request_details: Optional[str] = None
    notes: Optional[str] = None


class OutreachUpdate(BaseModel):
    """Update an existing outreach record."""
    outreach_type: Optional[str] = None
    status: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    template_used: Optional[str] = None
    date_sent: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    response_received: Optional[bool] = None
    response_date: Optional[datetime] = None
    response_content: Optional[str] = None
    response_summary: Optional[str] = None
    outcome: Optional[str] = None
    images_received: Optional[bool] = None
    metadata_received: Optional[bool] = None
    leads_received: Optional[bool] = None
    requesting_images: Optional[bool] = None
    requesting_metadata: Optional[bool] = None
    requesting_provenance: Optional[bool] = None
    requesting_attribution: Optional[bool] = None
    request_details: Optional[str] = None
    notes: Optional[str] = None


class ContactResponse(BaseModel):
    """Contact response model."""
    id: int
    name: str
    organization: Optional[str]
    contact_type: str
    role: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    website: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: str
    connection_notes: Optional[str]
    target_artworks: Optional[str]
    priority: int
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    outreach_count: int = 0
    last_outreach_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class OutreachResponse(BaseModel):
    """Outreach response model."""
    id: int
    contact_id: int
    contact_name: str
    outreach_type: str
    status: str
    subject: Optional[str]
    content: Optional[str]
    template_used: Optional[str]
    date_sent: Optional[datetime]
    follow_up_date: Optional[datetime]
    response_received: bool
    response_date: Optional[datetime]
    response_content: Optional[str]
    response_summary: Optional[str]
    outcome: Optional[str]
    images_received: bool
    metadata_received: bool
    leads_received: bool
    requesting_images: bool
    requesting_metadata: bool
    requesting_provenance: bool
    requesting_attribution: bool
    request_details: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    gmail_message_id: Optional[str] = None
    gmail_thread_id: Optional[str] = None

    class Config:
        from_attributes = True


class OutreachStats(BaseModel):
    """Statistics about outreach efforts."""
    total_contacts: int
    total_outreach: int
    sent: int
    awaiting_response: int
    responded: int
    follow_up_needed: int
    images_received: int
    metadata_received: int


# =============================================================================
# Contact Routes
# =============================================================================

@router.get("/contacts")
async def list_contacts(
    contact_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    priority_min: Optional[int] = None,
    session: AsyncSession = Depends(get_session)
):
    """List all contacts with optional filtering."""
    query = select(Contact)

    if contact_type:
        query = query.where(Contact.contact_type == contact_type)
    if is_active is not None:
        query = query.where(Contact.is_active == is_active)
    if priority_min:
        query = query.where(Contact.priority >= priority_min)

    query = query.order_by(Contact.priority.desc(), Contact.name)

    result = await session.execute(query)
    contacts = result.scalars().all()

    # Get outreach counts for each contact
    contact_list = []
    for contact in contacts:
        # Count outreach records
        count_query = select(func.count(Outreach.id)).where(Outreach.contact_id == contact.id)
        count_result = await session.execute(count_query)
        outreach_count = count_result.scalar() or 0

        # Get last outreach date
        last_query = select(Outreach.date_sent).where(
            Outreach.contact_id == contact.id,
            Outreach.date_sent.isnot(None)
        ).order_by(Outreach.date_sent.desc()).limit(1)
        last_result = await session.execute(last_query)
        last_date = last_result.scalar()

        contact_dict = {
            "id": contact.id,
            "name": contact.name,
            "organization": contact.organization,
            "contact_type": contact.contact_type,
            "role": contact.role,
            "email": contact.email,
            "phone": contact.phone,
            "address": contact.address,
            "website": contact.website,
            "city": contact.city,
            "state": contact.state,
            "country": contact.country,
            "connection_notes": contact.connection_notes,
            "target_artworks": contact.target_artworks,
            "priority": contact.priority,
            "is_active": contact.is_active,
            "notes": contact.notes,
            "created_at": contact.created_at,
            "updated_at": contact.updated_at,
            "outreach_count": outreach_count,
            "last_outreach_date": last_date
        }
        contact_list.append(contact_dict)

    return contact_list


@router.get("/contacts/{contact_id}")
async def get_contact(contact_id: int, session: AsyncSession = Depends(get_session)):
    """Get a single contact with their outreach history."""
    query = select(Contact).where(Contact.id == contact_id).options(
        selectinload(Contact.outreach_records)
    )
    result = await session.execute(query)
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return {
        "contact": {
            "id": contact.id,
            "name": contact.name,
            "organization": contact.organization,
            "contact_type": contact.contact_type,
            "role": contact.role,
            "email": contact.email,
            "phone": contact.phone,
            "address": contact.address,
            "website": contact.website,
            "city": contact.city,
            "state": contact.state,
            "country": contact.country,
            "connection_notes": contact.connection_notes,
            "target_artworks": contact.target_artworks,
            "priority": contact.priority,
            "is_active": contact.is_active,
            "notes": contact.notes,
            "created_at": contact.created_at,
            "updated_at": contact.updated_at,
        },
        "outreach_history": [
            {
                "id": o.id,
                "outreach_type": o.outreach_type,
                "status": o.status,
                "subject": o.subject,
                "date_sent": o.date_sent,
                "follow_up_date": o.follow_up_date,
                "response_received": o.response_received,
                "response_date": o.response_date,
            }
            for o in sorted(contact.outreach_records, key=lambda x: x.created_at, reverse=True)
        ]
    }


@router.post("/contacts")
async def create_contact(contact: ContactCreate, session: AsyncSession = Depends(get_session)):
    """Create a new contact."""
    db_contact = Contact(**contact.model_dump())
    session.add(db_contact)
    await session.commit()
    await session.refresh(db_contact)
    return {"id": db_contact.id, "message": "Contact created successfully"}


@router.patch("/contacts/{contact_id}")
async def update_contact(
    contact_id: int,
    updates: ContactUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update a contact."""
    query = select(Contact).where(Contact.id == contact_id)
    result = await session.execute(query)
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(contact, key, value)

    contact.updated_at = datetime.utcnow()
    await session.commit()

    return {"message": "Contact updated successfully"}


@router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: int, session: AsyncSession = Depends(get_session)):
    """Delete a contact and all associated outreach records."""
    query = select(Contact).where(Contact.id == contact_id)
    result = await session.execute(query)
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    await session.delete(contact)
    await session.commit()

    return {"message": "Contact deleted successfully"}


# =============================================================================
# Outreach Routes
# =============================================================================

@router.get("/records")
async def list_outreach(
    status: Optional[str] = None,
    outreach_type: Optional[str] = None,
    contact_id: Optional[int] = None,
    needs_follow_up: Optional[bool] = None,
    session: AsyncSession = Depends(get_session)
):
    """List all outreach records with optional filtering."""
    query = select(Outreach).options(selectinload(Outreach.contact))

    if status:
        query = query.where(Outreach.status == status)
    if outreach_type:
        query = query.where(Outreach.outreach_type == outreach_type)
    if contact_id:
        query = query.where(Outreach.contact_id == contact_id)
    if needs_follow_up:
        query = query.where(
            Outreach.follow_up_date.isnot(None),
            Outreach.follow_up_date <= datetime.utcnow(),
            Outreach.status.in_([
                OutreachStatus.SENT.value,
                OutreachStatus.AWAITING_RESPONSE.value,
                OutreachStatus.FOLLOW_UP_NEEDED.value
            ])
        )

    query = query.order_by(Outreach.created_at.desc())

    result = await session.execute(query)
    outreach_list = result.scalars().all()

    return [
        {
            "id": o.id,
            "contact_id": o.contact_id,
            "contact_name": o.contact.name if o.contact else "Unknown",
            "outreach_type": o.outreach_type,
            "status": o.status,
            "subject": o.subject,
            "content": o.content,
            "template_used": o.template_used,
            "date_sent": o.date_sent,
            "follow_up_date": o.follow_up_date,
            "response_received": o.response_received,
            "response_date": o.response_date,
            "response_content": o.response_content,
            "response_summary": o.response_summary,
            "outcome": o.outcome,
            "images_received": o.images_received,
            "metadata_received": o.metadata_received,
            "leads_received": o.leads_received,
            "requesting_images": o.requesting_images,
            "requesting_metadata": o.requesting_metadata,
            "requesting_provenance": o.requesting_provenance,
            "requesting_attribution": o.requesting_attribution,
            "request_details": o.request_details,
            "notes": o.notes,
            "created_at": o.created_at,
            "updated_at": o.updated_at,
            "gmail_message_id": o.gmail_message_id,
            "gmail_thread_id": o.gmail_thread_id,
        }
        for o in outreach_list
    ]


@router.get("/records/{outreach_id}")
async def get_outreach(outreach_id: int, session: AsyncSession = Depends(get_session)):
    """Get a single outreach record."""
    query = select(Outreach).where(Outreach.id == outreach_id).options(
        selectinload(Outreach.contact)
    )
    result = await session.execute(query)
    outreach = result.scalar_one_or_none()

    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach record not found")

    return {
        "id": outreach.id,
        "contact_id": outreach.contact_id,
        "contact_name": outreach.contact.name if outreach.contact else "Unknown",
        "outreach_type": outreach.outreach_type,
        "status": outreach.status,
        "subject": outreach.subject,
        "content": outreach.content,
        "template_used": outreach.template_used,
        "date_sent": outreach.date_sent,
        "follow_up_date": outreach.follow_up_date,
        "response_received": outreach.response_received,
        "response_date": outreach.response_date,
        "response_content": outreach.response_content,
        "response_summary": outreach.response_summary,
        "outcome": outreach.outcome,
        "images_received": outreach.images_received,
        "metadata_received": outreach.metadata_received,
        "leads_received": outreach.leads_received,
        "requesting_images": outreach.requesting_images,
        "requesting_metadata": outreach.requesting_metadata,
        "requesting_provenance": outreach.requesting_provenance,
        "requesting_attribution": outreach.requesting_attribution,
        "request_details": outreach.request_details,
        "notes": outreach.notes,
        "created_at": outreach.created_at,
        "updated_at": outreach.updated_at,
    }


@router.post("/records")
async def create_outreach(outreach: OutreachCreate, session: AsyncSession = Depends(get_session)):
    """Create a new outreach record."""
    # Verify contact exists
    contact_query = select(Contact).where(Contact.id == outreach.contact_id)
    contact_result = await session.execute(contact_query)
    if not contact_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Contact not found")

    db_outreach = Outreach(**outreach.model_dump())
    session.add(db_outreach)
    await session.commit()
    await session.refresh(db_outreach)

    return {"id": db_outreach.id, "message": "Outreach record created successfully"}


@router.patch("/records/{outreach_id}")
async def update_outreach(
    outreach_id: int,
    updates: OutreachUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update an outreach record."""
    query = select(Outreach).where(Outreach.id == outreach_id)
    result = await session.execute(query)
    outreach = result.scalar_one_or_none()

    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach record not found")

    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(outreach, key, value)

    outreach.updated_at = datetime.utcnow()
    await session.commit()

    return {"message": "Outreach record updated successfully"}


@router.delete("/records/{outreach_id}")
async def delete_outreach(outreach_id: int, session: AsyncSession = Depends(get_session)):
    """Delete an outreach record."""
    query = select(Outreach).where(Outreach.id == outreach_id)
    result = await session.execute(query)
    outreach = result.scalar_one_or_none()

    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach record not found")

    await session.delete(outreach)
    await session.commit()

    return {"message": "Outreach record deleted successfully"}


# =============================================================================
# Stats & Dashboard
# =============================================================================

@router.get("/stats")
async def get_outreach_stats(session: AsyncSession = Depends(get_session)):
    """Get outreach statistics."""
    # Total contacts
    contacts_query = select(func.count(Contact.id))
    contacts_result = await session.execute(contacts_query)
    total_contacts = contacts_result.scalar() or 0

    # Total outreach
    outreach_query = select(func.count(Outreach.id))
    outreach_result = await session.execute(outreach_query)
    total_outreach = outreach_result.scalar() or 0

    # By status
    def count_by_status(status):
        return select(func.count(Outreach.id)).where(Outreach.status == status)

    sent_result = await session.execute(count_by_status(OutreachStatus.SENT.value))
    awaiting_result = await session.execute(count_by_status(OutreachStatus.AWAITING_RESPONSE.value))
    responded_result = await session.execute(count_by_status(OutreachStatus.RESPONDED.value))
    follow_up_result = await session.execute(count_by_status(OutreachStatus.FOLLOW_UP_NEEDED.value))

    # Outcomes
    images_query = select(func.count(Outreach.id)).where(Outreach.images_received == True)
    images_result = await session.execute(images_query)

    metadata_query = select(func.count(Outreach.id)).where(Outreach.metadata_received == True)
    metadata_result = await session.execute(metadata_query)

    # Pending follow-ups (have follow_up_date and not closed/responded)
    pending_followups_query = select(func.count(Outreach.id)).where(
        Outreach.follow_up_date.isnot(None),
        Outreach.status.in_([
            OutreachStatus.SENT.value,
            OutreachStatus.AWAITING_RESPONSE.value,
            OutreachStatus.FOLLOW_UP_NEEDED.value
        ])
    )
    pending_followups_result = await session.execute(pending_followups_query)

    # Received responses (response_received flag or responded status)
    received_responses_query = select(func.count(Outreach.id)).where(
        Outreach.response_received == True
    )
    received_responses_result = await session.execute(received_responses_query)

    return {
        "total_contacts": total_contacts,
        "total_outreach": total_outreach,
        "sent": sent_result.scalar() or 0,
        "awaiting_response": awaiting_result.scalar() or 0,
        "responded": responded_result.scalar() or 0,
        "received_responses": received_responses_result.scalar() or 0,
        "follow_up_needed": follow_up_result.scalar() or 0,
        "pending_followups": pending_followups_result.scalar() or 0,
        "images_received": images_result.scalar() or 0,
        "metadata_received": metadata_result.scalar() or 0,
    }


@router.get("/follow-ups")
async def get_pending_follow_ups(session: AsyncSession = Depends(get_session)):
    """Get outreach records that need follow-up."""
    query = select(Outreach).options(selectinload(Outreach.contact)).where(
        Outreach.follow_up_date.isnot(None),
        Outreach.status.in_([
            OutreachStatus.SENT.value,
            OutreachStatus.AWAITING_RESPONSE.value,
            OutreachStatus.FOLLOW_UP_NEEDED.value
        ])
    ).order_by(Outreach.follow_up_date)

    result = await session.execute(query)
    outreach_list = result.scalars().all()

    return [
        {
            "id": o.id,
            "contact_name": o.contact.name if o.contact else "Unknown",
            "subject": o.subject,
            "date_sent": o.date_sent,
            "follow_up_date": o.follow_up_date,
            "status": o.status,
            "is_overdue": o.follow_up_date <= datetime.utcnow() if o.follow_up_date else False,
        }
        for o in outreach_list
    ]


# =============================================================================
# Enum Values (for dropdowns)
# =============================================================================

@router.get("/enums")
async def get_enum_values():
    """Get all enum values for form dropdowns."""
    return {
        "contact_types": [e.value for e in ContactType],
        "outreach_types": [e.value for e in OutreachType],
        "outreach_statuses": [e.value for e in OutreachStatus],
        "lead_statuses": [e.value for e in LeadStatus],
        "lead_priorities": [e.value for e in LeadPriority],
        "lead_categories": [e.value for e in LeadCategory],
    }


# =============================================================================
# Research Lead Pydantic Models
# =============================================================================

class ResearchLeadCreate(BaseModel):
    """Create a new research lead."""
    title: str
    description: Optional[str] = None
    category: str = LeadCategory.OTHER.value
    priority: str = LeadPriority.MEDIUM.value
    status: str = LeadStatus.NEW.value
    source: Optional[str] = None
    source_date: Optional[datetime] = None
    next_action: Optional[str] = None
    search_terms: Optional[str] = None
    notes: Optional[str] = None


class ResearchLeadUpdate(BaseModel):
    """Update an existing research lead."""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    source_date: Optional[datetime] = None
    next_action: Optional[str] = None
    search_terms: Optional[str] = None
    found_artwork_id: Optional[int] = None
    resolved_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    notes: Optional[str] = None


# =============================================================================
# Research Lead Routes
# =============================================================================

@router.get("/leads")
async def list_research_leads(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    """List all research leads with optional filtering."""
    query = select(ResearchLead)

    if status:
        query = query.where(ResearchLead.status == status)
    if priority:
        query = query.where(ResearchLead.priority == priority)
    if category:
        query = query.where(ResearchLead.category == category)

    # Sort by priority (high first), then by status (new/investigating first)
    query = query.order_by(
        ResearchLead.priority.desc(),
        ResearchLead.status,
        ResearchLead.created_at.desc()
    )

    result = await session.execute(query)
    leads = result.scalars().all()

    return [
        {
            "id": lead.id,
            "title": lead.title,
            "description": lead.description,
            "category": lead.category,
            "priority": lead.priority,
            "status": lead.status,
            "source": lead.source,
            "source_date": lead.source_date,
            "next_action": lead.next_action,
            "search_terms": lead.search_terms,
            "found_artwork_id": lead.found_artwork_id,
            "resolved_date": lead.resolved_date,
            "resolution_notes": lead.resolution_notes,
            "notes": lead.notes,
            "created_at": lead.created_at,
            "updated_at": lead.updated_at,
        }
        for lead in leads
    ]


@router.get("/leads/{lead_id}")
async def get_research_lead(lead_id: int, session: AsyncSession = Depends(get_session)):
    """Get a single research lead."""
    query = select(ResearchLead).where(ResearchLead.id == lead_id)
    result = await session.execute(query)
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Research lead not found")

    return {
        "id": lead.id,
        "title": lead.title,
        "description": lead.description,
        "category": lead.category,
        "priority": lead.priority,
        "status": lead.status,
        "source": lead.source,
        "source_date": lead.source_date,
        "next_action": lead.next_action,
        "search_terms": lead.search_terms,
        "found_artwork_id": lead.found_artwork_id,
        "resolved_date": lead.resolved_date,
        "resolution_notes": lead.resolution_notes,
        "notes": lead.notes,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
    }


@router.post("/leads")
async def create_research_lead(lead: ResearchLeadCreate, session: AsyncSession = Depends(get_session)):
    """Create a new research lead."""
    db_lead = ResearchLead(**lead.model_dump())
    session.add(db_lead)
    await session.commit()
    await session.refresh(db_lead)
    return {"id": db_lead.id, "message": "Research lead created successfully"}


@router.patch("/leads/{lead_id}")
async def update_research_lead(
    lead_id: int,
    updates: ResearchLeadUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update a research lead."""
    query = select(ResearchLead).where(ResearchLead.id == lead_id)
    result = await session.execute(query)
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Research lead not found")

    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lead, key, value)

    lead.updated_at = datetime.utcnow()
    await session.commit()

    return {"message": "Research lead updated successfully"}


@router.delete("/leads/{lead_id}")
async def delete_research_lead(lead_id: int, session: AsyncSession = Depends(get_session)):
    """Delete a research lead."""
    query = select(ResearchLead).where(ResearchLead.id == lead_id)
    result = await session.execute(query)
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Research lead not found")

    await session.delete(lead)
    await session.commit()

    return {"message": "Research lead deleted successfully"}


@router.get("/leads/stats/summary")
async def get_research_lead_stats(session: AsyncSession = Depends(get_session)):
    """Get research lead statistics."""
    # Total leads
    total_query = select(func.count(ResearchLead.id))
    total_result = await session.execute(total_query)
    total_leads = total_result.scalar() or 0

    # By status
    def count_by_status(status):
        return select(func.count(ResearchLead.id)).where(ResearchLead.status == status)

    new_result = await session.execute(count_by_status(LeadStatus.NEW.value))
    investigating_result = await session.execute(count_by_status(LeadStatus.INVESTIGATING.value))
    contacted_result = await session.execute(count_by_status(LeadStatus.CONTACTED.value))
    resolved_result = await session.execute(count_by_status(LeadStatus.RESOLVED.value))
    dead_end_result = await session.execute(count_by_status(LeadStatus.DEAD_END.value))

    # By priority
    def count_by_priority(priority):
        return select(func.count(ResearchLead.id)).where(ResearchLead.priority == priority)

    high_result = await session.execute(count_by_priority(LeadPriority.HIGH.value))
    medium_result = await session.execute(count_by_priority(LeadPriority.MEDIUM.value))
    low_result = await session.execute(count_by_priority(LeadPriority.LOW.value))

    return {
        "total_leads": total_leads,
        "by_status": {
            "new": new_result.scalar() or 0,
            "investigating": investigating_result.scalar() or 0,
            "contacted": contacted_result.scalar() or 0,
            "resolved": resolved_result.scalar() or 0,
            "dead_end": dead_end_result.scalar() or 0,
        },
        "by_priority": {
            "high": high_result.scalar() or 0,
            "medium": medium_result.scalar() or 0,
            "low": low_result.scalar() or 0,
        }
    }
