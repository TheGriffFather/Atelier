"""Command-line interface for the art tracker."""

import asyncio
import argparse
import sys

import structlog

from config.settings import settings


def setup_logging() -> None:
    """Configure structured logging."""
    import logging

    # Map string level to logging constant
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    log_level = level_map.get(settings.log_level, logging.INFO)

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
    )


async def run_scraper() -> None:
    """Run the scraper once."""
    from src.database import init_db, get_session_context
    from src.scrapers.orchestrator import ScraperOrchestrator
    from src.services.artwork_service import ArtworkService

    logger = structlog.get_logger()
    logger.info("Initializing database...")
    await init_db()

    logger.info("Starting scraper run...")
    orchestrator = ScraperOrchestrator()

    try:
        results = await orchestrator.run_all()

        async with get_session_context() as session:
            service = ArtworkService(session)
            saved = await service.save_batch(results, send_notifications=True)

            logger.info(
                "Scrape complete",
                found=len(results),
                saved=len(saved),
                duplicates=len(results) - len(saved),
            )
    finally:
        await orchestrator.close()


async def run_server() -> None:
    """Run the API server."""
    import uvicorn
    from src.api.main import app

    config = uvicorn.Config(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    await server.serve()


def main() -> None:
    """Main entry point for the CLI."""
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Atelier - Digital Catalogue Raisonne",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Run scrapers once")
    scrape_parser.add_argument(
        "--platform",
        choices=["ebay", "all"],
        default="all",
        help="Platform to scrape",
    )

    # Server command
    subparsers.add_parser("server", help="Run the API server")

    # Scheduler command
    subparsers.add_parser("scheduler", help="Run the scheduler for periodic scraping")

    # Init command
    subparsers.add_parser("init", help="Initialize the database")

    args = parser.parse_args()

    if args.command == "scrape":
        asyncio.run(run_scraper())
    elif args.command == "server":
        asyncio.run(run_server())
    elif args.command == "scheduler":
        from src.scheduler import run_scheduler
        asyncio.run(run_scheduler())
    elif args.command == "init":
        from src.database import init_db
        asyncio.run(init_db(dispose_engine=True))
        print("Database initialized successfully")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
