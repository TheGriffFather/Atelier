"""eBay scraper for finding Dan Brown artwork listings."""

import asyncio
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode, quote_plus

import httpx
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, ScrapedListing
from src.database import SourcePlatform


class EbayScraper(BaseScraper):
    """
    Scraper for eBay art listings.

    Uses eBay's search with category filtering to find potential Dan Brown artwork.
    """

    platform = SourcePlatform.EBAY
    BASE_URL = "https://www.ebay.com"

    # eBay category IDs
    CATEGORIES = {
        "art": 550,  # Art
        "paintings": 551,  # Paintings
        "prints": 360,  # Art Prints
    }

    def __init__(self, request_delay: float = 2.0):
        super().__init__()
        self.request_delay = request_delay
        self.client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
                follow_redirects=True,
                timeout=30.0,
            )
        return self.client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    def build_search_queries(self) -> list[str]:
        """Build eBay-optimized search queries."""
        return [
            # Primary searches - most likely to find the artist
            '"Dan Brown" trompe l\'oeil',
            '"Dan Brown" artist painting',
            '"Dan Brown" Connecticut artist',
            '"Dan Brown" "Susan Powell"',
            '"Daniel Brown" trompe l\'oeil',
            # Secondary searches - broader net
            '"Dan Brown" original painting -novel -book -author',
            '"Dan Brown" vintage postcards painting',
            '"Dan Brown" rack painting',
            '"Dan Brown" realist painting',
        ]

    def _build_search_url(self, query: str, category_id: int = 550) -> str:
        """Build eBay search URL with parameters."""
        params = {
            "_nkw": query,
            "_sacat": category_id,
            "_sop": 10,  # Sort by newly listed
            "LH_TitleDesc": 1,  # Search in title and description
            "_ipg": 60,  # Results per page
        }
        return f"{self.BASE_URL}/sch/i.html?{urlencode(params)}"

    async def search(self, query: str) -> list[ScrapedListing]:
        """
        Search eBay for listings matching the query.

        Args:
            query: Search query string

        Returns:
            List of scraped listings
        """
        client = await self._get_client()
        listings = []

        url = self._build_search_url(query)
        self.logger.info("Searching eBay", query=query, url=url)

        try:
            response = await client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            items = soup.select(".s-item")

            for item in items:
                try:
                    listing = self._parse_search_result(item)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    self.logger.warning("Failed to parse listing", error=str(e))
                    continue

            self.logger.info(
                "Search complete",
                query=query,
                results=len(listings),
            )

        except httpx.HTTPError as e:
            self.logger.error("HTTP error during search", error=str(e))
        except Exception as e:
            self.logger.error("Error during search", error=str(e))

        return listings

    def _parse_search_result(self, item) -> Optional[ScrapedListing]:
        """Parse a single search result item."""
        # Skip "Shop on eBay" placeholder items
        title_elem = item.select_one(".s-item__title")
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        if title.lower() == "shop on ebay":
            return None

        # Get URL
        link_elem = item.select_one(".s-item__link")
        if not link_elem:
            return None
        url = link_elem.get("href", "")

        # Extract item ID from URL
        item_id_match = re.search(r"/itm/(\d+)", url)
        item_id = item_id_match.group(1) if item_id_match else None

        # Clean URL (remove tracking params)
        if "?" in url:
            url = url.split("?")[0]

        # Get price
        price = None
        price_elem = item.select_one(".s-item__price")
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price_match = re.search(r"[\$£€]?([\d,]+\.?\d*)", price_text)
            if price_match:
                try:
                    price = float(price_match.group(1).replace(",", ""))
                except ValueError:
                    pass

        # Get location
        location = None
        location_elem = item.select_one(".s-item__location")
        if location_elem:
            location = location_elem.get_text(strip=True)
            # Clean up "From " prefix
            if location.lower().startswith("from "):
                location = location[5:]

        # Get image URL
        image_urls = []
        img_elem = item.select_one(".s-item__image-img")
        if img_elem:
            img_url = img_elem.get("src") or img_elem.get("data-src")
            if img_url and "s-l" in img_url:
                # Try to get larger image
                img_url = re.sub(r"s-l\d+", "s-l500", img_url)
            if img_url:
                image_urls.append(img_url)

        # Get subtitle/condition if available
        description = ""
        subtitle_elem = item.select_one(".s-item__subtitle")
        if subtitle_elem:
            description = subtitle_elem.get_text(strip=True)

        return ScrapedListing(
            title=title,
            description=description,
            source_platform=SourcePlatform.EBAY,
            source_url=url,
            source_id=item_id,
            price=price,
            currency="USD",
            location=location,
            image_urls=image_urls,
        )

    async def get_listing_details(self, url: str) -> Optional[ScrapedListing]:
        """
        Get full details for a specific eBay listing.

        Args:
            url: URL of the listing

        Returns:
            Detailed listing information
        """
        client = await self._get_client()

        self.logger.info("Fetching listing details", url=url)

        try:
            response = await client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            return self._parse_listing_page(soup, url)

        except httpx.HTTPError as e:
            self.logger.error("HTTP error fetching listing", url=url, error=str(e))
        except Exception as e:
            self.logger.error("Error fetching listing", url=url, error=str(e))

        return None

    def _parse_listing_page(self, soup: BeautifulSoup, url: str) -> Optional[ScrapedListing]:
        """Parse a full listing page."""
        # Title
        title_elem = soup.select_one("h1.x-item-title__mainTitle")
        if not title_elem:
            title_elem = soup.select_one('[data-testid="x-item-title"]')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown"

        # Extract item ID
        item_id_match = re.search(r"/itm/(\d+)", url)
        item_id = item_id_match.group(1) if item_id_match else None

        # Price
        price = None
        price_elem = soup.select_one('[data-testid="x-price-primary"]')
        if not price_elem:
            price_elem = soup.select_one(".x-price-primary")
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price_match = re.search(r"[\$£€]?([\d,]+\.?\d*)", price_text)
            if price_match:
                try:
                    price = float(price_match.group(1).replace(",", ""))
                except ValueError:
                    pass

        # Description
        description = ""
        desc_elem = soup.select_one('[data-testid="item-description"]')
        if not desc_elem:
            desc_elem = soup.select_one("#viTabs_0_is")
        if desc_elem:
            # Get text, limit length
            description = desc_elem.get_text(separator=" ", strip=True)[:2000]

        # Location
        location = None
        location_elem = soup.select_one('[data-testid="ux-labels-values__labels-content"]:-soup-contains("Item location")')
        if location_elem:
            value_elem = location_elem.find_next_sibling()
            if value_elem:
                location = value_elem.get_text(strip=True)

        # Alternative location finder
        if not location:
            for elem in soup.select(".ux-labels-values__labels"):
                if "location" in elem.get_text().lower():
                    value_elem = elem.find_next_sibling(class_="ux-labels-values__values")
                    if value_elem:
                        location = value_elem.get_text(strip=True)
                        break

        # Seller info
        seller_name = None
        seller_elem = soup.select_one('[data-testid="str-title"]')
        if not seller_elem:
            seller_elem = soup.select_one(".x-sellercard-atf__info__about-seller a")
        if seller_elem:
            seller_name = seller_elem.get_text(strip=True)

        # Images
        image_urls = []
        for img in soup.select('[data-testid="ux-image-carousel"] img'):
            src = img.get("src") or img.get("data-src")
            if src and "s-l" in src:
                # Get largest version
                src = re.sub(r"s-l\d+", "s-l1600", src)
                if src not in image_urls:
                    image_urls.append(src)

        # Alternative image finder
        if not image_urls:
            for img in soup.select(".ux-image-carousel-item img"):
                src = img.get("src") or img.get("data-zoom-src")
                if src and src not in image_urls:
                    image_urls.append(src)

        # End date (for auctions)
        date_ending = None
        end_elem = soup.select_one('[data-testid="timer"]')
        if end_elem:
            # Would need more parsing for actual date
            pass

        return ScrapedListing(
            title=title,
            description=description,
            source_platform=SourcePlatform.EBAY,
            source_url=url,
            source_id=item_id,
            price=price,
            currency="USD",
            seller_name=seller_name,
            location=location,
            image_urls=image_urls,
            date_ending=date_ending,
        )

    async def search_all(self) -> list[ScrapedListing]:
        """
        Run all search queries and combine results.

        Deduplicates by URL.
        """
        all_listings: dict[str, ScrapedListing] = {}

        for query in self.build_search_queries():
            listings = await self.search(query)

            for listing in listings:
                # Deduplicate by URL
                if listing.source_url not in all_listings:
                    all_listings[listing.source_url] = listing

            # Rate limiting between queries
            await asyncio.sleep(self.request_delay)

        self.logger.info(
            "All searches complete",
            total_unique=len(all_listings),
        )

        return list(all_listings.values())
