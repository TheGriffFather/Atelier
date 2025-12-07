# Auction House Integrations

> Phase 4, Task 1 | Priority: High | Dependencies: None

## Overview

Expand the scraping infrastructure to systematically monitor major auction houses for artworks. Includes both API integrations (where available) and web scrapers, with a unified interface for managing auction house data sources.

## Success Criteria

- [ ] Registry of auction houses with integration status
- [ ] Scrapers for major houses (Christie's, Sotheby's, Heritage, etc.)
- [ ] Unified scraper interface with common data model
- [ ] Scheduled monitoring of upcoming sales
- [ ] Historical results tracking
- [ ] Rate limiting and polite scraping
- [ ] Error handling and retry logic
- [ ] Admin dashboard for scraper management
- [ ] Alert on new matches

## Database Changes

### New `auction_houses` Table

```sql
CREATE TABLE auction_houses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    is_active INTEGER DEFAULT 1,
    has_api INTEGER DEFAULT 0,
    scraper_class TEXT,
    api_base_url TEXT,
    website TEXT,
    requests_per_minute INTEGER DEFAULT 10,
    last_scraped DATETIME,
    total_results INTEGER DEFAULT 0,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_auction_houses_code ON auction_houses(code);
CREATE INDEX idx_auction_houses_active ON auction_houses(is_active);
```

### New `auction_results` Table

```sql
CREATE TABLE auction_results (
    id INTEGER PRIMARY KEY,
    artwork_id INTEGER REFERENCES artworks(id),
    auction_house_id INTEGER NOT NULL REFERENCES auction_houses(id),
    -- Sale info
    sale_name TEXT,
    sale_number TEXT,
    sale_date DATETIME NOT NULL,
    sale_location TEXT,
    lot_number TEXT,
    -- Listing info
    listing_title TEXT NOT NULL,
    listing_description TEXT,
    artist_as_listed TEXT,
    medium_as_listed TEXT,
    dimensions_as_listed TEXT,
    -- Estimates and results
    estimate_low REAL,
    estimate_high REAL,
    hammer_price REAL,
    premium_price REAL,
    currency TEXT DEFAULT 'USD',
    -- Status
    was_sold INTEGER DEFAULT 1,
    was_bought_in INTEGER DEFAULT 0,
    was_withdrawn INTEGER DEFAULT 0,
    -- Source
    source_url TEXT,
    source_id TEXT,
    image_url TEXT,
    local_image_path TEXT,
    -- Matching
    confidence_score REAL,
    is_matched INTEGER DEFAULT 0,
    -- Timestamps
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_auction_results_house ON auction_results(auction_house_id);
CREATE INDEX idx_auction_results_artwork ON auction_results(artwork_id);
CREATE INDEX idx_auction_results_date ON auction_results(sale_date);
CREATE INDEX idx_auction_results_source ON auction_results(source_id);
```

### New `scraper_runs` Table

```sql
CREATE TABLE scraper_runs (
    id INTEGER PRIMARY KEY,
    auction_house_id INTEGER NOT NULL REFERENCES auction_houses(id),
    status TEXT DEFAULT 'running',
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    results_found INTEGER DEFAULT 0,
    new_results INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    error_messages TEXT,  -- JSON array
    query_used TEXT,
    duration_seconds INTEGER
);

CREATE INDEX idx_scraper_runs_house ON scraper_runs(auction_house_id);
CREATE INDEX idx_scraper_runs_status ON scraper_runs(status);
```

## Supported Auction Houses

### Tier 1 (API Available or Reliable Scraping)

| House | Code | API | Status |
|-------|------|-----|--------|
| eBay | ebay | Yes | Existing |
| Heritage Auctions | heritage | Yes | Planned |
| Artnet | artnet | No (scrape) | Existing |

### Tier 2 (Web Scraping Required)

| House | Code | Difficulty | Notes |
|-------|------|------------|-------|
| Christie's | christies | Medium | Dynamic content |
| Sotheby's | sothebys | Medium | Dynamic content |
| Bonhams | bonhams | Medium | - |
| Phillips | phillips | Medium | - |
| Doyle | doyle | Easy | - |
| Skinner | skinner | Easy | Regional |

### Tier 3 (Aggregators)

