# Museum Collection Search

> Phase 4, Task 3 | Priority: Low | Dependencies: None

## Overview

Search museum and institutional collections for artworks by the artist. Integrates with museum APIs (where available) and tracks institutional holdings. Helps identify works in public collections and builds relationships with institutions.

## Success Criteria

- [ ] Registry of museums/institutions
- [ ] API integrations where available (Met, Smithsonian, etc.)
- [ ] Track holdings with accession details
- [ ] Search across multiple collections
- [ ] Link holdings to catalogue artworks
- [ ] Institution contact management
- [ ] Generate institutional outreach lists

## Database Changes

### New `institutions` Table

```sql
CREATE TABLE institutions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    institution_type TEXT NOT NULL,
    city TEXT,
    state TEXT,
    country TEXT DEFAULT 'USA',
    website TEXT,
    collections_url TEXT,
    has_api INTEGER DEFAULT 0,
    api_base_url TEXT,
    contact_name TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    notes TEXT,
    last_searched DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_institutions_type ON institutions(institution_type);
CREATE INDEX idx_institutions_location ON institutions(state, city);
```

### New `institution_holdings` Table

```sql
CREATE TABLE institution_holdings (
    id INTEGER PRIMARY KEY,
    artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    institution_id INTEGER NOT NULL REFERENCES institutions(id),
    accession_number TEXT,
    department TEXT,
    date_acquired TEXT,
    acquisition_method TEXT,
    donor TEXT,
    credit_line TEXT,
    is_on_view INTEGER DEFAULT 0,
    gallery_location TEXT,
    collection_url TEXT,
    notes TEXT,
    verified INTEGER DEFAULT 0,
    verified_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(artwork_id, institution_id)
);

CREATE INDEX idx_holdings_artwork ON institution_holdings(artwork_id);
CREATE INDEX idx_holdings_institution ON institution_holdings(institution_id);
```

### New `collection_search_results` Table

```sql
CREATE TABLE collection_search_results (
    id INTEGER PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id),
    search_query TEXT,
    searched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- Result data
    external_id TEXT,
    title TEXT,
    artist_name TEXT,
    date_created TEXT,
    medium TEXT,
    dimensions TEXT,
    accession_number TEXT,
    department TEXT,
    image_url TEXT,
    collection_url TEXT,
    -- Matching
    confidence_score REAL,
    is_matched INTEGER DEFAULT 0,
    artwork_id INTEGER REFERENCES artworks(id),
    -- Status
    status TEXT DEFAULT 'new',
    reviewed_at DATETIME,
    UNIQUE(institution_id, external_id)
);

CREATE INDEX idx_search_results_institution ON collection_search_results(institution_id);
CREATE INDEX idx_search_results_status ON collection_search_results(status);
```

### Enums

```python
class InstitutionType(str, Enum):
    MUSEUM = "museum"
    LIBRARY = "library"
    ARCHIVE = "archive"
    UNIVERSITY = "university"
    HISTORICAL_SOCIETY = "historical_society"
    CORPORATE = "corporate"
    GOVERNMENT = "government"
    OTHER = "other"

class AcquisitionMethod(str, Enum):
    PURCHASE = "purchase"
    GIFT = "gift"
    BEQUEST = "bequest"
    EXCHANGE = "exchange"
    TRANSFER = "transfer"
    UNKNOWN = "unknown"
```

## Museum API Integrations

### Supported APIs

| Institution | API Available | Documentation |
|-------------|--------------|---------------|
| Metropolitan Museum | Yes | metmuseum.github.io |
| Smithsonian | Yes | api.si.edu |
| Art Institute Chicago | Yes | api.artic.edu |
| Cleveland Museum | Yes | openaccess-api.clevelandart.org |
| Harvard Art Museums | Yes | api.harvardartmuseums.org |
| Brooklyn Museum | Yes | www.brooklynmuseum.org/api |

### API Base Class

```python
# src/services/museum_apis/base.py

from abc import ABC, abstractmethod

@dataclass
class CollectionSearchResult:
    institution_code: str
    external_id: str
    title: str
    artist_name: str
    date_created: str
    medium: str
    dimensions: str
    accession_number: str
    department: str
    image_url: str
    collection_url: str

class BaseMuseumAPI(ABC):
    """Base class for museum API integrations."""

    code: str
    name: str
    base_url: str

    @abstractmethod
    async def search(self, query: str) -> list[CollectionSearchResult]:
        """Search collection."""
        pass

    @abstractmethod
    async def get_object(self, object_id: str) -> dict:
        """Get single object details."""
        pass
```

## API Endpoints

### Institutions

#### GET /api/institutions
List institutions.

**Query Parameters:**
- `type`: Filter by type
- `state`: Filter by state
- `has_api`: Filter by API availability
- `search`: Search name

