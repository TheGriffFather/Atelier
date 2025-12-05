"""API routes for exhibition tracking."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.database import Exhibition, ArtworkExhibition, Artwork, ArtworkImage, get_session_context

router = APIRouter()


# =============================================================================
# Pydantic Models
# =============================================================================

class ExhibitionCreate(BaseModel):
    """Create a new exhibition."""
    year: int
    venue_name: str
    venue_city: Optional[str] = None
    venue_state: Optional[str] = None
    venue_country: str = "USA"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_solo: bool = False
    exhibition_type: Optional[str] = None  # gallery, museum, art fair
    title: Optional[str] = None
    description: Optional[str] = None
    curator: Optional[str] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None
    catalog_url: Optional[str] = None


class ExhibitionUpdate(BaseModel):
    """Update an existing exhibition."""
    year: Optional[int] = None
    venue_name: Optional[str] = None
    venue_city: Optional[str] = None
    venue_state: Optional[str] = None
    venue_country: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_solo: Optional[bool] = None
    exhibition_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    curator: Optional[str] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None
    catalog_url: Optional[str] = None


class ArtworkExhibitionLink(BaseModel):
    """Link artwork(s) to an exhibition."""
    artwork_ids: List[int]
    catalog_number: Optional[str] = None
    was_sold: bool = False
    sale_price: Optional[float] = None
    notes: Optional[str] = None


class ArtworkPreview(BaseModel):
    """Preview of an artwork for exhibition cards."""
    id: int
    title: str
    image_url: Optional[str] = None


class ExhibitionResponse(BaseModel):
    """Response model for exhibition data."""
    id: int
    year: int
    venue_name: str
    venue_city: Optional[str] = None
    venue_state: Optional[str] = None
    venue_country: str = "USA"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_solo: bool = False
    exhibition_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    curator: Optional[str] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None
    catalog_url: Optional[str] = None
    artwork_count: int = 0
    artworks: Optional[List[dict]] = None
    artwork_previews: Optional[List[ArtworkPreview]] = None  # For show cards with thumbnails

    class Config:
        from_attributes = True


# =============================================================================
# Exhibition CRUD Endpoints
# =============================================================================

@router.get("", response_model=List[ExhibitionResponse])
async def list_exhibitions(
    year: Optional[int] = Query(None, description="Filter by year"),
    venue: Optional[str] = Query(None, description="Filter by venue name (partial match)"),
    is_solo: Optional[bool] = Query(None, description="Filter solo shows only"),
    has_artworks: Optional[bool] = Query(None, description="Only shows with linked artworks"),
    include_previews: bool = Query(True, description="Include artwork preview images"),
    preview_limit: int = Query(4, ge=1, le=10, description="Max number of artwork previews"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List all exhibitions with optional filters."""
    async with get_session_context() as session:
        # Build query with artwork relationships
        query = select(Exhibition).options(
            selectinload(Exhibition.artworks_shown)
            .selectinload(ArtworkExhibition.artwork)
            .selectinload(Artwork.images)
        )

        # Apply filters
        if year is not None:
            query = query.where(Exhibition.year == year)
        if venue:
            query = query.where(Exhibition.venue_name.ilike(f"%{venue}%"))
        if is_solo is not None:
            query = query.where(Exhibition.is_solo == is_solo)

        # Order by year descending, then venue
        query = query.order_by(Exhibition.year.desc(), Exhibition.venue_name)

        # Pagination
        query = query.offset(offset).limit(limit)

        result = await session.execute(query)
        exhibitions = result.scalars().all()

        # Convert to response format
        response = []
        for ex in exhibitions:
            artwork_count = len(ex.artworks_shown) if ex.artworks_shown else 0

            # Filter by has_artworks if specified
            if has_artworks is True and artwork_count == 0:
                continue
            if has_artworks is False and artwork_count > 0:
                continue

            # Build artwork previews (up to preview_limit, prioritizing those with images)
            artwork_previews = None
            if include_previews and ex.artworks_shown:
                previews = []
                # Sort artworks: those with images first
                sorted_artworks = sorted(
                    ex.artworks_shown,
                    key=lambda ae: 0 if (ae.artwork and ae.artwork.images) else 1
                )
                for ae in sorted_artworks[:preview_limit]:
                    artwork = ae.artwork
                    if artwork:
                        # Get primary image URL
                        image_url = None
                        if artwork.images:
                            primary = next((img for img in artwork.images if img.is_primary), None)
                            if primary:
                                image_url = primary.url
                            elif artwork.images:
                                image_url = artwork.images[0].url
                        previews.append(ArtworkPreview(
                            id=artwork.id,
                            title=artwork.title,
                            image_url=image_url
                        ))
                artwork_previews = previews if previews else None

            response.append(ExhibitionResponse(
                id=ex.id,
                year=ex.year,
                venue_name=ex.venue_name,
                venue_city=ex.venue_city,
                venue_state=ex.venue_state,
                venue_country=ex.venue_country or "USA",
                start_date=ex.start_date,
                end_date=ex.end_date,
                is_solo=ex.is_solo,
                exhibition_type=ex.exhibition_type,
                title=ex.title,
                description=ex.description,
                curator=ex.curator,
                notes=ex.notes,
                source_url=ex.source_url,
                catalog_url=ex.catalog_url,
                artwork_count=artwork_count,
                artwork_previews=artwork_previews,
            ))

        return response


