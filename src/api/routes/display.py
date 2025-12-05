"""Endpoints for the physical display frame."""

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select, func

from src.database import Artwork, ArtworkImage, get_session_context

router = APIRouter()


class DisplayArtwork(BaseModel):
    """Simplified artwork data for the display frame."""
    id: int
    title: str
    image_url: str
    artist: str = "Dan Brown"


class DisplayStatus(BaseModel):
    """Status information for the display frame."""
    total_artworks: int
    new_since_last_sync: int
    current_artwork_id: Optional[int]


@router.get("/artworks", response_model=list[DisplayArtwork])
async def get_display_artworks(
    limit: int = Query(default=20, le=100),
    verified_only: bool = True,
) -> list[DisplayArtwork]:
    """
    Get artworks for the display frame rotation.

    Returns verified artworks with their primary images.
    """
    async with get_session_context() as session:
        query = (
            select(Artwork, ArtworkImage)
            .join(ArtworkImage, Artwork.id == ArtworkImage.artwork_id)
            .where(ArtworkImage.is_primary == True)
            .where(Artwork.is_false_positive == False)
        )

        if verified_only:
            query = query.where(Artwork.is_verified == True)

        query = query.order_by(func.random()).limit(limit)

        result = await session.execute(query)
        rows = result.all()

        return [
            DisplayArtwork(
                id=artwork.id,
                title=artwork.title,
                image_url=image.local_path or image.url,
            )
            for artwork, image in rows
        ]


@router.get("/image/{artwork_id}")
async def get_artwork_image(artwork_id: int) -> RedirectResponse:
    """
    Get the primary image for an artwork.

    Redirects to the image URL (can be extended to serve cached images).
    """
    async with get_session_context() as session:
        result = await session.execute(
            select(ArtworkImage)
            .where(ArtworkImage.artwork_id == artwork_id)
            .where(ArtworkImage.is_primary == True)
        )
        image = result.scalar_one_or_none()

        if not image:
            # Return a placeholder or default image
            return RedirectResponse(url="/static/placeholder.png")

        return RedirectResponse(url=image.local_path or image.url)


@router.get("/status", response_model=DisplayStatus)
async def get_display_status() -> DisplayStatus:
    """Get status information for the display frame."""
    async with get_session_context() as session:
        # Total verified artworks
        total_result = await session.execute(
            select(func.count(Artwork.id))
            .where(Artwork.is_verified == True)
            .where(Artwork.is_false_positive == False)
        )
        total = total_result.scalar() or 0

        # New finds (status = 'new')
        new_result = await session.execute(
            select(func.count(Artwork.id))
            .where(Artwork.acquisition_status == "new")
            .where(Artwork.is_false_positive == False)
        )
        new_count = new_result.scalar() or 0

        return DisplayStatus(
            total_artworks=total,
            new_since_last_sync=new_count,
            current_artwork_id=None,
        )
