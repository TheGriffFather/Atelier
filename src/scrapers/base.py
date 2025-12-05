"""Base scraper class and shared types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import structlog

from src.database import SourcePlatform

logger = structlog.get_logger()


@dataclass
class ScrapedListing:
    """
    Represents a raw listing scraped from a platform.

    This is the intermediate format before filtering and database storage.
    """
    title: str
    description: str
    source_platform: SourcePlatform
    source_url: str
    source_id: Optional[str] = None

    price: Optional[float] = None
    currency: str = "USD"

    seller_name: Optional[str] = None
    seller_id: Optional[str] = None
    location: Optional[str] = None

    image_urls: list[str] = field(default_factory=list)

    date_listing: Optional[datetime] = None
    date_ending: Optional[datetime] = None

    raw_data: Optional[dict] = None  # Store original response for debugging


class BaseScraper(ABC):
    """
    Abstract base class for all platform scrapers.

    Each scraper should implement the search method to return listings
    that potentially match Dan Brown artwork.
    """

    platform: SourcePlatform

    def __init__(self) -> None:
        self.logger = logger.bind(scraper=self.__class__.__name__)

    @abstractmethod
    async def search(self, query: str) -> list[ScrapedListing]:
        """
        Search the platform for listings matching the query.

        Args:
            query: Search query string

        Returns:
            List of scraped listings that may contain Dan Brown artwork
        """
        pass

    @abstractmethod
    async def get_listing_details(self, url: str) -> Optional[ScrapedListing]:
        """
        Get full details for a specific listing.

        Args:
            url: URL of the listing

        Returns:
            Detailed listing information, or None if not found
        """
        pass

    async def close(self) -> None:
        """Clean up any resources (browser, connections, etc.)."""
        pass

    def build_search_queries(self) -> list[str]:
        """
        Build the list of search queries to use for this platform.

        Returns queries designed to find Dan Brown art while minimizing
        false positives from the author Dan Brown.
        """
        return [
            '"Dan Brown" trompe l\'oeil',
            '"Dan Brown" artist Connecticut',
            '"Dan Brown" "Susan Powell"',
            '"Daniel Brown" trompe l\'oeil',
            '"Dan Brown" painter vintage postcards',
            '"Dan Brown" rack painting',
        ]
