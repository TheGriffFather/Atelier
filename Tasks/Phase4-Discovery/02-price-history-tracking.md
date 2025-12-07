# Price History Tracking

> Phase 4, Task 2 | Priority: Medium | Dependencies: Auction House Integrations (Task 01)

## Overview

Track and analyze price history for artworks across multiple sales, providing market insights and valuation trends. Aggregates data from auction results, dealer sales, and manual entries to build comprehensive price records.

## Success Criteria

- [ ] Price history timeline for each artwork
- [ ] Multiple price sources (auction, dealer, private)
- [ ] Currency conversion and inflation adjustment
- [ ] Price trend charts and analytics
- [ ] Market comparison tools
- [ ] Valuation estimates based on comparable sales
- [ ] Export price history reports
- [ ] Alert on significant price events

## Database Changes

### New `price_records` Table

```sql
CREATE TABLE price_records (
    id INTEGER PRIMARY KEY,
    artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    -- Sale info
    sale_date DATE NOT NULL,
    sale_type TEXT NOT NULL,  -- auction, dealer, private, estimate
    -- Price details
    price REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    price_usd REAL,  -- Converted to USD for comparison
    price_type TEXT DEFAULT 'hammer',  -- hammer, premium, asking, estimate_low, estimate_high
    -- Inflation adjustment
    price_usd_adjusted REAL,  -- Adjusted for inflation to current year
    adjustment_year INTEGER,
    -- Source
    auction_result_id INTEGER REFERENCES auction_results(id),
    source_venue TEXT,
    source_url TEXT,
    source_notes TEXT,
    -- Verification
    is_verified INTEGER DEFAULT 0,
    verified_by_id INTEGER REFERENCES users(id),
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_price_records_artwork ON price_records(artwork_id);
CREATE INDEX idx_price_records_date ON price_records(sale_date);
CREATE INDEX idx_price_records_type ON price_records(sale_type);
```

### New `currency_rates` Table

```sql
CREATE TABLE currency_rates (
    id INTEGER PRIMARY KEY,
    from_currency TEXT NOT NULL,
    to_currency TEXT DEFAULT 'USD',
    rate_date DATE NOT NULL,
    rate REAL NOT NULL,
    source TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_currency, to_currency, rate_date)
);

CREATE INDEX idx_currency_rates_date ON currency_rates(rate_date);
CREATE INDEX idx_currency_rates_pair ON currency_rates(from_currency, to_currency);
```

### New `inflation_factors` Table

```sql
CREATE TABLE inflation_factors (
    id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL UNIQUE,
    factor_to_current REAL NOT NULL,  -- Multiply historic price by this
    source TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inflation_year ON inflation_factors(year);
```

### Enums

```python
class SaleType(str, Enum):
    AUCTION = "auction"
    DEALER = "dealer"
    PRIVATE = "private"
    ESTIMATE = "estimate"
    INSURANCE = "insurance"

class PriceType(str, Enum):
    HAMMER = "hammer"           # Auction hammer price
    PREMIUM = "premium"         # With buyer's premium
    ASKING = "asking"           # Listed/asking price
    FINAL = "final"             # Final sale price
    ESTIMATE_LOW = "estimate_low"
    ESTIMATE_HIGH = "estimate_high"
    INSURANCE = "insurance"
```

## API Endpoints

### Price Records

#### GET /api/artworks/{id}/prices
Get price history for artwork.

**Query Parameters:**
- `include_estimates`: Include estimate-type records
- `adjusted`: Include inflation-adjusted values

**Response:**
```json
{
  "artwork_id": 42,
  "artwork_title": "The Harbor",
  "price_history": [
    {
      "id": 1,
      "sale_date": "1985-06-15",
      "sale_type": "dealer",
      "price": 4500,
      "currency": "USD",
      "price_usd": 4500,
      "price_usd_adjusted": 12150,
      "price_type": "final",
      "source_venue": "Susan Powell Fine Art",
      "is_verified": true
    },
    {
      "id": 2,
      "sale_date": "2020-05-10",
      "sale_type": "auction",
      "price": 8500,
      "currency": "USD",
      "price_usd": 8500,
      "price_usd_adjusted": 9350,
      "price_type": "premium",
      "source_venue": "Heritage Auctions",
      "is_verified": true,
      "auction_result_id": 123
    }
  ],
  "stats": {
    "first_recorded": 4500,
    "last_recorded": 8500,
    "highest": 8500,
    "lowest": 4500,
    "average": 6500,
    "price_change_percent": 88.9
  }
}
```

#### POST /api/artworks/{id}/prices
Add price record.

**Request:**
```json
{
  "sale_date": "2015-03-20",
  "sale_type": "private",
  "price": 6000,
  "currency": "USD",
  "price_type": "final",
  "source_venue": "Private sale",
  "source_notes": "Sold through dealer"
}
```

#### PATCH /api/prices/{id}
Update price record.

#### DELETE /api/prices/{id}
Delete price record.

### Analytics

#### GET /api/artworks/{id}/prices/chart
Get chart data for artwork.

**Response:**
```json
{
  "labels": ["1985", "2020"],
  "datasets": [
    {
      "label": "Sale Price (USD)",
      "data": [4500, 8500]
    },
    {
      "label": "Adjusted Price",
      "data": [12150, 9350]
    }
  ]
}
```

#### GET /api/prices/market-analysis
Get market analysis for artist.

