"""
LiveAuctioneers.com auction scraper.

Provides two implementations:
1. Using the auction-scraper package (if installed)
2. Custom Playwright-based scraper (fallback)

LiveAuctioneers is one of the largest online auction platforms
for art, antiques, and collectibles.
"""

import asyncio
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, quote_plus

from src.scrapers.base import BaseScraper, ScrapedListing
from src.database import SourcePlatform

# Check for auction-scraper package
try:
    from auction_scraper import LiveauctioneersBackend
    AUCTION_SCRAPER_AVAILABLE = True
except ImportError:
    AUCTION_SCRAPER_AVAILABLE = False

# Check for Playwright
try:
    from playwright.async_api import async_playwright, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class LiveAuctioneersScraper(BaseScraper):
    """
    Scraper for LiveAuctioneers.com.

    Uses Playwright for reliable JavaScript rendering.
    LiveAuctioneers search URL pattern:
    https://www.liveauctioneers.com/search/?keyword=dan+brown+artist
    """

    platform = SourcePlatform.LIVEAUCTIONEERS
    BASE_URL = "https://www.liveauctioneers.com"

    def __init__(self, request_delay: float = 2.5, headless: bool = True):
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
        """Build search queries for LiveAuctioneers."""
        return [
            "dan brown trompe l'oeil",
            "dan brown artist oil painting",
            "dan brown connecticut painter",
            "dan brown currency painting",
            "dan brown still life rack",
        ]

    async def search(self, query: str) -> list[ScrapedListing]:
        """
        Search LiveAuctioneers for artwork listings.
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
            search_url = f"{self.BASE_URL}/search/?keyword={quote_plus(query)}"
            self.logger.info(f"Searching LiveAuctioneers", url=search_url, query=query)

            await page.goto(search_url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)

            # Check for blocking
            content = await page.content()
            if "captcha" in content.lower() or "access denied" in content.lower():
                self.logger.warning("LiveAuctioneers may be blocking requests")
                await context.close()
                return []

            # Find lot cards
            selectors = [
                "[data-testid='lot-card']",
                ".lot-card",
                ".search-result-item",
                "article.lot",
                ".item-card",
            ]

            results = []
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        results = elements
                        self.logger.info(f"Found results", selector=selector, count=len(elements))
                        break
                except Exception:
                    continue

            if not results:
                # Try finding lot links directly
                links = await page.query_selector_all("a[href*='/item/']")
                self.logger.info(f"Found item links", count=len(links))

                seen_urls = set()
                for link in links[:30]:
                    try:
                        href = await link.get_attribute("href")
                        if href and href not in seen_urls:
                            seen_urls.add(href)
                            text = await link.inner_text()

                            if text.strip():
                                full_url = urljoin(self.BASE_URL, href)
                                listing = ScrapedListing(
                                    title=text.strip()[:200],
                                    description="",
                                    source_platform=SourcePlatform.LIVEAUCTIONEERS,
                                    source_url=full_url,
                                    source_id=self._extract_item_id(href),
                                )
                                listings.append(listing)
                    except Exception as e:
                        self.logger.debug(f"Failed to parse link", error=str(e))
            else:
                for element in results[:20]:
                    listing = await self._parse_search_result(element)
                    if listing:
                        listings.append(listing)

            await context.close()

        except Exception as e:
            self.logger.error(f"Search failed", error=str(e), query=query)

        await asyncio.sleep(self.request_delay)
        return listings

    async def _parse_search_result(self, element) -> Optional[ScrapedListing]:
        """Parse a search result element."""
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
            link = await element.query_selector("a[href*='/item/']")
            if not link:
                link = await element.query_selector("a[href]")
            if link:
                url = await link.get_attribute("href")
                if url and not url.startswith("http"):
                    url = urljoin(self.BASE_URL, url)

            if not url:
                return None

            # Extract price/estimate
            price = None
            for selector in [".price", ".estimate", ".current-bid", "[data-testid='price']"]:
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
                    # Skip placeholder images
                    if "placeholder" not in src.lower() and "blank" not in src.lower():
                        images.append(src)

            # Extract auction house
            seller = ""
            for selector in [".house-name", ".auctioneer", ".seller"]:
                try:
                    seller_elem = await element.query_selector(selector)
                    if seller_elem:
                        seller = await seller_elem.inner_text()
                        break
                except Exception:
                    continue

            # Extract location
            location = ""
            for selector in [".location", ".auction-location"]:
                try:
                    loc_elem = await element.query_selector(selector)
                    if loc_elem:
                        location = await loc_elem.inner_text()
                        break
                except Exception:
                    continue

            return ScrapedListing(
                title=title.strip(),
                description="",
                source_platform=SourcePlatform.LIVEAUCTIONEERS,
                source_url=url,
                source_id=self._extract_item_id(url),
                price=price,
                currency="USD",
                seller_name=seller.strip() if seller else None,
                location=location.strip() if location else None,
                image_urls=images,
            )

        except Exception as e:
            self.logger.warning(f"Failed to parse result", error=str(e))
            return None

    def _extract_item_id(self, url: str) -> Optional[str]:
        """Extract item ID from LiveAuctioneers URL."""
        # URLs like: /item/12345_dan-brown-painting
        match = re.search(r'/item/(\d+)', url)
        if match:
            return match.group(1)
        return None

    async def get_listing_details(self, url: str) -> Optional[ScrapedListing]:
        """Get detailed information for a specific lot."""
        try:
            browser = await self._ensure_browser()
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
            page = await context.new_page()

            self.logger.info(f"Fetching lot details", url=url)
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)

            # Extract title
            title = ""
            title_elem = await page.query_selector("h1")
            if title_elem:
                title = await title_elem.inner_text()

            # Extract description
            description = ""
            for selector in [".lot-description", ".description", "#description"]:
                try:
                    desc_elem = await page.query_selector(selector)
                    if desc_elem:
                        description = await desc_elem.inner_text()
                        break
                except Exception:
                    continue

            # Extract price
            price = None
            for selector in [".sold-price", ".current-bid", ".estimate", ".price"]:
                try:
                    price_elem = await page.query_selector(selector)
                    if price_elem:
                        price_text = await price_elem.inner_text()
                        price_match = re.search(r'\$?([\d,]+)', price_text)
                        if price_match:
                            price = float(price_match.group(1).replace(",", ""))
                            break
                except Exception:
                    continue

            # Extract images
            images = []
            img_elements = await page.query_selector_all(".gallery img, .lot-image img, [data-testid='lot-image'] img")
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
            seller_elem = await page.query_selector(".house-name, .auctioneer-name")
            if seller_elem:
                seller = await seller_elem.inner_text()

            # Extract location
            location = ""
            loc_elem = await page.query_selector(".location, .auction-location")
            if loc_elem:
                location = await loc_elem.inner_text()

            # Extract auction date
            auction_date = None
            date_elem = await page.query_selector(".auction-date, .sale-date")
            if date_elem:
                date_text = await date_elem.inner_text()
                # Try to parse date
                for fmt in ["%B %d, %Y", "%m/%d/%Y", "%Y-%m-%d"]:
                    try:
                        auction_date = datetime.strptime(date_text.strip(), fmt)
                        break
                    except ValueError:
                        continue

            await context.close()

            return ScrapedListing(
                title=title.strip(),
                description=description.strip()[:1000],
                source_platform=SourcePlatform.LIVEAUCTIONEERS,
                source_url=url,
                source_id=self._extract_item_id(url),
                price=price,
                currency="USD",
                seller_name=seller.strip() if seller else None,
                location=location.strip() if location else None,
                image_urls=images,
                date_listing=auction_date,
            )

        except Exception as e:
            self.logger.error(f"Failed to get listing details", error=str(e), url=url)
            return None


class LiveAuctioneersPackageScraper(BaseScraper):
    """
    Alternative scraper using the auction-scraper package.

    Install with: pip install auction-scraper
    """

    platform = SourcePlatform.LIVEAUCTIONEERS
    BASE_URL = "https://www.liveauctioneers.com"

    def __init__(self, db_path: str = "data/liveauctioneers_cache.db"):
        super().__init__()
        self.db_path = db_path
        self.backend = None

    def _ensure_backend(self):
        """Initialize the auction-scraper backend."""
        if not AUCTION_SCRAPER_AVAILABLE:
            raise RuntimeError(
                "auction-scraper package not installed. Install with: pip install auction-scraper"
            )
        if self.backend is None:
            self.backend = LiveauctioneersBackend(self.db_path)
        return self.backend

    def build_search_queries(self) -> list[str]:
        """Build search queries."""
        return [
            "dan brown trompe l'oeil",
            "dan brown artist painting",
        ]

    async def search(self, query: str) -> list[ScrapedListing]:
        """Search using auction-scraper package."""
        try:
            backend = self._ensure_backend()

            # auction-scraper is synchronous, run in executor
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(backend.search(query, max_results=20))
            )

            listings = []
            for result in results:
                listing = ScrapedListing(
                    title=result.get("title", "Unknown"),
                    description=result.get("description", ""),
                    source_platform=SourcePlatform.LIVEAUCTIONEERS,
                    source_url=result.get("url", ""),
                    source_id=str(result.get("id", "")),
                    price=result.get("price"),
                    currency="USD",
                    image_urls=result.get("images", []),
                    raw_data=result,
                )
                listings.append(listing)

            return listings

        except Exception as e:
            self.logger.error(f"auction-scraper search failed", error=str(e))
            return []

    async def get_listing_details(self, url: str) -> Optional[ScrapedListing]:
        """Get listing details using auction-scraper."""
        try:
            backend = self._ensure_backend()

            # Extract auction ID from URL
            match = re.search(r'/item/(\d+)', url)
            if not match:
                return None

            auction_id = match.group(1)

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: backend.auction(auction_id)
            )

            if result:
                return ScrapedListing(
                    title=result.get("title", "Unknown"),
                    description=result.get("description", ""),
                    source_platform=SourcePlatform.LIVEAUCTIONEERS,
                    source_url=url,
                    source_id=auction_id,
                    price=result.get("price"),
                    currency="USD",
                    image_urls=result.get("images", []),
                    raw_data=result,
                )

        except Exception as e:
            self.logger.error(f"Failed to get details", error=str(e), url=url)

        return None

    async def close(self) -> None:
        """Cleanup."""
        self.backend = None
