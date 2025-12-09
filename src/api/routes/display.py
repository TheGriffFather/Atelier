"""Endpoints for the physical display frame."""

from typing import Optional, List

from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select, func

from src.database import Artwork, ArtworkImage, get_session_context
from src.database.models import DisplaySettings

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


# =============================================================================
# Display Settings (shared across all clients)
# =============================================================================

class DisplaySettingsResponse(BaseModel):
    """Display settings response model."""
    frame_style: str = "wood"
    interval: int = 3600
    shuffle: bool = True
    show_title: bool = True
    show_progress: bool = False
    verified_only: bool = True
    image_fit: str = "auto"  # auto, contain, cover, fill
    selected_artwork_ids: Optional[List[int]] = None
    excluded_art_types: Optional[List[str]] = None


class DisplaySettingsUpdate(BaseModel):
    """Display settings update model."""
    frame_style: Optional[str] = None
    interval: Optional[int] = None
    shuffle: Optional[bool] = None
    show_title: Optional[bool] = None
    show_progress: Optional[bool] = None
    verified_only: Optional[bool] = None
    image_fit: Optional[str] = None
    selected_artwork_ids: Optional[List[int]] = None
    excluded_art_types: Optional[List[str]] = None


@router.get("/settings", response_model=DisplaySettingsResponse)
async def get_display_settings() -> DisplaySettingsResponse:
    """
    Get display settings.

    Returns the global settings used by all frame clients.
    Creates default settings if none exist.
    """
    async with get_session_context() as session:
        result = await session.execute(
            select(DisplaySettings).where(DisplaySettings.id == 1)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            # Create default settings
            settings = DisplaySettings(id=1)
            session.add(settings)
            await session.commit()
            await session.refresh(settings)

        return DisplaySettingsResponse(
            frame_style=settings.frame_style,
            interval=settings.interval,
            shuffle=settings.shuffle,
            show_title=settings.show_title,
            show_progress=settings.show_progress,
            verified_only=settings.verified_only,
            image_fit=getattr(settings, 'image_fit', 'auto'),
            selected_artwork_ids=settings.selected_artwork_ids,
            excluded_art_types=settings.excluded_art_types,
        )


@router.put("/settings", response_model=DisplaySettingsResponse)
async def update_display_settings(update: DisplaySettingsUpdate) -> DisplaySettingsResponse:
    """
    Update display settings.

    Updates the global settings used by all frame clients.
    """
    async with get_session_context() as session:
        result = await session.execute(
            select(DisplaySettings).where(DisplaySettings.id == 1)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            settings = DisplaySettings(id=1)
            session.add(settings)

        # Update only provided fields
        if update.frame_style is not None:
            settings.frame_style = update.frame_style
        if update.interval is not None:
            settings.interval = update.interval
        if update.shuffle is not None:
            settings.shuffle = update.shuffle
        if update.show_title is not None:
            settings.show_title = update.show_title
        if update.show_progress is not None:
            settings.show_progress = update.show_progress
        if update.verified_only is not None:
            settings.verified_only = update.verified_only
        if update.image_fit is not None:
            settings.image_fit = update.image_fit
        if update.selected_artwork_ids is not None:
            settings.selected_artwork_ids = update.selected_artwork_ids
        if update.excluded_art_types is not None:
            settings.excluded_art_types = update.excluded_art_types

        await session.commit()
        await session.refresh(settings)

        return DisplaySettingsResponse(
            frame_style=settings.frame_style,
            interval=settings.interval,
            shuffle=settings.shuffle,
            show_title=settings.show_title,
            show_progress=settings.show_progress,
            verified_only=settings.verified_only,
            image_fit=getattr(settings, 'image_fit', 'auto'),
            selected_artwork_ids=settings.selected_artwork_ids,
            excluded_art_types=settings.excluded_art_types,
        )