**Response:**
```json
{
  "total_sales": 45,
  "total_value": 385000,
  "average_price": 8555,
  "median_price": 6500,
  "by_year": {
    "2020": {"count": 5, "average": 9200},
    "2021": {"count": 8, "average": 10500}
  },
  "by_category": {
    "Currency/Trompe l'oeil": {"count": 25, "average": 9500},
    "Still Life": {"count": 12, "average": 7200}
  },
  "price_trend": "increasing",
  "trend_percent": 15.5
}
```

#### GET /api/artworks/{id}/prices/comparables
Get comparable sales.

**Response:**
```json
{
  "artwork_id": 42,
  "comparables": [
    {
      "artwork_id": 55,
      "title": "Five Dollar Bills",
      "year_created": 1986,
      "medium": "Oil on canvas",
      "dimensions": "24 x 30 in",
      "last_sale_date": "2022-05-15",
      "last_sale_price": 9500,
      "similarity_score": 0.85
    }
  ],
  "estimated_value": {
    "low": 8000,
    "mid": 9500,
    "high": 11000,
    "confidence": "medium",
    "basis": "3 comparable sales"
  }
}
```

### Currency/Inflation

#### GET /api/prices/convert
Convert currency.

**Query Parameters:**
- `amount`: Amount to convert
- `from_currency`: Source currency
- `to_currency`: Target currency (default: USD)
- `date`: Historical date (optional)

**Response:**
```json
{
  "original": 5000,
  "from_currency": "GBP",
  "to_currency": "USD",
  "converted": 6250,
  "rate": 1.25,
  "rate_date": "2025-12-05"
}
```

#### GET /api/prices/adjust-inflation
Adjust for inflation.

**Query Parameters:**
- `amount`: Amount
- `from_year`: Original year
- `to_year`: Target year (default: current)

**Response:**
```json
{
  "original": 5000,
  "from_year": 1985,
  "to_year": 2025,
  "adjusted": 13500,
  "factor": 2.7
}
```

## UI Requirements

### Price History Tab

On `/artwork/{id}`:

1. **Price Chart**
   - Line chart showing price over time
   - Toggle: Nominal / Adjusted
   - Hover for details

2. **Price Table**
   - All price records
   - Columns: Date, Type, Price, Adjusted, Source, Verified
   - Sort by date

3. **Add Price Button**
   - Modal with form

4. **Stats Summary**
   - First/Last recorded price
   - Price change %
   - Average price

### Market Analysis Page

Location: `/market`

**Layout:**

1. **Overview Stats**
   - Total sales tracked
   - Average price
   - Recent trend

2. **Price Trends Chart**
   - By year
   - By category

3. **Top Sales**
   - Highest prices achieved

4. **Category Breakdown**
   - Prices by artwork type

### Comparable Sales Modal

When viewing artwork:
- "Find Comparables" button
- Shows similar artworks with prices
- Estimated value range

## Implementation Steps

### Step 1: Database Migration

Create migration with tables for price_records, currency_rates, inflation_factors.

### Step 2: Update Models

Add models and relationships.

### Step 3: Create Price Service

Create `src/services/price_service.py`:

```python
class PriceService:
    """Track and analyze artwork prices."""

    async def get_price_history(self, artwork_id: int) -> dict:
        """Get full price history with stats."""
        pass

    async def add_price_record(
        self,
        artwork_id: int,
        price_data: dict
    ) -> PriceRecord:
        """Add price record."""
        pass

    async def update_price_record(
        self,
        record_id: int,
        price_data: dict
    ) -> PriceRecord:
        """Update price record."""
        pass

    async def import_from_auction_result(
        self,
        auction_result_id: int
    ) -> PriceRecord:
        """Import price from auction result."""
        pass

    def convert_currency(
        self,
        amount: float,
        from_currency: str,
        to_currency: str = "USD",
        date: date = None
    ) -> float:
        """Convert currency using historical rates."""
        pass

    def adjust_for_inflation(
        self,
        amount: float,
        from_year: int,
        to_year: int = None
    ) -> float:
        """Adjust for inflation."""
        pass

    async def get_market_analysis(self) -> dict:
        """Get market analysis for artist."""
        pass

    async def find_comparables(
        self,
        artwork_id: int,
        limit: int = 10
    ) -> list:
        """Find comparable sales."""
        pass

    async def estimate_value(
        self,
        artwork_id: int
    ) -> dict:
        """Estimate value based on comparables."""
        pass

    async def get_chart_data(
        self,
        artwork_id: int
    ) -> dict:
        """Get data formatted for charts."""
        pass
```

### Step 4: Currency/Inflation Data

- Seed historical exchange rates
- Seed inflation factors (CPI-based)
- Consider API for live rates (optional)

### Step 5: Create API Routes

Create `src/api/routes/prices.py`

### Step 6: Create Templates and JavaScript

Including Chart.js integration for price charts.

## Testing Requirements

### Unit Tests

```python
def test_currency_conversion():
    """Currency converts correctly."""

def test_inflation_adjustment():
    """Inflation adjustment correct."""

def test_price_stats():
    """Stats calculate correctly."""

def test_comparable_matching():
    """Comparables found correctly."""
```

### Manual Testing Checklist

- [ ] View price history
- [ ] Add manual price record
- [ ] View price chart
- [ ] Toggle nominal/adjusted
- [ ] View market analysis
- [ ] Find comparable sales
- [ ] See estimated value

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/012_price_tracking.py` | Create | Migration |
| `src/database/models.py` | Modify | Add models |
| `src/services/price_service.py` | Create | Business logic |
| `src/api/routes/prices.py` | Create | API endpoints |
| Templates and JS | Create | UI with charts |

---

*Last updated: December 5, 2025*
