"""Artwork CRUD endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, case
from sqlalchemy.orm import selectinload

from src.database import Artwork, ArtworkImage, AcquisitionStatus, SourcePlatform, ArtworkExhibition, Exhibition, get_session_context

router = APIRouter()


class ArtworkResponse(BaseModel):
    """Response model for artwork data."""
    id: int
    title: str
    description: Optional[str]
    source_platform: str
    source_url: str
    price: Optional[float]
    currency: str
    location: Optional[str]
    confidence_score: float
    is_verified: bool
    acquisition_status: str
    positive_signals: Optional[dict] = None
    primary_image_url: Optional[str] = None

    # Catalog metadata fields
    medium: Optional[str] = None
    dimensions: Optional[str] = None
    dimensions_cm: Optional[str] = None
    year_created: Optional[int] = None
    year_created_circa: bool = False
    signed: Optional[str] = None
    inscription: Optional[str] = None
    provenance: Optional[str] = None
    exhibition_history: Optional[str] = None
    literature: Optional[str] = None
    condition: Optional[str] = None
    framed: Optional[bool] = None
    frame_description: Optional[str] = None
    subject_matter: Optional[str] = None
    category: Optional[str] = None
    art_type: Optional[str] = None
    notes: Optional[str] = None

    # Acquisition & Sales Tracking
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[datetime] = None
    last_sale_venue: Optional[str] = None
    last_known_owner: Optional[str] = None
    current_location: Optional[str] = None
    acquisition_priority: Optional[int] = None
    acquisition_notes: Optional[str] = None
    estimated_value: Optional[float] = None

    # Source URLs
    source_listing_url: Optional[str] = None
    last_sale_url: Optional[str] = None
    research_source_url: Optional[str] = None
    research_notes: Optional[str] = None

    class Config:
        from_attributes = True


class ArtworkUpdate(BaseModel):
    """Model for updating artwork fields."""
    # Status fields
    is_verified: Optional[bool] = None
    is_false_positive: Optional[bool] = None
    acquisition_status: Optional[AcquisitionStatus] = None
    notes: Optional[str] = None

    # Basic info
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None

    # Catalog metadata fields
    medium: Optional[str] = None
    dimensions: Optional[str] = None
    dimensions_cm: Optional[str] = None
    year_created: Optional[int] = None
    year_created_circa: Optional[bool] = None
    signed: Optional[str] = None
    inscription: Optional[str] = None
    provenance: Optional[str] = None
    exhibition_history: Optional[str] = None
    literature: Optional[str] = None
    condition: Optional[str] = None
    framed: Optional[bool] = None
    frame_description: Optional[str] = None
    subject_matter: Optional[str] = None
    category: Optional[str] = None

    # Acquisition & Sales Tracking
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[datetime] = None
    last_sale_venue: Optional[str] = None
    last_known_owner: Optional[str] = None
    current_location: Optional[str] = None
    acquisition_priority: Optional[int] = None
    acquisition_notes: Optional[str] = None
    estimated_value: Optional[float] = None

    # Source URLs
    source_listing_url: Optional[str] = None
    last_sale_url: Optional[str] = None
    research_source_url: Optional[str] = None
    research_notes: Optional[str] = None


def _get_image_url(img) -> str | None:
    """Get the best URL for an image, preferring local files."""
    from pathlib import Path

    # Check if local_path is set and file exists
    if img.local_path:
        local_path = Path(img.local_path)
        # Handle both absolute and relative paths
        if local_path.is_absolute():
            if local_path.exists():
                # Return serving URL for local file
                return f"/api/images/serve/{local_path.name}"
        else:
            # Relative path - check if exists from project root
            if local_path.exists():
                return f"/api/images/serve/{local_path.name}"

    # Fallback to external URL
    return img.url if img.url else None


def _artwork_to_response(artwork: Artwork) -> ArtworkResponse:
    """Convert artwork model to response, including primary image."""
    primary_image = None
    if artwork.images:
        for img in artwork.images:
            if img.is_primary:
                primary_image = _get_image_url(img)
                break
        if not primary_image and artwork.images:
            primary_image = _get_image_url(artwork.images[0])

    return ArtworkResponse(
        id=artwork.id,
        title=artwork.title,
        description=artwork.description,
        source_platform=artwork.source_platform,
        source_url=artwork.source_url,
        price=artwork.price,
        currency=artwork.currency,
        location=artwork.location,
        confidence_score=artwork.confidence_score,
        is_verified=artwork.is_verified,
        acquisition_status=artwork.acquisition_status,
        positive_signals=artwork.positive_signals,
        primary_image_url=primary_image,
        # Catalog metadata fields
        medium=artwork.medium,
        dimensions=artwork.dimensions,
        dimensions_cm=artwork.dimensions_cm,
        year_created=artwork.year_created,
        year_created_circa=artwork.year_created_circa or False,
        signed=artwork.signed,
        inscription=artwork.inscription,
        provenance=artwork.provenance,
        exhibition_history=artwork.exhibition_history,
        literature=artwork.literature,
        condition=artwork.condition,
        framed=artwork.framed,
        frame_description=artwork.frame_description,
        subject_matter=artwork.subject_matter,
        category=artwork.category,
        art_type=artwork.art_type,
        notes=artwork.notes,
        # Acquisition & Sales Tracking
        last_sale_price=artwork.last_sale_price,
        last_sale_date=artwork.last_sale_date,
        last_sale_venue=artwork.last_sale_venue,
        last_known_owner=artwork.last_known_owner,
        current_location=artwork.current_location,
        acquisition_priority=artwork.acquisition_priority,
        acquisition_notes=artwork.acquisition_notes,
        estimated_value=artwork.estimated_value,
        # Source URLs
        source_listing_url=artwork.source_listing_url,
        last_sale_url=artwork.last_sale_url,
        research_source_url=artwork.research_source_url,
        research_notes=artwork.research_notes,
    )


@router.get("/", response_model=list[ArtworkResponse])
async def list_artworks(
    status: Optional[AcquisitionStatus] = None,
    verified_only: bool = False,
    unverified_only: bool = False,
    include_false_positives: bool = False,
    art_type: Optional[str] = Query(None, description="Filter by art type (Painting, Book Cover, Lithograph, etc.)"),
    sort_by: str = Query(default="images_first", description="Sort order: images_first, date, confidence"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    limit: int = Query(default=50, le=200),
    offset: int = 0,
) -> list[ArtworkResponse]:
    """List artworks with optional filtering."""
    async with get_session_context() as session:
        query = select(Artwork).options(selectinload(Artwork.images))

        if status:
            query = query.where(Artwork.acquisition_status == status.value)

        if verified_only:
            query = query.where(Artwork.is_verified == True)

        if unverified_only:
            query = query.where(Artwork.is_verified == False)

        if not include_false_positives:
            query = query.where(Artwork.is_false_positive == False)

        # Art type filter
        if art_type:
            query = query.where(Artwork.art_type == art_type)

        # Search filter
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Artwork.title.ilike(search_term)) |
                (Artwork.description.ilike(search_term))
            )

        # Sorting options
        if sort_by == "images_first":
            # Subquery to check if artwork has images
            has_image = (
                select(func.count(ArtworkImage.id))
                .where(ArtworkImage.artwork_id == Artwork.id)
                .correlate(Artwork)
                .scalar_subquery()
            )
            query = query.order_by(
                has_image.desc(),  # Artworks with images first
                Artwork.is_verified.desc(),  # Then verified
                Artwork.confidence_score.desc(),  # Then by confidence
                Artwork.date_found.desc()  # Then by date
            )
        elif sort_by == "confidence":
            query = query.order_by(Artwork.confidence_score.desc(), Artwork.date_found.desc())
        else:  # date
            query = query.order_by(Artwork.date_found.desc())

        query = query.offset(offset).limit(limit)

        result = await session.execute(query)
        artworks = result.scalars().all()

        return [_artwork_to_response(a) for a in artworks]


@router.get("/{artwork_id}", response_model=ArtworkResponse)
async def get_artwork(artwork_id: int) -> ArtworkResponse:
    """Get a specific artwork by ID."""
    async with get_session_context() as session:
        result = await session.execute(
            select(Artwork)
            .options(selectinload(Artwork.images))
            .where(Artwork.id == artwork_id)
        )
        artwork = result.scalar_one_or_none()

        if not artwork:
            raise HTTPException(status_code=404, detail="Artwork not found")

        return _artwork_to_response(artwork)


@router.patch("/{artwork_id}", response_model=ArtworkResponse)
async def update_artwork(artwork_id: int, update: ArtworkUpdate) -> ArtworkResponse:
    """Update artwork status or notes."""
    async with get_session_context() as session:
        result = await session.execute(
            select(Artwork).where(Artwork.id == artwork_id)
        )
        artwork = result.scalar_one_or_none()

        if not artwork:
            raise HTTPException(status_code=404, detail="Artwork not found")

        update_data = update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "acquisition_status" and value:
                value = value.value
            setattr(artwork, field, value)

        await session.commit()
        await session.refresh(artwork)

        return ArtworkResponse.model_validate(artwork)


# --- Manual Artwork Entry ---

class ArtworkCreate(BaseModel):
    """Model for creating a new artwork manually."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    price: Optional[float] = None
    currency: str = "USD"
    location: Optional[str] = None
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    notes: Optional[str] = None
    is_verified: bool = True  # Manual entries are typically verified

    # Catalog metadata fields
    medium: Optional[str] = None
    dimensions: Optional[str] = None
    dimensions_cm: Optional[str] = None
    year_created: Optional[int] = None
    year_created_circa: bool = False
    signed: Optional[str] = None
    inscription: Optional[str] = None
    provenance: Optional[str] = None
    exhibition_history: Optional[str] = None
    literature: Optional[str] = None
    condition: Optional[str] = None
    framed: Optional[bool] = None
    frame_description: Optional[str] = None
    subject_matter: Optional[str] = None
    category: Optional[str] = None

    # Acquisition & Sales Tracking
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[datetime] = None
    last_sale_venue: Optional[str] = None
    last_known_owner: Optional[str] = None
    current_location: Optional[str] = None
    acquisition_priority: Optional[int] = None
    acquisition_notes: Optional[str] = None
    estimated_value: Optional[float] = None

    # Source URLs
    source_listing_url: Optional[str] = None
    last_sale_url: Optional[str] = None
    research_source_url: Optional[str] = None
    research_notes: Optional[str] = None