| Site | Code | Type |
|------|------|------|
| Invaluable | invaluable | Aggregator |
| LiveAuctioneers | liveauctioneers | Aggregator |
| Bidsquare | bidsquare | Aggregator |

## API Endpoints

### Auction Houses

#### GET /api/auction-houses
List all auction houses.

**Response:**
```json
{
  "auction_houses": [
    {
      "id": 1,
      "name": "Christie's",
      "code": "christies",
      "is_active": true,
      "has_api": false,
      "scraper_class": "ChristiesScraper",
      "website": "https://www.christies.com",
      "last_scraped": "2025-12-05T10:00:00",
      "total_results": 45
    }
  ]
}
```

#### POST /api/auction-houses
Add auction house.

#### PATCH /api/auction-houses/{id}
Update auction house settings.

#### POST /api/auction-houses/{id}/toggle
Toggle active status.

### Scraping

#### POST /api/scrapers/run
Run scraper for specific house.

**Request:**
```json
{
  "auction_house_id": 1,
  "query": "Dan Brown",
  "date_from": "2020-01-01",
  "date_to": null
}
```

**Response:**
```json
{
  "run_id": 123,
  "status": "started",
  "message": "Scraper started for Christie's"
}
```

#### POST /api/scrapers/run-all
Run all active scrapers.

#### GET /api/scrapers/runs
Get scraper run history.

**Response:**
```json
{
  "runs": [
    {
      "id": 123,
      "auction_house": "Christie's",
      "status": "completed",
      "started_at": "2025-12-05T10:00:00",
      "duration_seconds": 45,
      "results_found": 12,
      "new_results": 3,
      "errors_count": 0
    }
  ]
}
```

#### GET /api/scrapers/runs/{id}
Get run details with errors.

### Auction Results

#### GET /api/auction-results
List auction results.

**Query Parameters:**
- `auction_house_id`: Filter by house
- `is_matched`: Filter matched/unmatched
- `artwork_id`: Results for specific artwork
- `date_from`, `date_to`: Date range
- `was_sold`: Sold/unsold filter
- `min_price`, `max_price`: Price range
- `search`: Search title/description
- `limit`, `offset`: Pagination

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "auction_house": "Christie's",
      "sale_name": "American Art",
      "sale_date": "2023-05-15",
      "lot_number": "245",
      "listing_title": "Trompe l'Oeil with Currency",
      "artist_as_listed": "Dan Brown",
      "estimate_low": 5000,
      "estimate_high": 7000,
      "hammer_price": 6500,
      "was_sold": true,
      "is_matched": true,
      "artwork_id": 42,
      "source_url": "https://..."
    }
  ],
  "total": 150
}
```

#### GET /api/auction-results/{id}
Get result details.

#### POST /api/auction-results/{id}/match
Match result to artwork.

**Request:**
```json
{
  "artwork_id": 42
}
```

#### POST /api/auction-results/{id}/unmatch
Remove match.

#### POST /api/auction-results/{id}/create-artwork
Create new artwork from result.

### Statistics

#### GET /api/auction-results/stats
Get auction statistics.

**Response:**
```json
{
  "total_results": 450,
  "matched_results": 380,
  "unmatched_results": 70,
  "by_house": {
    "christies": 120,
    "sothebys": 95,
    "heritage": 200
  },
  "price_stats": {
    "total_hammer": 1250000,
    "average_hammer": 8500,
    "highest": 45000,
    "lowest": 500
  }
}
```

## Scraper Architecture

### Base Scraper Class

```python
# src/scrapers/base_auction.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class AuctionResult:
    """Standardized auction result."""
    auction_house_code: str
    sale_name: Optional[str]
    sale_date: datetime
    lot_number: Optional[str]
    listing_title: str
    listing_description: Optional[str]
    artist_as_listed: Optional[str]
    medium_as_listed: Optional[str]
    dimensions_as_listed: Optional[str]
    estimate_low: Optional[float]
    estimate_high: Optional[float]
    hammer_price: Optional[float]
    premium_price: Optional[float]
    currency: str = "USD"
    was_sold: bool = True
    source_url: Optional[str] = None
    source_id: Optional[str] = None
    image_url: Optional[str] = None