@router.get("/{exhibition_id}", response_model=ExhibitionResponse)
async def get_exhibition(exhibition_id: int):
    """Get a single exhibition with its linked artworks."""
    async with get_session_context() as session:
        query = (
            select(Exhibition)
            .where(Exhibition.id == exhibition_id)
            .options(
                selectinload(Exhibition.artworks_shown)
                .selectinload(ArtworkExhibition.artwork)
            )
        )
        result = await session.execute(query)
        exhibition = result.scalar_one_or_none()

        if not exhibition:
            raise HTTPException(status_code=404, detail="Exhibition not found")

        # Build artworks list
        artworks_list = []
        if exhibition.artworks_shown:
            for ae in exhibition.artworks_shown:
                artwork = ae.artwork
                artworks_list.append({
                    "id": artwork.id,
                    "title": artwork.title,
                    "medium": artwork.medium,
                    "catalog_number": ae.catalog_number,
                    "was_sold": ae.was_sold,
                    "sale_price": ae.sale_price,
                    "notes": ae.notes,
                })

        return ExhibitionResponse(
            id=exhibition.id,
            year=exhibition.year,
            venue_name=exhibition.venue_name,
            venue_city=exhibition.venue_city,
            venue_state=exhibition.venue_state,
            venue_country=exhibition.venue_country or "USA",
            start_date=exhibition.start_date,
            end_date=exhibition.end_date,
            is_solo=exhibition.is_solo,
            exhibition_type=exhibition.exhibition_type,
            title=exhibition.title,
            description=exhibition.description,
            curator=exhibition.curator,
            notes=exhibition.notes,
            source_url=exhibition.source_url,
            catalog_url=exhibition.catalog_url,
            artwork_count=len(artworks_list),
            artworks=artworks_list,
        )


@router.post("", response_model=ExhibitionResponse)
async def create_exhibition(data: ExhibitionCreate):
    """Create a new exhibition."""
    async with get_session_context() as session:
        exhibition = Exhibition(
            year=data.year,
            venue_name=data.venue_name,
            venue_city=data.venue_city,
            venue_state=data.venue_state,
            venue_country=data.venue_country,
            start_date=data.start_date,
            end_date=data.end_date,
            is_solo=data.is_solo,
            exhibition_type=data.exhibition_type,
            title=data.title,
            description=data.description,
            curator=data.curator,
            notes=data.notes,
            source_url=data.source_url,
            catalog_url=data.catalog_url,
        )
        session.add(exhibition)
        await session.commit()
        await session.refresh(exhibition)

        return ExhibitionResponse(
            id=exhibition.id,
            year=exhibition.year,
            venue_name=exhibition.venue_name,
            venue_city=exhibition.venue_city,
            venue_state=exhibition.venue_state,
            venue_country=exhibition.venue_country or "USA",
            start_date=exhibition.start_date,
            end_date=exhibition.end_date,
            is_solo=exhibition.is_solo,
            exhibition_type=exhibition.exhibition_type,
            title=exhibition.title,
            description=exhibition.description,
            curator=exhibition.curator,
            notes=exhibition.notes,
            source_url=exhibition.source_url,
            catalog_url=exhibition.catalog_url,
            artwork_count=0,
        )


@router.patch("/{exhibition_id}", response_model=ExhibitionResponse)
async def update_exhibition(exhibition_id: int, data: ExhibitionUpdate):
    """Update an existing exhibition."""
    async with get_session_context() as session:
        query = (
            select(Exhibition)
            .where(Exhibition.id == exhibition_id)
            .options(selectinload(Exhibition.artworks_shown))
        )
        result = await session.execute(query)
        exhibition = result.scalar_one_or_none()

        if not exhibition:
            raise HTTPException(status_code=404, detail="Exhibition not found")

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(exhibition, field, value)

        exhibition.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(exhibition)

        return ExhibitionResponse(
            id=exhibition.id,
            year=exhibition.year,
            venue_name=exhibition.venue_name,
            venue_city=exhibition.venue_city,
            venue_state=exhibition.venue_state,
            venue_country=exhibition.venue_country or "USA",
            start_date=exhibition.start_date,
            end_date=exhibition.end_date,
            is_solo=exhibition.is_solo,
            exhibition_type=exhibition.exhibition_type,
            title=exhibition.title,
            description=exhibition.description,
            curator=exhibition.curator,
            notes=exhibition.notes,
            source_url=exhibition.source_url,
            catalog_url=exhibition.catalog_url,
            artwork_count=len(exhibition.artworks_shown) if exhibition.artworks_shown else 0,
        )