@router.post("/", response_model=ArtworkResponse)
async def create_artwork(artwork_data: ArtworkCreate) -> ArtworkResponse:
    """Create a new artwork manually."""
    async with get_session_context() as session:
        # Generate a unique source URL if not provided
        source_url = artwork_data.source_url or f"manual://{datetime.utcnow().timestamp()}"

        # Check for duplicate source URL
        existing = await session.execute(
            select(Artwork).where(Artwork.source_url == source_url)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Artwork with this source URL already exists")

        # Build positive signals for backward compatibility (legacy field)
        positive_signals = {}
        if artwork_data.medium:
            positive_signals["medium"] = artwork_data.medium
        if artwork_data.category:
            positive_signals["category"] = artwork_data.category
        if artwork_data.dimensions:
            positive_signals["dimensions"] = artwork_data.dimensions

        # Create artwork with all catalog metadata fields
        artwork = Artwork(
            title=artwork_data.title,
            description=artwork_data.description,
            source_platform=SourcePlatform.MANUAL.value,
            source_url=source_url,
            price=artwork_data.price,
            currency=artwork_data.currency,
            location=artwork_data.location,
            confidence_score=5.0,  # Manual entries get high confidence
            positive_signals=positive_signals if positive_signals else None,
            is_verified=artwork_data.is_verified,
            acquisition_status=AcquisitionStatus.NEW.value,
            notes=artwork_data.notes,
            date_found=datetime.utcnow(),
            # Catalog metadata fields
            medium=artwork_data.medium,
            dimensions=artwork_data.dimensions,
            dimensions_cm=artwork_data.dimensions_cm,
            year_created=artwork_data.year_created,
            year_created_circa=artwork_data.year_created_circa,
            signed=artwork_data.signed,
            inscription=artwork_data.inscription,
            provenance=artwork_data.provenance,
            exhibition_history=artwork_data.exhibition_history,
            literature=artwork_data.literature,
            condition=artwork_data.condition,
            framed=artwork_data.framed,
            frame_description=artwork_data.frame_description,
            subject_matter=artwork_data.subject_matter,
            category=artwork_data.category,
            # Acquisition & Sales Tracking
            last_sale_price=artwork_data.last_sale_price,
            last_sale_date=artwork_data.last_sale_date,
            last_sale_venue=artwork_data.last_sale_venue,
            last_known_owner=artwork_data.last_known_owner,
            current_location=artwork_data.current_location,
            acquisition_priority=artwork_data.acquisition_priority,
            acquisition_notes=artwork_data.acquisition_notes,
            estimated_value=artwork_data.estimated_value,
            # Source URLs
            source_listing_url=artwork_data.source_listing_url,
            last_sale_url=artwork_data.last_sale_url,
            research_source_url=artwork_data.research_source_url,
            research_notes=artwork_data.research_notes,
        )
        session.add(artwork)
        await session.flush()

        # Add image if provided
        if artwork_data.image_url:
            image = ArtworkImage(
                artwork_id=artwork.id,
                url=artwork_data.image_url,
                is_primary=True,
            )
            session.add(image)

        await session.commit()
        await session.refresh(artwork)

        # Load images relationship
        result = await session.execute(
            select(Artwork)
            .options(selectinload(Artwork.images))
            .where(Artwork.id == artwork.id)
        )
        artwork = result.scalar_one()

        return _artwork_to_response(artwork)


# --- Bulk Actions ---

class BulkActionRequest(BaseModel):
    """Request for bulk actions on artworks."""
    artwork_ids: List[int]
    action: str = Field(..., description="Action: verify, reject, delete, set_status")
    status: Optional[AcquisitionStatus] = None  # For set_status action


class BulkActionResponse(BaseModel):
    """Response for bulk actions."""
    success: bool
    affected: int
    message: str


@router.post("/bulk", response_model=BulkActionResponse)
async def bulk_action(request: BulkActionRequest) -> BulkActionResponse:
    """Perform bulk actions on multiple artworks."""
    if not request.artwork_ids:
        raise HTTPException(status_code=400, detail="No artwork IDs provided")

    async with get_session_context() as session:
        result = await session.execute(
            select(Artwork).where(Artwork.id.in_(request.artwork_ids))
        )
        artworks = result.scalars().all()

        if not artworks:
            raise HTTPException(status_code=404, detail="No artworks found")

        affected = 0
        for artwork in artworks:
            if request.action == "verify":
                artwork.is_verified = True
                artwork.is_false_positive = False
                affected += 1
            elif request.action == "reject":
                artwork.is_false_positive = True
                affected += 1
            elif request.action == "delete":
                await session.delete(artwork)
                affected += 1
            elif request.action == "set_status" and request.status:
                artwork.acquisition_status = request.status.value
                affected += 1

        await session.commit()

        return BulkActionResponse(
            success=True,
            affected=affected,
            message=f"Successfully applied '{request.action}' to {affected} artwork(s)"
        )


# --- Export ---

@router.get("/export/json")
async def export_artworks_json(
    verified_only: bool = False,
    include_false_positives: bool = False,
):
    """Export artworks as JSON."""
    async with get_session_context() as session:
        query = select(Artwork).options(selectinload(Artwork.images))

        if verified_only:
            query = query.where(Artwork.is_verified == True)

        if not include_false_positives:
            query = query.where(Artwork.is_false_positive == False)

        query = query.order_by(Artwork.title)

        result = await session.execute(query)
        artworks = result.scalars().all()

        export_data = []
        for artwork in artworks:
            images = [{"url": img.url, "is_primary": img.is_primary} for img in artwork.images]
            export_data.append({
                "id": artwork.id,
                "title": artwork.title,
                "description": artwork.description,
                "source_platform": artwork.source_platform,
                "source_url": artwork.source_url,
                "price": artwork.price,
                "currency": artwork.currency,
                "location": artwork.location,
                "confidence_score": artwork.confidence_score,
                "positive_signals": artwork.positive_signals,
                "is_verified": artwork.is_verified,
                "acquisition_status": artwork.acquisition_status,
                "date_found": artwork.date_found.isoformat() if artwork.date_found else None,
                "notes": artwork.notes,
                "images": images,
                # Catalog metadata fields
                "medium": artwork.medium,
                "dimensions": artwork.dimensions,
                "dimensions_cm": artwork.dimensions_cm,
                "year_created": artwork.year_created,
                "year_created_circa": artwork.year_created_circa,
                "signed": artwork.signed,
                "inscription": artwork.inscription,
                "provenance": artwork.provenance,
                "exhibition_history": artwork.exhibition_history,
                "literature": artwork.literature,
                "condition": artwork.condition,
                "framed": artwork.framed,
                "frame_description": artwork.frame_description,
                "subject_matter": artwork.subject_matter,
                "category": artwork.category,
            })

        return {"count": len(export_data), "artworks": export_data}


@router.get("/export/csv")
async def export_artworks_csv(
    verified_only: bool = False,
    include_false_positives: bool = False,
):
    """Export artworks as CSV."""
    from fastapi.responses import StreamingResponse
    import csv
    import io

    async with get_session_context() as session:
        query = select(Artwork).options(selectinload(Artwork.images))

        if verified_only:
            query = query.where(Artwork.is_verified == True)

        if not include_false_positives:
            query = query.where(Artwork.is_false_positive == False)

        query = query.order_by(Artwork.title)

        result = await session.execute(query)
        artworks = result.scalars().all()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Header with all catalog fields
        writer.writerow([
            "ID", "Title", "Description", "Medium", "Dimensions", "Dimensions (cm)",
            "Year Created", "Year Circa", "Signed", "Inscription",
            "Category", "Subject Matter", "Condition", "Framed", "Frame Description",
            "Provenance", "Exhibition History", "Literature",
            "Price", "Currency", "Location", "Platform", "URL",
            "Verified", "Status", "Date Found", "Primary Image", "Notes"
        ])

        # Data rows
        for artwork in artworks:
            primary_image = next((img.url for img in artwork.images if img.is_primary), "")
            if not primary_image and artwork.images:
                primary_image = artwork.images[0].url

            writer.writerow([
                artwork.id,
                artwork.title,
                artwork.description or "",
                artwork.medium or "",
                artwork.dimensions or "",
                artwork.dimensions_cm or "",
                artwork.year_created or "",
                "Yes" if artwork.year_created_circa else "",
                artwork.signed or "",
                artwork.inscription or "",
                artwork.category or "",
                artwork.subject_matter or "",
                artwork.condition or "",
                "Yes" if artwork.framed else ("No" if artwork.framed is False else ""),
                artwork.frame_description or "",
                artwork.provenance or "",
                artwork.exhibition_history or "",
                artwork.literature or "",
                artwork.price or "",
                artwork.currency,
                artwork.location or "",
                artwork.source_platform,
                artwork.source_url,
                "Yes" if artwork.is_verified else "No",
                artwork.acquisition_status,
                artwork.date_found.strftime("%Y-%m-%d") if artwork.date_found else "",
                primary_image,
                artwork.notes or "",
            ])

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=dan_brown_artworks.csv"}
        )


