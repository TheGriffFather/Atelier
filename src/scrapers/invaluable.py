"""
Invaluable.com auction scraper.

Scrapes auction listings and results from Invaluable using Playwright
for JavaScript-rendered content.

Note: Invaluable has no public API for data access.
This scraper respects rate limits and is for personal use only.
"""

import asyncio
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, quote_plus

from src.scrapers.base import BaseScraper, ScrapedListing
from src.database import SourcePlatform

# Playwright is optional - handle import gracefully
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class InvaluableScraper(BaseScraper):
    """
    Scraper for Invaluable.com auction platform.

    Uses Playwright for JavaScript rendering as Invaluable
    heavily relies on client-side rendering.

    Search URL pattern:
    https://www.invaluable.com/search?query=dan+brown+artist
    """

    platform = SourcePlatform.INVALUABLE
    BASE_URL = "https://www.invaluable.com"

    def __init__(self, request_delay: float = 3.0, headless: bool = True):
        super().__init__()
        self.request_delay = request_delay
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def _ensure_browser(self) -> Browser:
        """Ensure Playwright browser is running."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright not installed. Install with: pip install playwright && playwright install chromium"
            )

        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
        return self.browser

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    def build_search_queries(self) -> list[str]:
        """Build search queries for Invaluable."""
        return [
            "dan brown trompe l'oeil",
            "dan brown artist painting",
            "dan brown connecticut artist",
            "dan brown oil painting currency",
        ]

    async def search(self, query: str) -> list[ScrapedListing]:
        """
        Search Invaluable for artwork listings.

        Args:
            query: Search query string

        Returns:
            List of scraped listings
        """
        listings = []

        try:
            browser = await self._ensure_browser()
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()

            # Build search URL
            search_url = f"{self.BASE_URL}/search?query={quote_plus(query)}"
            self.logger.info(f"Searching Invaluable", url=search_url, query=query)

            await page.goto(search_url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)  # Wait for dynamic content

            # Check for CAPTCHA or blocking
            content = await page.content()
            if "captcha" in content.lower() or "blocked" in content.lower():
                self.logger.warning("Invaluable may be blocking requests (CAPTCHA detected)")
                await context.close()
                return []

            # Try multiple selectors for search results
            selectors = [
                ".search-result-item",
                ".lot-card",
                "[data-testid='lot-card']",
                ".auction-lot",
                "article.lot",
            ]

            results = []
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        results = elements
                        self.logger.info(f"Found results with selector: {selector}", count=len(elements))
                        break
                except Exception:
                    continue

            if not results:
                # Try to find any links that look like lot pages
                links = await page.query_selector_all("a[href*='/auction-lot/']")
                self.logger.info(f"Found lot links", count=len(links))

                for link in links[:20]:  # Limit results
                    try:
                        href = await link.get_attribute("href")
                        text = await link.inner_text()

                        if href and text:
                            listing = ScrapedListing(
                                title=text.strip()[:200],
                                description="",
                                source_platform=SourcePlatform.INVALUABLE,
                                source_url=urljoin(self.BASE_URL, href),
                                source_id=self._extract_lot_id(href),
                            )
                            listings.append(listing)
                    except Exception as e:
                        self.logger.debug(f"Failed to parse link", error=str(e))
                        continue

            else:
                # Parse structured results
                for element in results[:20]:  # Limit results
                    listing = await self._parse_search_result(page, element)
                    if listing:
                        listings.append(listing)

            await context.close()

        except Exception as e:
            self.logger.error(f"Search failed", error=str(e), query=query)

        await asyncio.sleep(self.request_delay)
        return listings

    async def _parse_search_result(self, page: Page, element) -> Optional[ScrapedListing]:
        """Parse a search result element into a ScrapedListing."""
        try:
            # Extract title
            title = ""
            for selector in ["h2", "h3", ".title", ".lot-title", "[data-testid='title']"]:
                try:
                    title_elem = await element.query_selector(selector)
                    if title_elem:
                        title = await title_elem.inner_text()
                        break
                except Exception:
                    continue

            if not title:
                title = await element.inner_text()
                title = title.split("\n")[0][:200]

            # Extract URL
            url = ""
            link = await element.query_selector("a[href*='/auction-lot/']")
            if link:
                url = await link.get_attribute("href")
                if url and not url.startswith("http"):
                    url = urljoin(self.BASE_URL, url)

            if not url:
                return None

            # Extract price
            price = None
            for selector in [".price", ".estimate", "[data-testid='price']"]:
                try:
                    price_elem = await element.query_selector(selector)
                    if price_elem:
                        price_text = await price_elem.inner_text()
                        price_match = re.search(r'\$?([\d,]+)', price_text)
                        if price_match:
                            price = float(price_match.group(1).replace(",", ""))
                            break
                except Exception:
                    continue

            # Extract image
            images = []
            img = await element.query_selector("img")
            if img:
                src = await img.get_attribute("src") or await img.get_attribute("data-src")
                if src:
                    if not src.startswith("http"):
                        src = urljoin(self.BASE_URL, src)
                    images.append(src)

            # Extract description
            description = ""
            for selector in [".description", ".lot-description", "p"]:
                try:
                    desc_elem = await element.query_selector(selector)
                    if desc_elem:
                        description = await desc_elem.inner_text()
                        break
                except Exception:
                    continue

            # Extract auction house/seller
            seller = ""
            for selector in [".auction-house", ".seller", ".house-name"]:
                try:
                    seller_elem = await element.query_selector(selector)
                    if seller_elem:
                        seller = await seller_elem.inner_text()
                        break
                except Exception:
                    continue

            return ScrapedListing(
                title=title.strip(),
                description=description.strip()[:500],
                source_platform=SourcePlatform.INVALUABLE,
                source_url=url,
                source_id=self._extract_lot_id(url),
                price=price,
                currency="USD",
                seller_name=seller.strip() if seller else None,
                image_urls=images,
            )

        except Exception as e:
            self.logger.warning(f"Failed to parse search result", error=str(e))
            return None

    def _extract_lot_id(self, url: str) -> Optional[str]:
        """Extract lot ID from Invaluable URL."""
        # URLs like: /auction-lot/dan-brown-american-b-1949-six-fives-323-c-abc123
        match = re.search(r'/auction-lot/[^/]+-([a-z0-9]+)/?$', url, re.I)
        if match:
            return match.group(1)
        # Try to get last segment
        parts = url.rstrip("/").split("/")
        return parts[-1] if parts else None

    async def get_listing_details(self, url: str) -> Optional[ScrapedListing]:
        """Get detailed information for a specific lot."""
        try:
            browser = await self._ensure_browser()
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            page = await context.new_page()

            self.logger.info(f"Fetching lot details", url=url)
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)

            # Extract title
            title = ""
            for selector in ["h1", ".lot-title", "[data-testid='lot-title']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        title = await elem.inner_text()
                        break
                except Exception:
                    continue

            # Extract description
            description = ""
            for selector in [".lot-description", ".description", "[data-testid='description']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        description = await elem.inner_text()
                        break
                except Exception:
                    continue

            # Extract price/estimate
            price = None
            for selector in [".price", ".estimate", ".sold-price", "[data-testid='price']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        price_text = await elem.inner_text()
                        price_match = re.search(r'\$?([\d,]+)', price_text)
                        if price_match:
                            price = float(price_match.group(1).replace(",", ""))
                            break
                except Exception:
                    continue

            # Extract images
            images = []
            img_elements = await page.query_selector_all(".lot-image img, .gallery img, [data-testid='lot-image'] img")
            for img in img_elements[:5]:
                try:
                    src = await img.get_attribute("src") or await img.get_attribute("data-src")
                    if src and src not in images:
                        if not src.startswith("http"):
                            src = urljoin(self.BASE_URL, src)
                        images.append(src)
                except Exception:
                    continue

            # Extract auction house
            seller = ""
            for selector in [".auction-house", ".house-name", "[data-testid='auction-house']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        seller = await elem.inner_text()
                        break
                except Exception:
                    continue

            # Extract dimensions from description
            dimensions = None
            dim_match = re.search(r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(in|cm|inches)', description)
            if dim_match:
                dimensions = f"{dim_match.group(1)} x {dim_match.group(2)} {dim_match.group(3)}"

            await context.close()

            return ScrapedListing(
                title=title.strip(),
                description=description.strip(),
                source_platform=SourcePlatform.INVALUABLE,
                source_url=url,
                source_id=self._extract_lot_id(url),
                price=price,
                currency="USD",
                seller_name=seller.strip() if seller else None,
                image_urls=images,
                raw_data={"dimensions": dimensions} if dimensions else None,
            )

        except Exception as e:
            self.logger.error(f"Failed to get listing details", error=str(e), url=url)
            return None


class InvaluableHttpScraper(BaseScraper):
    """
    Fallback HTTP-based scraper for Invaluable when Playwright isn't available.

    Less reliable than the Playwright version but doesn't require browser.
    """

    platform = SourcePlatform.INVALUABLE
    BASE_URL = "https://www.invaluable.com"

    def __init__(self, request_delay: float = 2.0):
        super().__init__()
        self.request_delay = request_delay
        self.client = None

    async def _get_client(self):
        """Get or create HTTP client."""
        if self.client is None:
            import httpx
            self.client = httpx.AsyncClient(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                timeout=30.0,
                follow_redirects=True,
            )
        return self.client

    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    def build_search_queries(self) -> list[str]:
        """Build search queries."""
        return [
            "dan brown trompe l'oeil",
            "dan brown artist painting",
        ]

    async def search(self, query: str) -> list[ScrapedListing]:
        """Search using HTTP requests (limited functionality)."""
        # Invaluable heavily relies on JavaScript, so HTTP-only scraping
        # has very limited effectiveness
        self.logger.warning(
            "HTTP-only Invaluable scraping has limited functionality. "
            "Install Playwright for better results: pip install playwright && playwright install chromium"
        )
        return []

    async def get_listing_details(self, url: str) -> Optional[ScrapedListing]:
        """Get listing details via HTTP."""
        return None
