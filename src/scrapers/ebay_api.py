"""eBay Browse API scraper for finding Dan Brown artwork listings.

Uses the official eBay Browse API instead of web scraping.
Requires eBay Developer credentials (free tier: 5,000 calls/day).

Get credentials at: https://developer.ebay.com/my/keys
"""

import asyncio
import base64
from datetime import datetime, timedelta
from typing import Optional

import httpx
import structlog

from src.scrapers.base import BaseScraper, ScrapedListing
from src.database import SourcePlatform

logger = structlog.get_logger()


class EbayApiScraper(BaseScraper):
    """
    Scraper using eBay's official Browse API.

    Much more reliable than web scraping - no blocking, structured data,
    and access to more listing details.

    Free tier provides 5,000 API calls per day.
    """

    platform = SourcePlatform.EBAY

    # API endpoints (production)
    PROD_AUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    PROD_BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    # API endpoints (sandbox)
    SANDBOX_AUTH_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
    SANDBOX_BROWSE_URL = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"

    # eBay category IDs for art
    CATEGORIES = {
        "art": "550",
        "paintings": "551",
        "prints": "360",
    }

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        request_delay: float = 0.5,
        environment: str = "production",
    ):
        """
        Initialize the eBay API scraper.

        Args:
            client_id: eBay Developer App ID (Client ID)
            client_secret: eBay Developer Cert ID (Client Secret)
            request_delay: Delay between API calls in seconds
            environment: "production" or "sandbox"
        """
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.request_delay = request_delay
        self.environment = environment.lower()

        # Set API URLs based on environment
        if self.environment == "sandbox":
            self.auth_url = self.SANDBOX_AUTH_URL
            self.browse_url = self.SANDBOX_BROWSE_URL
        else:
            self.auth_url = self.PROD_AUTH_URL
            self.browse_url = self.PROD_BROWSE_URL

        self.client: Optional[httpx.AsyncClient] = None
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def _get_access_token(self) -> str:
        """
        Get OAuth access token using client credentials flow.

        Caches token until expiry.
        """
        # Return cached token if still valid
        if self._access_token and self._token_expires:
            if datetime.utcnow() < self._token_expires - timedelta(minutes=5):
                return self._access_token

        client = await self._get_client()

        # Encode credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}",
        }

        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        }

        self.logger.debug(f"Requesting eBay OAuth token from {self.environment} environment")

        response = await client.post(self.auth_url, headers=headers, data=data)
        response.raise_for_status()

        token_data = response.json()
        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 7200)
        self._token_expires = datetime.utcnow() + timedelta(seconds=expires_in)

        self.logger.info("eBay OAuth token obtained", expires_in=expires_in)
        return self._access_token

    def build_search_queries(self) -> list[str]:
        """Build search queries optimized for the eBay API."""
        return [
            # Specific artist searches
            "Dan Brown trompe l'oeil",
            "Dan Brown artist painting",
            "Dan Brown Connecticut artist",
            "Dan Brown Susan Powell",
            "Daniel Brown trompe l'oeil",
            # Style-specific searches
            "Dan Brown rack painting",
            "Dan Brown vintage postcards painting",
            "Dan Brown realist painting",
            # Broader searches with exclusions (handled in post-filter)
            "Dan Brown original oil painting",
        ]

    async def search(self, query: str) -> list[ScrapedListing]:
        """
        Search eBay using the Browse API.

        Args:
            query: Search query string

        Returns:
            List of scraped listings
        """
        client = await self._get_client()
        token = await self._get_access_token()

        listings = []

        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            "Content-Type": "application/json",
        }

        params = {
            "q": query,
            "category_ids": self.CATEGORIES["art"],
            "limit": 50,
            "sort": "newlyListed",
            # Filter to items with images
            "fieldgroups": "MATCHING_ITEMS,EXTENDED",
        }

        self.logger.info("Searching eBay API", query=query)

        try:
            response = await client.get(
                self.browse_url,
                headers=headers,
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            items = data.get("itemSummaries", [])

            for item in items:
                try:
                    listing = self._parse_item(item)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    self.logger.warning("Failed to parse item", error=str(e))
                    continue

            self.logger.info(
                "API search complete",
                query=query,
                results=len(listings),
                total_available=data.get("total", 0),
            )

        except httpx.HTTPStatusError as e:
            self.logger.error(
                "eBay API error",
                status=e.response.status_code,
                error=str(e),
            )
        except Exception as e:
            self.logger.error("Error during API search", error=str(e))

        return listings

    def _parse_item(self, item: dict) -> Optional[ScrapedListing]:
        """Parse an item from the API response."""
        title = item.get("title", "")
        if not title:
            return None

        # Get item ID and URL
        item_id = item.get("itemId", "")
        item_url = item.get("itemWebUrl", "")
        if not item_url:
            item_url = f"https://www.ebay.com/itm/{item_id}"

        # Parse price
        price = None
        price_data = item.get("price", {})
        if price_data:
            try:
                price = float(price_data.get("value", 0))
            except (ValueError, TypeError):
                pass

        currency = price_data.get("currency", "USD")

        # Get location
        location = None
        item_location = item.get("itemLocation", {})
        if item_location:
            city = item_location.get("city", "")
            state = item_location.get("stateOrProvince", "")
            country = item_location.get("country", "")
            location_parts = [p for p in [city, state, country] if p]
            location = ", ".join(location_parts) if location_parts else None

        # Get seller info
        seller_name = None
        seller_id = None
        seller = item.get("seller", {})
        if seller:
            seller_name = seller.get("username")
            seller_id = seller.get("username")

        # Get images
        image_urls = []
        image = item.get("image", {})
        if image:
            img_url = image.get("imageUrl", "")
            if img_url:
                image_urls.append(img_url)

        # Get additional images if available
        additional_images = item.get("additionalImages", [])
        for img in additional_images[:5]:  # Limit to 5 additional
            img_url = img.get("imageUrl", "")
            if img_url and img_url not in image_urls:
                image_urls.append(img_url)

        # Parse dates
        date_listing = None
        listing_date_str = item.get("itemCreationDate")
        if listing_date_str:
            try:
                # eBay returns ISO format
                date_listing = datetime.fromisoformat(
                    listing_date_str.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        date_ending = None
        end_date_str = item.get("itemEndDate")
        if end_date_str:
            try:
                date_ending = datetime.fromisoformat(
                    end_date_str.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        # Get short description if available
        description = item.get("shortDescription", "")

        # Get condition
        condition = item.get("condition", "")
        if condition and description:
            description = f"{condition}. {description}"
        elif condition:
            description = condition

        return ScrapedListing(
            title=title,
            description=description,
            source_platform=SourcePlatform.EBAY,
            source_url=item_url,
            source_id=item_id,
            price=price,
            currency=currency,
            seller_name=seller_name,
            seller_id=seller_id,
            location=location,
            image_urls=image_urls,
            date_listing=date_listing,
            date_ending=date_ending,
            raw_data=item,
        )

    async def get_listing_details(self, url: str) -> Optional[ScrapedListing]:
        """
        Get detailed info for a specific listing.

        The Browse API's getItem method provides more details than search.
        """
        # Extract item ID from URL
        item_id = None
        if "/itm/" in url:
            parts = url.split("/itm/")
            if len(parts) > 1:
                item_id = parts[1].split("?")[0].split("/")[0]

        if not item_id:
            self.logger.warning("Could not extract item ID from URL", url=url)
            return None

        client = await self._get_client()
        token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        }

        detail_url = f"https://api.ebay.com/buy/browse/v1/item/{item_id}"

        try:
            response = await client.get(detail_url, headers=headers)
            response.raise_for_status()

            item = response.json()

            # Use existing parser but with more detail
            listing = self._parse_item(item)

            # Add full description if available
            if listing and item.get("description"):
                listing.description = item["description"][:2000]

            return listing

        except httpx.HTTPStatusError as e:
            self.logger.error(
                "Error fetching item details",
                item_id=item_id,
                status=e.response.status_code,
            )
        except Exception as e:
            self.logger.error("Error fetching item details", error=str(e))

        return None

    async def search_all(self) -> list[ScrapedListing]:
        """
        Run all search queries and combine results.

        Deduplicates by item ID.
        """
        all_listings: dict[str, ScrapedListing] = {}

        for query in self.build_search_queries():
            listings = await self.search(query)

            for listing in listings:
                # Deduplicate by source_id (eBay item ID)
                if listing.source_id and listing.source_id not in all_listings:
                    all_listings[listing.source_id] = listing
                elif listing.source_url not in [l.source_url for l in all_listings.values()]:
                    all_listings[listing.source_url] = listing

            # Rate limiting
            await asyncio.sleep(self.request_delay)

        self.logger.info(
            "All API searches complete",
            total_unique=len(all_listings),
        )

        return list(all_listings.values())