# --- Artwork Exhibitions (must be after /export routes due to path param matching) ---

@router.get("/{artwork_id}/exhibitions")
async def get_artwork_exhibitions(artwork_id: int):
    """Get all exhibitions where this artwork was shown."""
    async with get_session_context() as session:
        # First verify artwork exists
        artwork_result = await session.execute(
            select(Artwork).where(Artwork.id == artwork_id)
        )
        artwork = artwork_result.scalar_one_or_none()
        if not artwork:
            raise HTTPException(status_code=404, detail="Artwork not found")

        # Get exhibitions linked to this artwork
        result = await session.execute(
            select(ArtworkExhibition, Exhibition)
            .join(Exhibition, ArtworkExhibition.exhibition_id == Exhibition.id)
            .where(ArtworkExhibition.artwork_id == artwork_id)
            .order_by(Exhibition.year.desc())
        )
        rows = result.all()

        exhibitions = []
        for artwork_exhibition, exhibition in rows:
            exhibitions.append({
                "id": exhibition.id,
                "title": exhibition.title,
                "venue_name": exhibition.venue_name,
                "venue_city": exhibition.venue_city,
                "venue_state": exhibition.venue_state,
                "year": exhibition.year,
                "is_solo": exhibition.is_solo,
                "catalog_number": artwork_exhibition.catalog_number,
                "was_sold": artwork_exhibition.was_sold,
                "sale_price": artwork_exhibition.sale_price,
                "notes": artwork_exhibition.notes,
            })

        return {"artwork_id": artwork_id, "exhibitions": exhibitions, "count": len(exhibitions)}
