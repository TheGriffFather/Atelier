"""Scraper control and stats endpoints."""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from src.database import get_session_context
from src.scrapers.orchestrator import ScraperOrchestrator
from src.services.artwork_service import ArtworkService

router = APIRouter()


class ScrapeResult(BaseModel):
    """Result of a scrape run."""
    total_found: int
    passed_filter: int
    new_artworks: int
    duplicates: int


class Stats(BaseModel):
    """Overall statistics."""
    total: int
    verified: int
    new: int
    acquired: int
    with_images: int = 0


@router.get("/stats", response_model=Stats)
async def get_stats() -> Stats:
    """Get overall statistics."""
    async with get_session_context() as session:
        service = ArtworkService(session)
        stats = await service.get_stats()
        return Stats(**stats)


@router.post("/scrape", response_model=ScrapeResult)
async def run_scraper() -> ScrapeResult:
    """
    Run the scrapers and save new finds.

    This runs synchronously - for long-running scrapes, consider
    using the background task version.
    """
    orchestrator = ScraperOrchestrator()

    try:
        results = await orchestrator.run_all()

        async with get_session_context() as session:
            service = ArtworkService(session)
            saved = await service.save_batch(results, send_notifications=True)

            return ScrapeResult(
                total_found=len(results) + len([r for r in results if r.is_rejected]),
                passed_filter=len(results),
                new_artworks=len(saved),
                duplicates=len(results) - len(saved),
            )
    finally:
        await orchestrator.close()


async def _run_scraper_background():
    """Background task for running the scraper."""
    orchestrator = ScraperOrchestrator()
    try:
        results = await orchestrator.run_all()
        async with get_session_context() as session:
            service = ArtworkService(session)
            await service.save_batch(results, send_notifications=True)
    finally:
        await orchestrator.close()


@router.post("/scrape/background")
async def run_scraper_background(background_tasks: BackgroundTasks) -> dict:
    """
    Start a scraper run in the background.

    Returns immediately while scraping continues.
    """
    background_tasks.add_task(_run_scraper_background)
    return {"status": "started", "message": "Scraper running in background"}
