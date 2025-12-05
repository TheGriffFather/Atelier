"""Orchestrates multiple scrapers and processes results."""

import asyncio
from datetime import datetime
from typing import Optional

import structlog

from config.settings import settings
from src.scrapers.base import BaseScraper, ScrapedListing
from src.scrapers.ebay import EbayScraper
from src.scrapers.ebay_api import EbayApiScraper
from src.scrapers.artnet import ArtnetScraper
from src.filters.confidence import ConfidenceScorer, FilterResult
from src.database import SourcePlatform

# Optional scrapers that require Playwright
try:
    from src.scrapers.invaluable import InvaluableScraper, PLAYWRIGHT_AVAILABLE as INVALUABLE_PLAYWRIGHT
except ImportError:
    InvaluableScraper = None
    INVALUABLE_PLAYWRIGHT = False

try:
    from src.scrapers.liveauctioneers import LiveAuctioneersScraper, PLAYWRIGHT_AVAILABLE as LA_PLAYWRIGHT
except ImportError:
    LiveAuctioneersScraper = None
    LA_PLAYWRIGHT = False

logger = structlog.get_logger()


class ScraperOrchestrator:
    """
    Coordinates running multiple scrapers and processing their results.

    Handles:
    - Running scrapers in sequence (to respect rate limits)
    - Deduplicating results across scrapers
    - Applying confidence filtering
    - Preparing results for database storage
    """

    def __init__(
        self,
        scrapers: Optional[list[BaseScraper]] = None,
        confidence_threshold: float = 0.5,
        include_playwright: bool = False,
    ):
        """
        Initialize the orchestrator.

        Args:
            scrapers: List of scrapers to use. If None, uses defaults.
            confidence_threshold: Minimum confidence score to keep a result.
            include_playwright: Include Playwright-based scrapers (Invaluable,
                               LiveAuctioneers). Requires Playwright to be installed.
        """
        self.logger = logger.bind(component="orchestrator")
        self.scrapers = scrapers or self._default_scrapers(include_playwright=include_playwright)
        self.scorer = ConfidenceScorer(acceptance_threshold=confidence_threshold)

    def _default_scrapers(self, include_playwright: bool = False) -> list[BaseScraper]:
        """
        Create default set of scrapers.

        Args:
            include_playwright: If True, include scrapers that require Playwright
                               (Invaluable, LiveAuctioneers). Default False for
                               faster runs with just API/HTTP scrapers.

        Uses eBay API if credentials are configured, otherwise falls back
        to web scraping (which may be blocked).
        """
        scrapers: list[BaseScraper] = []

        # eBay - Prefer API if credentials are available
        if settings.ebay_client_id and settings.ebay_client_secret:
            self.logger.info("Using eBay Browse API (credentials configured)")
            scrapers.append(
                EbayApiScraper(
                    client_id=settings.ebay_client_id,
                    client_secret=settings.ebay_client_secret,
                    request_delay=0.5,  # API allows faster requests
                )
            )
        else:
            self.logger.warning(
                "eBay API credentials not configured, using web scraper (may be blocked)"
            )
            scrapers.append(EbayScraper(request_delay=2.0))

        # Artnet - Always include (HTTP-based)
        self.logger.info("Adding Artnet scraper")
        scrapers.append(ArtnetScraper(request_delay=2.0))

        # Playwright-based scrapers (optional)
        if include_playwright:
            # Invaluable
            if InvaluableScraper and INVALUABLE_PLAYWRIGHT:
                self.logger.info("Adding Invaluable scraper (Playwright)")
                scrapers.append(InvaluableScraper(request_delay=3.0))
            else:
                self.logger.warning(
                    "Invaluable scraper not available (requires Playwright: "
                    "pip install playwright && playwright install chromium)"
                )

            # LiveAuctioneers
            if LiveAuctioneersScraper and LA_PLAYWRIGHT:
                self.logger.info("Adding LiveAuctioneers scraper (Playwright)")
                scrapers.append(LiveAuctioneersScraper(request_delay=2.5))
            else:
                self.logger.warning(
                    "LiveAuctioneers scraper not available (requires Playwright)"
                )

        return scrapers

    async def run_all(self) -> list[FilterResult]:
        """
        Run all scrapers and return filtered results.

        Returns:
            List of FilterResult objects, sorted by confidence score.
        """
        self.logger.info("Starting scrape run", scraper_count=len(self.scrapers))
        start_time = datetime.utcnow()

        all_listings: dict[str, ScrapedListing] = {}

        for scraper in self.scrapers:
            try:
                self.logger.info(
                    "Running scraper",
                    platform=scraper.platform.value,
                )

                listings = await scraper.search_all()

                # Deduplicate by URL
                new_count = 0
                for listing in listings:
                    if listing.source_url not in all_listings:
                        all_listings[listing.source_url] = listing
                        new_count += 1

                self.logger.info(
                    "Scraper complete",
                    platform=scraper.platform.value,
                    found=len(listings),
                    new=new_count,
                )

            except Exception as e:
                self.logger.error(
                    "Scraper failed",
                    platform=scraper.platform.value,
                    error=str(e),
                )
            finally:
                await scraper.close()

        # Apply confidence scoring
        self.logger.info("Filtering results", total=len(all_listings))
        results = self.scorer.filter_listings(list(all_listings.values()))

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        self.logger.info(
            "Scrape run complete",
            total_found=len(all_listings),
            passed_filter=len(results),
            elapsed_seconds=elapsed,
        )

        return results

    async def run_scraper(self, platform: SourcePlatform) -> list[FilterResult]:
        """
        Run a single scraper by platform.

        Args:
            platform: The platform to scrape.

        Returns:
            Filtered results from that platform.
        """
        scraper = None
        for s in self.scrapers:
            if s.platform == platform:
                scraper = s
                break

        if not scraper:
            self.logger.error("Scraper not found", platform=platform.value)
            return []

        try:
            listings = await scraper.search_all()
            return self.scorer.filter_listings(listings)
        finally:
            await scraper.close()

    async def get_listing_details(
        self,
        url: str,
        platform: SourcePlatform,
    ) -> Optional[FilterResult]:
        """
        Get detailed info for a specific listing and score it.

        Args:
            url: The listing URL.
            platform: The platform the listing is from.

        Returns:
            FilterResult with full details, or None if not found.
        """
        scraper = None
        for s in self.scrapers:
            if s.platform == platform:
                scraper = s
                break

        if not scraper:
            return None

        try:
            listing = await scraper.get_listing_details(url)
            if listing:
                return self.scorer.score(listing)
        finally:
            await scraper.close()

        return None

    async def close(self) -> None:
        """Close all scrapers."""
        for scraper in self.scrapers:
            await scraper.close()
