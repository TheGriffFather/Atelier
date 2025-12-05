"""
Artnet auction records scraper.

Scrapes artwork and auction data from artnet.com for Dan Brown (artist).
Uses httpx for HTTP requests and BeautifulSoup for parsing.

Note: Artnet has no public API, so this uses web scraping.
Be respectful of rate limits and robots.txt.
"""

import asyncio
import re
from datetime import datetime
from typing import Optional
from urllib.parse import quote, urljoin

import httpx
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, ScrapedListing
from src.database import SourcePlatform


class ArtnetScraper(BaseScraper):
    """
    Scraper for Artnet auction records and price database.

    Artnet URLs follow patterns like:
    - Artist page: https://www.artnet.com/artists/dan-brown/
    - Auction results: https://www.artnet.com/artists/dan-brown/auction-results
    """

    platform = SourcePlatform.ARTNET
    BASE_URL = "https://www.artnet.com"

    # Artist slug for Dan Brown (the painter, not the author)
    # There may be multiple "Dan Brown" artists - we need to filter carefully
    ARTIST_SLUGS = [
        "dan-brown-2",  # Often painters get numbered slugs
        "dan-brown",
    ]

    def __init__(self, request_delay: float = 2.0):
        super().__init__()
        self.request_delay = request_delay
        self.client: Optional[httpx.AsyncClient] = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                headers=self.headers,
                timeout=30.0,
                follow_redirects=True,
            )
        return self.client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    def build_search_queries(self) -> list[str]:
        """Build search queries - for Artnet we search by artist page."""
        # Artnet doesn't have a traditional search - we scrape artist pages
        return self.ARTIST_SLUGS

    async def search(self, query: str) -> list[ScrapedListing]:
        """
        Search Artnet for Dan Brown artwork.

        For Artnet, 'query' is actually the artist slug.
        """
        listings = []
        client = await self._get_client()

        # Try auction results page first
        auction_url = f"{self.BASE_URL}/artists/{query}/auction-results"

        try:
            self.logger.info(f"Fetching Artnet auction results", url=auction_url)
            response = await client.get(auction_url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Check if this is the right Dan Brown (painter, not author)
                artist_info = soup.find("div", class_="artist-header")
                if artist_info:
                    info_text = artist_info.get_text().lower()
                    # Skip if this looks like the author
                    if "novelist" in info_text or "da vinci" in info_text or "author" in info_text:
                        self.logger.info(f"Skipping - appears to be author Dan Brown", slug=query)
                        return []

                # Find auction result items
                results = soup.find_all("div", class_="auction-result") or \
                         soup.find_all("div", class_="lot-item") or \
                         soup.find_all("article", class_="artwork")

                for result in results:
                    listing = self._parse_auction_result(result, query)
                    if listing:
                        listings.append(listing)

                self.logger.info(f"Found {len(listings)} auction results", artist=query)

            elif response.status_code == 404:
                self.logger.warning(f"Artist not found on Artnet", slug=query)
            else:
                self.logger.warning(f"Artnet returned status {response.status_code}", slug=query)

        except httpx.RequestError as e:
            self.logger.error(f"Request failed", error=str(e), url=auction_url)

        await asyncio.sleep(self.request_delay)

        # Also try the main artist page for current works
        artist_url = f"{self.BASE_URL}/artists/{query}/"

        try:
            response = await client.get(artist_url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Find artwork listings
                artworks = soup.find_all("div", class_="artwork-item") or \
                          soup.find_all("a", class_="details-link")

                for artwork in artworks[:20]:  # Limit to first 20
                    listing = self._parse_artwork_item(artwork, query)
                    if listing and listing.source_url not in [l.source_url for l in listings]:
                        listings.append(listing)

        except httpx.RequestError as e:
            self.logger.error(f"Request failed", error=str(e), url=artist_url)

        return listings

    def _parse_auction_result(self, element, artist_slug: str) -> Optional[ScrapedListing]:
        """Parse an auction result element into a ScrapedListing."""
        try:
            # Extract title
            title_elem = element.find("h2") or element.find("a", class_="title") or \
                        element.find("span", class_="title")
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)

            # Extract URL
            link = element.find("a", href=True)
            if link:
                url = urljoin(self.BASE_URL, link["href"])
            else:
                url = f"{self.BASE_URL}/artists/{artist_slug}/auction-results"

            # Extract price
            price = None
            price_elem = element.find("span", class_="price") or \
                        element.find("div", class_="price") or \
                        element.find(string=re.compile(r'\$[\d,]+'))
            if price_elem:
                price_text = price_elem.get_text() if hasattr(price_elem, 'get_text') else str(price_elem)
                price_match = re.search(r'\$([\d,]+)', price_text)
                if price_match:
                    price = float(price_match.group(1).replace(",", ""))

            # Extract description/details
            desc_elem = element.find("p") or element.find("div", class_="details")
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            # Extract image
            images = []
            img = element.find("img")
            if img and img.get("src"):
                img_url = img["src"]
                if not img_url.startswith("http"):
                    img_url = urljoin(self.BASE_URL, img_url)
                images.append(img_url)

            # Extract date
            date_elem = element.find("span", class_="date") or \
                       element.find(string=re.compile(r'\d{1,2}/\d{1,2}/\d{2,4}'))
            listing_date = None
            if date_elem:
                date_text = date_elem.get_text() if hasattr(date_elem, 'get_text') else str(date_elem)
                # Try to parse date
                for fmt in ["%m/%d/%Y", "%m/%d/%y", "%B %d, %Y"]:
                    try:
                        listing_date = datetime.strptime(date_text.strip(), fmt)
                        break
                    except ValueError:
                        continue

            # Generate source ID from URL
            source_id = url.split("/")[-1] if url else None

            return ScrapedListing(
                title=title,
                description=description,
                source_platform=SourcePlatform.ARTNET,
                source_url=url,
                source_id=source_id,
                price=price,
                currency="USD",
                image_urls=images,
                date_listing=listing_date,
                raw_data={"artist_slug": artist_slug},
            )

        except Exception as e:
            self.logger.warning(f"Failed to parse auction result", error=str(e))
            return None

    def _parse_artwork_item(self, element, artist_slug: str) -> Optional[ScrapedListing]:
        """Parse an artwork item element into a ScrapedListing."""
        try:
            # Get link and title
            if element.name == "a":
                link = element
                title = element.get_text(strip=True)
            else:
                link = element.find("a", href=True)
                title_elem = element.find("h3") or element.find("span", class_="title")
                title = title_elem.get_text(strip=True) if title_elem else "Unknown"

            if not link or not link.get("href"):
                return None

            url = urljoin(self.BASE_URL, link["href"])

            # Skip if not an artwork page
            if "/artists/" not in url and "/artwork/" not in url:
                return None

            # Extract image
            images = []
            img = element.find("img")
            if img and img.get("src"):
                img_url = img["src"]
                if not img_url.startswith("http"):
                    img_url = urljoin(self.BASE_URL, img_url)
                images.append(img_url)

            return ScrapedListing(
                title=title,
                description="",
                source_platform=SourcePlatform.ARTNET,
                source_url=url,
                source_id=url.split("/")[-1],
                image_urls=images,
                raw_data={"artist_slug": artist_slug},
            )

        except Exception as e:
            self.logger.warning(f"Failed to parse artwork item", error=str(e))
            return None

    async def get_listing_details(self, url: str) -> Optional[ScrapedListing]:
        """Get detailed information for a specific artwork."""
        client = await self._get_client()

        try:
            response = await client.get(url)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title
            title_elem = soup.find("h1") or soup.find("meta", property="og:title")
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"

            # Extract description
            desc_elem = soup.find("div", class_="description") or \
                       soup.find("meta", property="og:description")
            description = ""
            if desc_elem:
                if hasattr(desc_elem, 'get_text'):
                    description = desc_elem.get_text(strip=True)
                else:
                    description = desc_elem.get("content", "")

            # Extract price
            price = None
            price_elem = soup.find("span", class_="price") or \
                        soup.find("div", class_="price")
            if price_elem:
                price_match = re.search(r'\$([\d,]+)', price_elem.get_text())
                if price_match:
                    price = float(price_match.group(1).replace(",", ""))

            # Extract images
            images = []
            for img in soup.find_all("img", class_=re.compile(r"artwork|gallery|main")):
                src = img.get("src") or img.get("data-src")
                if src:
                    if not src.startswith("http"):
                        src = urljoin(self.BASE_URL, src)
                    images.append(src)

            # Also check og:image
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                images.insert(0, og_image["content"])

            return ScrapedListing(
                title=title,
                description=description,
                source_platform=SourcePlatform.ARTNET,
                source_url=url,
                source_id=url.split("/")[-1],
                price=price,
                currency="USD",
                image_urls=images[:5],  # Limit images
            )

        except Exception as e:
            self.logger.error(f"Failed to get listing details", error=str(e), url=url)
            return None