@router.delete("/{exhibition_id}")
async def delete_exhibition(exhibition_id: int):
    """Delete an exhibition."""
    async with get_session_context() as session:
        query = select(Exhibition).where(Exhibition.id == exhibition_id)
        result = await session.execute(query)
        exhibition = result.scalar_one_or_none()

        if not exhibition:
            raise HTTPException(status_code=404, detail="Exhibition not found")

        await session.delete(exhibition)
        await session.commit()

        return {"message": "Exhibition deleted successfully"}


# =============================================================================
# Artwork-Exhibition Linking Endpoints
# =============================================================================

@router.post("/{exhibition_id}/artworks")
async def link_artworks_to_exhibition(exhibition_id: int, data: ArtworkExhibitionLink):
    """Link one or more artworks to an exhibition."""
    async with get_session_context() as session:
        # Verify exhibition exists
        ex_query = select(Exhibition).where(Exhibition.id == exhibition_id)
        ex_result = await session.execute(ex_query)
        exhibition = ex_result.scalar_one_or_none()

        if not exhibition:
            raise HTTPException(status_code=404, detail="Exhibition not found")

        # Verify all artworks exist
        art_query = select(Artwork).where(Artwork.id.in_(data.artwork_ids))
        art_result = await session.execute(art_query)
        artworks = art_result.scalars().all()

        if len(artworks) != len(data.artwork_ids):
            raise HTTPException(status_code=404, detail="One or more artworks not found")

        # Check for existing links
        existing_query = select(ArtworkExhibition).where(
            ArtworkExhibition.exhibition_id == exhibition_id,
            ArtworkExhibition.artwork_id.in_(data.artwork_ids)
        )
        existing_result = await session.execute(existing_query)
        existing_links = {ae.artwork_id for ae in existing_result.scalars().all()}

        # Create new links
        created = []
        for artwork_id in data.artwork_ids:
            if artwork_id not in existing_links:
                link = ArtworkExhibition(
                    artwork_id=artwork_id,
                    exhibition_id=exhibition_id,
                    catalog_number=data.catalog_number,
                    was_sold=data.was_sold,
                    sale_price=data.sale_price,
                    notes=data.notes,
                )
                session.add(link)
                created.append(artwork_id)

        await session.commit()

        return {
            "message": f"Linked {len(created)} artwork(s) to exhibition",
            "linked_artwork_ids": created,
            "already_linked": list(existing_links),
        }


@router.delete("/{exhibition_id}/artworks/{artwork_id}")
async def unlink_artwork_from_exhibition(exhibition_id: int, artwork_id: int):
    """Remove an artwork from an exhibition."""
    async with get_session_context() as session:
        query = select(ArtworkExhibition).where(
            ArtworkExhibition.exhibition_id == exhibition_id,
            ArtworkExhibition.artwork_id == artwork_id
        )
        result = await session.execute(query)
        link = result.scalar_one_or_none()

        if not link:
            raise HTTPException(status_code=404, detail="Artwork-exhibition link not found")

        await session.delete(link)
        await session.commit()

        return {"message": "Artwork unlinked from exhibition successfully"}


@router.get("/{exhibition_id}/artworks")
async def get_exhibition_artworks(exhibition_id: int):
    """Get all artworks linked to an exhibition."""
    async with get_session_context() as session:
        query = (
            select(ArtworkExhibition)
            .where(ArtworkExhibition.exhibition_id == exhibition_id)
            .options(selectinload(ArtworkExhibition.artwork))
        )
        result = await session.execute(query)
        links = result.scalars().all()

        artworks = []
        for link in links:
            artwork = link.artwork
            artworks.append({
                "id": artwork.id,
                "title": artwork.title,
                "medium": artwork.medium,
                "dimensions": artwork.dimensions,
                "year_created": artwork.year_created,
                "primary_image_url": None,  # Would need to fetch from images
                "catalog_number": link.catalog_number,
                "was_sold": link.was_sold,
                "sale_price": link.sale_price,
                "notes": link.notes,
            })

        return {"exhibition_id": exhibition_id, "artworks": artworks, "count": len(artworks)}