class BaseAuctionScraper(ABC):
    """Base class for auction house scrapers."""

    code: str
    name: str
    base_url: str
    requests_per_minute: int = 10

    def __init__(self):
        self.session = None
        self.rate_limiter = RateLimiter(self.requests_per_minute)

    @abstractmethod
    async def search(
        self,
        query: str,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> list[AuctionResult]:
        """Search for auction results."""
        pass

    @abstractmethod
    async def get_upcoming_sales(self) -> list[dict]:
        """Get upcoming sales calendar."""
        pass

    async def _fetch(self, url: str) -> str:
        """Fetch URL with rate limiting."""
        await self.rate_limiter.wait()
        # Implementation
        pass
```

### Heritage Auctions Scraper

```python
# src/scrapers/heritage.py

class HeritageScraper(BaseAuctionScraper):
    """Heritage Auctions API scraper."""

    code = "heritage"
    name = "Heritage Auctions"
    base_url = "https://www.ha.com"
    has_api = True

    async def search(
        self,
        query: str,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> list[AuctionResult]:
        # Heritage has a search API
        pass
```

### Christie's Scraper

```python
# src/scrapers/christies.py

class ChristiesScraper(BaseAuctionScraper):
    """Christie's web scraper."""

    code = "christies"
    name = "Christie's"
    base_url = "https://www.christies.com"

    async def search(
        self,
        query: str,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> list[AuctionResult]:
        # Christie's search results page scraping
        pass
```

## UI Requirements

### Auction Houses Management

Location: `/admin/auction-houses`

**Layout:**

1. **House Cards/List**
   - Name and logo
   - Status badge (active/inactive)
   - API/Scraper indicator
   - Last scraped time
   - Results count
   - Quick actions (Run, Toggle, Edit)

2. **Add/Edit Modal**
   - Name, code
   - Website URL
   - API settings
   - Rate limiting
   - Notes

### Scraper Dashboard

Location: `/admin/scrapers`

**Layout:**

1. **Run Controls**
   - "Run All Active" button
   - Individual house run buttons
   - Query input for targeted search

2. **Recent Runs**
   - Status indicators
   - Results found
   - Duration
   - Error count

3. **Run Details Modal**
   - Full run log
   - Error messages
   - Results list

### Auction Results Browser

Location: `/auction-results`

**Layout:**

1. **Filters**
   - Auction house dropdown
   - Date range
   - Matched/Unmatched toggle
   - Price range
   - Search

2. **Results Grid**
   - Image thumbnail
   - Title
   - Auction house
   - Sale date
   - Hammer price
   - Match status
   - Actions

3. **Result Detail Panel**
   - Full listing info
   - Match to artwork dropdown
   - Create artwork button

### Artwork Integration

On `/artwork/{id}`:

**Auction History Tab**
- List of matched auction results
- Add result button (search/link)

## Implementation Steps

### Step 1: Database Migration

```python
# scripts/migrations/011_auction_integrations.py
"""
Migration: Auction House Integrations
Date: YYYY-MM-DD
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create auction_houses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auction_houses (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1,
            has_api INTEGER DEFAULT 0,
            scraper_class TEXT,
            api_base_url TEXT,
            website TEXT,
            requests_per_minute INTEGER DEFAULT 10,
            last_scraped DATETIME,
            total_results INTEGER DEFAULT 0,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create auction_results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auction_results (
            id INTEGER PRIMARY KEY,
            artwork_id INTEGER REFERENCES artworks(id),
            auction_house_id INTEGER NOT NULL REFERENCES auction_houses(id),
            sale_name TEXT,
            sale_number TEXT,
            sale_date DATETIME NOT NULL,
            sale_location TEXT,
            lot_number TEXT,
            listing_title TEXT NOT NULL,
            listing_description TEXT,
            artist_as_listed TEXT,
            medium_as_listed TEXT,
            dimensions_as_listed TEXT,
            estimate_low REAL,
            estimate_high REAL,
            hammer_price REAL,
            premium_price REAL,
            currency TEXT DEFAULT 'USD',
            was_sold INTEGER DEFAULT 1,
            was_bought_in INTEGER DEFAULT 0,
            was_withdrawn INTEGER DEFAULT 0,
            source_url TEXT,
            source_id TEXT,
            image_url TEXT,
            local_image_path TEXT,
            confidence_score REAL,
            is_matched INTEGER DEFAULT 0,
            scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create scraper_runs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scraper_runs (
            id INTEGER PRIMARY KEY,
            auction_house_id INTEGER NOT NULL REFERENCES auction_houses(id),
            status TEXT DEFAULT 'running',
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            results_found INTEGER DEFAULT 0,
            new_results INTEGER DEFAULT 0,
            errors_count INTEGER DEFAULT 0,
            error_messages TEXT,
            query_used TEXT,
            duration_seconds INTEGER
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auction_houses_code ON auction_houses(code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auction_results_house ON auction_results(auction_house_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auction_results_artwork ON auction_results(artwork_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auction_results_date ON auction_results(sale_date)")

    # Seed initial auction houses
    houses = [
        ("Christie's", "christies", "ChristiesScraper", "https://www.christies.com"),
        ("Sotheby's", "sothebys", "SothebysScraper", "https://www.sothebys.com"),
        ("Heritage Auctions", "heritage", "HeritageScraper", "https://www.ha.com"),
        ("Bonhams", "bonhams", "BonhamsScraper", "https://www.bonhams.com"),
        ("Phillips", "phillips", "PhillipsScraper", "https://www.phillips.com"),
    ]

    for name, code, scraper, website in houses:
        cursor.execute("""
            INSERT OR IGNORE INTO auction_houses (name, code, scraper_class, website)
            VALUES (?, ?, ?, ?)
        """, (name, code, scraper, website))

    conn.commit()
    conn.close()
    print("Migration completed successfully")

if __name__ == "__main__":
    migrate()
```

### Step 2: Update Models

Add to `src/database/models.py`:
- `AuctionHouse` model
- `AuctionResult` model
- `ScraperRun` model

### Step 3: Create Scraper Service

Create `src/services/auction_service.py`:

```python
class AuctionService:
    """Manage auction house scrapers and results."""

    async def list_houses(self) -> list:
        """List all auction houses."""
        pass

    async def get_house(self, house_id: int) -> dict:
        """Get house with stats."""
        pass

    async def update_house(self, house_id: int, data: dict) -> AuctionHouse:
        """Update house settings."""
        pass

    async def run_scraper(
        self,
        house_id: int,
        query: str = None,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> int:
        """Run scraper for house. Returns run_id."""
        pass

    async def run_all_scrapers(self) -> list[int]:
        """Run all active scrapers."""
        pass

    async def get_scraper_runs(
        self,
        house_id: int = None,
        limit: int = 50
    ) -> list:
        """Get scraper run history."""
        pass

    async def list_results(
        self,
        house_id: int = None,
        artwork_id: int = None,
        is_matched: bool = None,
        date_from: datetime = None,
        date_to: datetime = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """List auction results."""
        pass

    async def match_result(
        self,
        result_id: int,
        artwork_id: int
    ) -> None:
        """Match result to artwork."""
        pass

    async def create_artwork_from_result(
        self,
        result_id: int
    ) -> int:
        """Create artwork from auction result."""
        pass

    async def get_stats(self) -> dict:
        """Get auction statistics."""
        pass
```

### Step 4: Implement Scrapers

Create individual scraper files in `src/scrapers/`:
- `heritage.py`
- `christies.py`
- `sothebys.py`
- etc.

### Step 5: Create API Routes

Create `src/api/routes/auctions.py`

### Step 6: Create Templates and JavaScript

## Testing Requirements

### Unit Tests

```python
def test_scraper_base_class():
    """Base scraper has required methods."""

def test_rate_limiter():
    """Rate limiter respects limits."""

def test_result_parsing():
    """Results parse correctly."""

def test_match_result():
    """Matching updates both records."""
```

### Manual Testing Checklist

- [ ] View auction houses list
- [ ] Enable/disable auction house
- [ ] Run scraper manually
- [ ] View scraper run history
- [ ] Browse auction results
- [ ] Filter results
- [ ] Match result to artwork
- [ ] Create artwork from result
- [ ] View auction history on artwork

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/011_auction_integrations.py` | Create | Migration |
| `src/database/models.py` | Modify | Add models |
| `src/scrapers/base_auction.py` | Create | Base class |
| `src/scrapers/heritage.py` | Create | Heritage scraper |
| `src/scrapers/christies.py` | Create | Christie's scraper |
| `src/services/auction_service.py` | Create | Business logic |
| `src/api/routes/auctions.py` | Create | API endpoints |
| Templates and JS | Create | UI |

---

*Last updated: December 5, 2025*
