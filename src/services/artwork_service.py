"""Service layer for artwork database operations."""

from datetime import datetime
from typing import Optional

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import Artwork, ArtworkImage, Notification, AcquisitionStatus
from src.filters.confidence import FilterResult
from src.scrapers.base import ScrapedListing
from src.notifications.email import EmailNotifier

logger = structlog.get_logger()


class ArtworkService:
    """
    Handles all artwork-related database operations.

    Provides methods for:
    - Saving new artwork finds
    - Checking for duplicates
    - Updating artwork status
    - Retrieving artworks with various filters
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logger.bind(component="artwork_service")
        self.notifier = EmailNotifier()

    async def save_from_filter_result(
        self,
        result: FilterResult,
        send_notification: bool = True,
    ) -> Optional[Artwork]:
        """
        Save a filtered scrape result to the database.

        Checks for duplicates by source URL before saving.

        Args:
            result: The FilterResult containing the listing and scores.
            send_notification: Whether to send email notification.

        Returns:
            The created Artwork, or None if it was a duplicate.
        """
        listing = result.listing

        # Check for existing
        existing = await self.get_by_url(listing.source_url)
        if existing:
            self.logger.debug(
                "Duplicate listing, skipping",
                url=listing.source_url,
            )
            return None

        # Create artwork record
        artwork = Artwork(
            title=listing.title,
            description=listing.description,
            source_platform=listing.source_platform.value,
            source_url=listing.source_url,
            source_id=listing.source_id,
            price=listing.price,
            currency=listing.currency,
            seller_name=listing.seller_name,
            seller_id=listing.seller_id,
            location=listing.location,
            date_found=datetime.utcnow(),
            date_listing=listing.date_listing,
            date_ending=listing.date_ending,
            confidence_score=result.confidence_score,
            positive_signals=result.positive_signals,
            negative_signals=result.negative_signals,
            is_verified=False,
            is_false_positive=False,
            acquisition_status=AcquisitionStatus.NEW.value,
        )

        self.session.add(artwork)
        await self.session.flush()  # Get the ID

        # Save images
        for i, img_url in enumerate(listing.image_urls):
            image = ArtworkImage(
                artwork_id=artwork.id,
                url=img_url,
                is_primary=(i == 0),
            )
            self.session.add(image)

        await self.session.commit()

        self.logger.info(
            "Saved new artwork",
            id=artwork.id,
            title=artwork.title[:50],
            confidence=artwork.confidence_score,
        )

        # Send notification
        if send_notification:
            try:
                success = await self.notifier.send_new_artwork_notification(artwork)
                if success:
                    notification = Notification(
                        artwork_id=artwork.id,
                        channel="email",
                        recipient="configured",
                        status="sent",
                    )
                    self.session.add(notification)
                    await self.session.commit()
            except Exception as e:
                self.logger.error("Failed to send notification", error=str(e))

        return artwork

    async def save_batch(
        self,
        results: list[FilterResult],
        send_notifications: bool = True,
    ) -> list[Artwork]:
        """
        Save multiple filter results, skipping duplicates.

        Args:
            results: List of FilterResults to save.
            send_notifications: Whether to send notifications for new finds.

        Returns:
            List of newly created Artwork records.
        """
        saved = []

        for result in results:
            artwork = await self.save_from_filter_result(
                result,
                send_notification=send_notifications,
            )
            if artwork:
                saved.append(artwork)

        self.logger.info(
            "Batch save complete",
            attempted=len(results),
            saved=len(saved),
        )

        return saved

    async def get_by_url(self, url: str) -> Optional[Artwork]:
        """Get artwork by source URL."""
        result = await self.session.execute(
            select(Artwork).where(Artwork.source_url == url)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, artwork_id: int) -> Optional[Artwork]:
        """Get artwork by ID."""
        result = await self.session.execute(
            select(Artwork).where(Artwork.id == artwork_id)
        )
        return result.scalar_one_or_none()

    async def list_artworks(
        self,
        status: Optional[AcquisitionStatus] = None,
        verified_only: bool = False,
        include_false_positives: bool = False,
        min_confidence: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Artwork]:
        """
        List artworks with optional filtering.

        Args:
            status: Filter by acquisition status.
            verified_only: Only return verified artworks.
            include_false_positives: Include false positive marked items.
            min_confidence: Minimum confidence score.
            limit: Maximum results to return.
            offset: Number of results to skip.

        Returns:
            List of matching Artwork records.
        """
        query = select(Artwork)

        if status:
            query = query.where(Artwork.acquisition_status == status.value)

        if verified_only:
            query = query.where(Artwork.is_verified == True)

        if not include_false_positives:
            query = query.where(Artwork.is_false_positive == False)

        if min_confidence is not None:
            query = query.where(Artwork.confidence_score >= min_confidence)

        query = query.order_by(Artwork.date_found.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_new_finds(self, limit: int = 20) -> list[Artwork]:
        """Get recent new finds that haven't been reviewed."""
        return await self.list_artworks(
            status=AcquisitionStatus.NEW,
            limit=limit,
        )

    async def mark_verified(self, artwork_id: int) -> Optional[Artwork]:
        """Mark an artwork as verified (confirmed Dan Brown)."""
        artwork = await self.get_by_id(artwork_id)
        if artwork:
            artwork.is_verified = True
            await self.session.commit()
            self.logger.info("Marked verified", id=artwork_id)
        return artwork

    async def mark_false_positive(self, artwork_id: int) -> Optional[Artwork]:
        """Mark an artwork as false positive (not Dan Brown)."""
        artwork = await self.get_by_id(artwork_id)
        if artwork:
            artwork.is_false_positive = True
            await self.session.commit()
            self.logger.info("Marked false positive", id=artwork_id)
        return artwork

    async def update_status(
        self,
        artwork_id: int,
        status: AcquisitionStatus,
        notes: Optional[str] = None,
    ) -> Optional[Artwork]:
        """Update artwork acquisition status."""
        artwork = await self.get_by_id(artwork_id)
        if artwork:
            artwork.acquisition_status = status.value
            if notes:
                artwork.notes = notes
            await self.session.commit()
            self.logger.info(
                "Updated status",
                id=artwork_id,
                status=status.value,
            )
        return artwork

    async def get_stats(self) -> dict:
        """Get summary statistics."""
        total = await self.session.execute(
            select(func.count(Artwork.id))
        )
        verified = await self.session.execute(
            select(func.count(Artwork.id)).where(Artwork.is_verified == True)
        )
        new = await self.session.execute(
            select(func.count(Artwork.id)).where(
                Artwork.acquisition_status == AcquisitionStatus.NEW.value
            )
        )
        acquired = await self.session.execute(
            select(func.count(Artwork.id)).where(
                Artwork.acquisition_status == AcquisitionStatus.ACQUIRED.value
            )
        )
        # Count artworks with at least one image
        with_images = await self.session.execute(
            select(func.count(func.distinct(ArtworkImage.artwork_id)))
        )

        return {
            "total": total.scalar() or 0,
            "verified": verified.scalar() or 0,
            "new": new.scalar() or 0,
            "acquired": acquired.scalar() or 0,
            "with_images": with_images.scalar() or 0,
        }
