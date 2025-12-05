"""API routes for saved searches and alerts."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload

from src.database import get_session_context, SavedSearch, AlertResult, AlertStatus, SourcePlatform
from src.scrapers.ebay_api import EbayApiScraper
from src.filters.confidence import ConfidenceScorer
from config.settings import settings

router = APIRouter()


# =============================================================================
# Pydantic Models
# =============================================================================

class SavedSearchCreate(BaseModel):
    name: str
    query: str
    platform: str = "ebay"
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    run_interval_hours: int = 24
    notes: Optional[str] = None


class SavedSearchUpdate(BaseModel):
    name: Optional[str] = None
    query: Optional[str] = None
    platform: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    is_active: Optional[bool] = None
    run_interval_hours: Optional[int] = None
    notes: Optional[str] = None


class AlertResultUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class RunSearchResponse(BaseModel):
    search_id: int
    search_name: str
    new_results: int
    total_results: int
    message: str


# =============================================================================
# Saved Search Endpoints
# =============================================================================

@router.get("/searches")
async def list_searches():
    """List all saved searches with result counts."""
    async with get_session_context() as session:
        # Get searches with result counts
        result = await session.execute(
            select(SavedSearch).order_by(SavedSearch.created_at.desc())
        )
        searches = result.scalars().all()

        search_list = []
        for search in searches:
            # Count total results
            total_result = await session.execute(
                select(func.count(AlertResult.id)).where(AlertResult.search_id == search.id)
            )
            total_count = total_result.scalar() or 0

            # Count new results
            new_result = await session.execute(
                select(func.count(AlertResult.id))
                .where(AlertResult.search_id == search.id)
                .where(AlertResult.status == 'new')
            )
            new_count = new_result.scalar() or 0

            search_list.append({
                "id": search.id,
                "name": search.name,
                "query": search.query,
                "platform": search.platform,
                "category": search.category,
                "min_price": search.min_price,
                "max_price": search.max_price,
                "is_active": search.is_active,
                "run_interval_hours": search.run_interval_hours,
                "last_run": search.last_run.isoformat() if search.last_run else None,
                "next_run": search.next_run.isoformat() if search.next_run else None,
                "total_results": total_count,
                "new_results": new_count,
                "notes": search.notes,
                "created_at": search.created_at.isoformat(),
            })

        return {"searches": search_list, "total": len(search_list)}


@router.get("/searches/{search_id}")
async def get_search(search_id: int):
    """Get a specific saved search with its results."""
    async with get_session_context() as session:
        result = await session.execute(
            select(SavedSearch).where(SavedSearch.id == search_id)
        )
        search = result.scalar_one_or_none()

        if not search:
            raise HTTPException(status_code=404, detail="Search not found")

        # Get results
        results_query = await session.execute(
            select(AlertResult)
            .where(AlertResult.search_id == search_id)
            .order_by(AlertResult.date_found.desc())
            .limit(100)
        )
        results = results_query.scalars().all()

        return {
            "search": {
                "id": search.id,
                "name": search.name,
                "query": search.query,
                "platform": search.platform,
                "category": search.category,
                "min_price": search.min_price,
                "max_price": search.max_price,
                "is_active": search.is_active,
                "run_interval_hours": search.run_interval_hours,
                "last_run": search.last_run.isoformat() if search.last_run else None,
                "notes": search.notes,
            },
            "results": [
                {
                    "id": r.id,
                    "title": r.title,
                    "description": r.description,
                    "source_url": r.source_url,
                    "source_id": r.source_id,
                    "price": r.price,
                    "currency": r.currency,
                    "seller_name": r.seller_name,
                    "location": r.location,
                    "image_url": r.image_url,
                    "date_found": r.date_found.isoformat() if r.date_found else None,
                    "date_listing": r.date_listing.isoformat() if r.date_listing else None,
                    "date_ending": r.date_ending.isoformat() if r.date_ending else None,
                    "status": r.status,
                    "confidence_score": r.confidence_score,
                    "notes": r.notes,
                }
                for r in results
            ],
            "total_results": len(results)
        }


@router.post("/searches")
async def create_search(data: SavedSearchCreate):
    """Create a new saved search."""
    async with get_session_context() as session:
        search = SavedSearch(
            name=data.name,
            query=data.query,
            platform=data.platform,
            category=data.category,
            min_price=data.min_price,
            max_price=data.max_price,
            run_interval_hours=data.run_interval_hours,
            notes=data.notes,
            is_active=True,
            next_run=datetime.utcnow(),  # Ready to run immediately
        )
        session.add(search)
        await session.commit()
        await session.refresh(search)

        return {
            "id": search.id,
            "name": search.name,
            "message": "Search created successfully"
        }


@router.patch("/searches/{search_id}")
async def update_search(search_id: int, data: SavedSearchUpdate):
    """Update a saved search."""
    async with get_session_context() as session:
        result = await session.execute(
            select(SavedSearch).where(SavedSearch.id == search_id)
        )
        search = result.scalar_one_or_none()

        if not search:
            raise HTTPException(status_code=404, detail="Search not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(search, key, value)

        search.updated_at = datetime.utcnow()
        await session.commit()

        return {"message": "Search updated successfully"}


@router.delete("/searches/{search_id}")
async def delete_search(search_id: int):
    """Delete a saved search and all its results."""
    async with get_session_context() as session:
        result = await session.execute(
            select(SavedSearch).where(SavedSearch.id == search_id)
        )
        search = result.scalar_one_or_none()

        if not search:
            raise HTTPException(status_code=404, detail="Search not found")

        await session.delete(search)
        await session.commit()

        return {"message": "Search deleted successfully"}


# =============================================================================
# Run Search Endpoints
# =============================================================================

@router.post("/searches/{search_id}/run", response_model=RunSearchResponse)
async def run_search(search_id: int):
    """Run a specific saved search and save new results."""
    async with get_session_context() as session:
        # Get the search
        result = await session.execute(
            select(SavedSearch).where(SavedSearch.id == search_id)
        )
        search = result.scalar_one_or_none()

        if not search:
            raise HTTPException(status_code=404, detail="Search not found")

        # Currently only eBay is supported
        if search.platform != "ebay":
            raise HTTPException(status_code=400, detail=f"Platform {search.platform} not yet supported")

        # Initialize scraper
        scraper = EbayApiScraper(
            client_id=settings.ebay_client_id,
            client_secret=settings.ebay_client_secret,
        )

        confidence_scorer = ConfidenceScorer()
        new_count = 0

        try:
            # Run the search
            listings = await scraper.search(search.query)

            # Get existing source_ids to avoid duplicates
            existing_result = await session.execute(
                select(AlertResult.source_id)
                .where(AlertResult.search_id == search_id)
                .where(AlertResult.source_id.isnot(None))
            )
            existing_ids = set(r[0] for r in existing_result.fetchall())

            for listing in listings:
                # Skip if we already have this listing
                if listing.source_id and listing.source_id in existing_ids:
                    continue

                # Calculate confidence score - pass the listing object directly
                filter_result = confidence_scorer.score(listing)
                score = filter_result.confidence_score

                # Create alert result
                alert_result = AlertResult(
                    search_id=search_id,
                    title=listing.title,
                    description=listing.description,
                    source_url=listing.source_url,
                    source_id=listing.source_id,
                    price=listing.price,
                    currency=listing.currency or "USD",
                    seller_name=listing.seller_name,
                    location=listing.location,
                    image_url=listing.image_urls[0] if listing.image_urls else None,
                    date_listing=listing.date_listing,
                    date_ending=listing.date_ending,
                    status=AlertStatus.NEW.value,
                    confidence_score=score,
                )
                session.add(alert_result)
                new_count += 1

            # Update search stats
            search.last_run = datetime.utcnow()
            search.next_run = datetime.utcnow() + timedelta(hours=search.run_interval_hours)
            search.total_results = (search.total_results or 0) + new_count
            search.new_since_last_view = (search.new_since_last_view or 0) + new_count

            await session.commit()

            # Get total count
            count_result = await session.execute(
                select(func.count(AlertResult.id)).where(AlertResult.search_id == search_id)
            )
            total = count_result.scalar() or 0

            return RunSearchResponse(
                search_id=search_id,
                search_name=search.name,
                new_results=new_count,
                total_results=total,
                message=f"Found {new_count} new listings"
            )

        finally:
            await scraper.close()


@router.post("/searches/run-all")
async def run_all_searches(background_tasks: BackgroundTasks):
    """Run all active searches in the background."""
    background_tasks.add_task(_run_all_searches_background)
    return {"status": "started", "message": "Running all active searches in background"}


async def _run_all_searches_background():
    """Background task to run all active searches."""
    async with get_session_context() as session:
        result = await session.execute(
            select(SavedSearch).where(SavedSearch.is_active == True)
        )
        searches = result.scalars().all()

        for search in searches:
            try:
                # Run each search (simplified - could be optimized)
                await run_search(search.id)
            except Exception as e:
                print(f"Error running search {search.id}: {e}")


# =============================================================================
# Alert Results Endpoints
# =============================================================================

@router.get("/results")
async def list_all_results(
    status: Optional[str] = None,
    search_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List alert results with optional filtering."""
    async with get_session_context() as session:
        query = select(AlertResult).order_by(AlertResult.date_found.desc())

        if status:
            query = query.where(AlertResult.status == status)
        if search_id:
            query = query.where(AlertResult.search_id == search_id)

        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        results = result.scalars().all()

        # Get total count
        count_query = select(func.count(AlertResult.id))
        if status:
            count_query = count_query.where(AlertResult.status == status)
        if search_id:
            count_query = count_query.where(AlertResult.search_id == search_id)

        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        return {
            "results": [
                {
                    "id": r.id,
                    "search_id": r.search_id,
                    "title": r.title,
                    "description": r.description,
                    "source_url": r.source_url,
                    "source_id": r.source_id,
                    "price": r.price,
                    "currency": r.currency,
                    "seller_name": r.seller_name,
                    "location": r.location,
                    "image_url": r.image_url,
                    "date_found": r.date_found.isoformat() if r.date_found else None,
                    "date_listing": r.date_listing.isoformat() if r.date_listing else None,
                    "date_ending": r.date_ending.isoformat() if r.date_ending else None,
                    "status": r.status,
                    "confidence_score": r.confidence_score,
                    "notes": r.notes,
                }
                for r in results
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.patch("/results/{result_id}")
async def update_result(result_id: int, data: AlertResultUpdate):
    """Update an alert result (e.g., change status, add notes)."""
    async with get_session_context() as session:
        result = await session.execute(
            select(AlertResult).where(AlertResult.id == result_id)
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise HTTPException(status_code=404, detail="Result not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(alert, key, value)

        alert.updated_at = datetime.utcnow()
        await session.commit()

        return {"message": "Result updated successfully"}


@router.post("/results/{result_id}/promote")
async def promote_to_artwork(result_id: int):
    """Promote an alert result to the main artwork catalog."""
    from src.database import Artwork, ArtworkImage

    async with get_session_context() as session:
        # Get the alert result
        result = await session.execute(
            select(AlertResult).where(AlertResult.id == result_id)
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise HTTPException(status_code=404, detail="Result not found")

        if alert.promoted_to_artwork_id:
            raise HTTPException(status_code=400, detail="Already promoted to artwork")

        # Create new artwork
        artwork = Artwork(
            title=alert.title,
            description=alert.description,
            source_platform="ebay",
            source_url=alert.source_url,
            source_id=alert.source_id,
            price=alert.price,
            currency=alert.currency,
            seller_name=alert.seller_name,
            location=alert.location,
            date_found=alert.date_found,
            date_listing=alert.date_listing,
            date_ending=alert.date_ending,
            confidence_score=alert.confidence_score or 0.0,
            acquisition_status="new",
            notes=alert.notes,
        )
        session.add(artwork)
        await session.flush()  # Get the artwork ID

        # Add image if present
        if alert.image_url:
            image = ArtworkImage(
                artwork_id=artwork.id,
                url=alert.image_url,
                is_primary=True,
            )
            session.add(image)

        # Update alert result
        alert.promoted_to_artwork_id = artwork.id
        alert.status = AlertStatus.CONFIRMED.value

        await session.commit()

        return {
            "message": "Promoted to artwork catalog",
            "artwork_id": artwork.id,
        }


@router.delete("/results/{result_id}")
async def delete_result(result_id: int):
    """Delete an alert result."""
    async with get_session_context() as session:
        result = await session.execute(
            select(AlertResult).where(AlertResult.id == result_id)
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise HTTPException(status_code=404, detail="Result not found")

        await session.delete(alert)
        await session.commit()

        return {"message": "Result deleted successfully"}


# =============================================================================
# Stats Endpoint
# =============================================================================

@router.get("/stats")
async def get_alert_stats():
    """Get overall alert statistics."""
    async with get_session_context() as session:
        # Count searches
        search_count = await session.execute(
            select(func.count(SavedSearch.id))
        )
        total_searches = search_count.scalar() or 0

        active_search_count = await session.execute(
            select(func.count(SavedSearch.id)).where(SavedSearch.is_active == True)
        )
        active_searches = active_search_count.scalar() or 0

        # Get last scan time (most recent last_run from any search)
        last_scan_result = await session.execute(
            select(func.max(SavedSearch.last_run))
        )
        last_scan = last_scan_result.scalar()

        # Count results by status
        status_counts = {}
        for status in AlertStatus:
            count_result = await session.execute(
                select(func.count(AlertResult.id)).where(AlertResult.status == status.value)
            )
            status_counts[status.value] = count_result.scalar() or 0

        total_results = sum(status_counts.values())

        return {
            "total_searches": total_searches,
            "active_searches": active_searches,
            "total_results": total_results,
            "new_results": status_counts.get("new", 0),
            "confirmed_results": status_counts.get("confirmed", 0),
            "rejected_results": status_counts.get("rejected", 0),
            "watching_results": status_counts.get("watching", 0),
            "status_breakdown": status_counts,
            "last_scan": last_scan.isoformat() if last_scan else None,
        }
