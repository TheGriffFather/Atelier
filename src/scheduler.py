"""Scheduled task runner for periodic scraping."""

import asyncio
from datetime import datetime

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import settings
from src.database import get_session_context, init_db
from src.scrapers.orchestrator import ScraperOrchestrator
from src.services.artwork_service import ArtworkService

logger = structlog.get_logger()


async def run_scheduled_scrape():
    """
    Run a scheduled scrape job.

    This is called by the scheduler at configured intervals.
    """
    job_logger = logger.bind(job="scheduled_scrape", started_at=datetime.utcnow().isoformat())
    job_logger.info("Starting scheduled scrape")

    orchestrator = ScraperOrchestrator()

    try:
        results = await orchestrator.run_all()

        async with get_session_context() as session:
            service = ArtworkService(session)
            saved = await service.save_batch(results, send_notifications=True)

            job_logger.info(
                "Scheduled scrape complete",
                found=len(results),
                saved=len(saved),
            )

    except Exception as e:
        job_logger.error("Scheduled scrape failed", error=str(e))
    finally:
        await orchestrator.close()


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the scheduler."""
    scheduler = AsyncIOScheduler()

    # Add the main scraping job
    scheduler.add_job(
        run_scheduled_scrape,
        trigger=IntervalTrigger(minutes=settings.scrape_interval_minutes),
        id="main_scrape",
        name="Main artwork scrape",
        replace_existing=True,
        max_instances=1,  # Prevent overlapping runs
    )

    logger.info(
        "Scheduler configured",
        interval_minutes=settings.scrape_interval_minutes,
    )

    return scheduler


async def run_scheduler():
    """Run the scheduler as a standalone process."""
    import structlog

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
    )

    logger.info("Initializing database...")
    await init_db()

    scheduler = create_scheduler()
    scheduler.start()

    logger.info("Scheduler started, running initial scrape...")

    # Run once immediately on startup
    await run_scheduled_scrape()

    logger.info("Scheduler running, press Ctrl+C to stop")

    # Keep running
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(run_scheduler())