**Response:**
```json
{
  "institutions": [
    {
      "id": 1,
      "name": "Metropolitan Museum of Art",
      "institution_type": "museum",
      "city": "New York",
      "state": "NY",
      "has_api": true,
      "holdings_count": 3,
      "last_searched": "2025-12-01T10:00:00"
    }
  ],
  "total": 25
}
```

#### POST /api/institutions
Add institution.

#### GET /api/institutions/{id}
Get institution with holdings.

#### PATCH /api/institutions/{id}
Update institution.

### Holdings

#### GET /api/artworks/{id}/holdings
Get institutional holdings for artwork.

**Response:**
```json
{
  "artwork_id": 42,
  "holdings": [
    {
      "id": 1,
      "institution": {
        "id": 1,
        "name": "New Britain Museum of American Art"
      },
      "accession_number": "2005.42",
      "date_acquired": "2005",
      "acquisition_method": "gift",
      "donor": "Estate of the Artist",
      "is_on_view": true,
      "gallery_location": "Gallery 5",
      "collection_url": "https://..."
    }
  ]
}
```

#### POST /api/artworks/{id}/holdings
Add holding record.

#### PATCH /api/holdings/{id}
Update holding.

### Collection Search

#### POST /api/institutions/{id}/search
Search institution's collection.

**Request:**
```json
{
  "query": "Dan Brown"
}
```

**Response:**
```json
{
  "institution_id": 1,
  "query": "Dan Brown",
  "results": [
    {
      "id": 123,
      "external_id": "12345",
      "title": "Trompe l'oeil with Currency",
      "artist_name": "Dan Brown",
      "date_created": "1985",
      "medium": "Oil on canvas",
      "accession_number": "2005.42",
      "image_url": "https://...",
      "collection_url": "https://...",
      "confidence_score": 0.95,
      "is_matched": false
    }
  ],
  "total": 3
}
```

#### POST /api/institutions/search-all
Search all institutions with APIs.

#### POST /api/collection-results/{id}/match
Match search result to artwork.

#### POST /api/collection-results/{id}/create-holding
Create holding from search result.

## UI Requirements

### Institutions Page

Location: `/institutions`

**Layout:**

1. **Institution List**
   - Sortable/filterable table
   - Name, Type, Location, Holdings Count
   - API indicator
   - Search button (if has API)

2. **Add Institution Modal**
   - Full form

3. **Institution Detail**
   - Contact info
   - Holdings list
   - Search results (if has API)

### Collection Search Interface

On institution detail or separate page:

1. **Search Form**
   - Query input
   - Institution selector (or all)
   - Search button

2. **Results Grid**
   - Image, Title, Artist, Medium
   - Match status
   - Actions: Match, Create Holding, Ignore

### Artwork Holdings Tab

On `/artwork/{id}`:

1. **Holdings List**
   - Institution name
   - Accession #
   - On view status
   - Collection link

2. **Add Holding Button**

## Implementation Steps

### Step 1: Database Migration

Create migration for institutions, institution_holdings, collection_search_results.

### Step 2: Create Museum API Services

```python
# src/services/museum_apis/met.py

class MetMuseumAPI(BaseMuseumAPI):
    """Metropolitan Museum of Art API."""

    code = "met"
    name = "Metropolitan Museum of Art"
    base_url = "https://collectionapi.metmuseum.org/public/collection/v1"

    async def search(self, query: str) -> list[CollectionSearchResult]:
        # Search endpoint: /search?q={query}
        # Returns object IDs, then fetch each
        pass

    async def get_object(self, object_id: str) -> dict:
        # Object endpoint: /objects/{objectID}
        pass
```

### Step 3: Create Institution Service

```python
class InstitutionService:
    """Manage institutions and holdings."""

    async def list_institutions(self, **filters) -> list:
        pass

    async def search_collection(
        self,
        institution_id: int,
        query: str
    ) -> list:
        pass

    async def search_all_collections(
        self,
        query: str
    ) -> dict:
        pass

    async def add_holding(
        self,
        artwork_id: int,
        institution_id: int,
        holding_data: dict
    ) -> InstitutionHolding:
        pass

    async def match_search_result(
        self,
        result_id: int,
        artwork_id: int
    ) -> None:
        pass
```

### Step 4: Create API Routes and UI

## Testing Requirements

### Unit Tests

```python
def test_met_api_search():
    """Met API search works."""

def test_add_holding():
    """Holding adds correctly."""

def test_match_result():
    """Matching works."""
```

### Manual Testing Checklist

- [ ] Add institution
- [ ] Search Met collection
- [ ] Match result to artwork
- [ ] Create holding from result
- [ ] View holdings on artwork

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/013_museum_collections.py` | Create | Migration |
| `src/database/models.py` | Modify | Add models |
| `src/services/museum_apis/base.py` | Create | Base API class |
| `src/services/museum_apis/met.py` | Create | Met API |
| `src/services/institution_service.py` | Create | Business logic |
| `src/api/routes/institutions.py` | Create | API endpoints |
| Templates and JS | Create | UI |

---

*Last updated: December 5, 2025*
