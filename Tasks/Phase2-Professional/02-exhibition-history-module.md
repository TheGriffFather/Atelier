# Exhibition History Module

> Phase 2, Task 2 | Priority: High | Dependencies: None

## Overview

Enhance the existing exhibition system to fully track where artworks have been exhibited, including solo and group shows, museum exhibitions, and gallery presentations. Links exhibitions to artworks with detailed showing information. Essential for establishing an artwork's exhibition history and scholarly documentation.

## Success Criteria

- [ ] Track exhibitions with full metadata (venue, dates, catalog info)
- [ ] Link multiple artworks to each exhibition
- [ ] Record exhibition-specific details per artwork (catalog #, illustrated, etc.)
- [ ] Search and filter exhibitions
- [ ] Exhibition detail page with all shown artworks
- [ ] Artwork detail shows exhibition history
- [ ] Import exhibitions from CSV
- [ ] Timeline view of exhibition history

## Current State

The database already has:
- `exhibitions` table (basic info)
- `artwork_exhibitions` junction table

This task enhances these tables and builds a full UI.

## Database Changes

### Modify `exhibitions` Table

Add columns to existing table:

```sql
ALTER TABLE exhibitions ADD COLUMN end_date TEXT;
ALTER TABLE exhibitions ADD COLUMN curator TEXT;
ALTER TABLE exhibitions ADD COLUMN catalog_title TEXT;
ALTER TABLE exhibitions ADD COLUMN catalog_isbn TEXT;
ALTER TABLE exhibitions ADD COLUMN traveling INTEGER DEFAULT 0;
ALTER TABLE exhibitions ADD COLUMN venue_city TEXT;
ALTER TABLE exhibitions ADD COLUMN venue_country TEXT DEFAULT 'USA';
ALTER TABLE exhibitions ADD COLUMN exhibition_type TEXT DEFAULT 'solo';
ALTER TABLE exhibitions ADD COLUMN notes TEXT;
ALTER TABLE exhibitions ADD COLUMN source_url TEXT;
ALTER TABLE exhibitions ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;
```

**Updated Schema:**

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `artist_id` | INTEGER | FK to artists (existing) |
| `year` | INTEGER | Start year (existing) |
| `venue_name` | TEXT | Venue name (existing) |
| `is_solo` | INTEGER | Solo show flag (existing) |
| `end_date` | TEXT | End date (NEW) |
| `curator` | TEXT | Curator name (NEW) |
| `catalog_title` | TEXT | Exhibition catalog title (NEW) |
| `catalog_isbn` | TEXT | Catalog ISBN (NEW) |
| `traveling` | INTEGER | Multi-venue show (NEW) |
| `venue_city` | TEXT | City (NEW) |
| `venue_country` | TEXT | Country (NEW) |
| `exhibition_type` | TEXT | Type enum (NEW) |
| `notes` | TEXT | Notes (NEW) |
| `source_url` | TEXT | Source URL (NEW) |

### Modify `artwork_exhibitions` Table

Add columns for exhibition-specific artwork info:

```sql
ALTER TABLE artwork_exhibitions ADD COLUMN catalog_number TEXT;
ALTER TABLE artwork_exhibitions ADD COLUMN plate_number TEXT;
ALTER TABLE artwork_exhibitions ADD COLUMN is_illustrated INTEGER DEFAULT 0;
ALTER TABLE artwork_exhibitions ADD COLUMN label_text TEXT;
ALTER TABLE artwork_exhibitions ADD COLUMN lent_by TEXT;
ALTER TABLE artwork_exhibitions ADD COLUMN notes TEXT;
ALTER TABLE artwork_exhibitions ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
```

**Updated Schema:**

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `artwork_id` | INTEGER | FK to artworks |
| `exhibition_id` | INTEGER | FK to exhibitions |
| `catalog_number` | TEXT | Cat. number in exhibition (NEW) |
| `plate_number` | TEXT | Plate # if illustrated (NEW) |
| `is_illustrated` | INTEGER | In catalog? (NEW) |
| `label_text` | TEXT | Exhibition label text (NEW) |
| `lent_by` | TEXT | Lender for this showing (NEW) |
| `notes` | TEXT | Notes (NEW) |

### Enums

```python
class ExhibitionType(str, Enum):
    SOLO = "solo"
    GROUP = "group"
    MUSEUM = "museum"
    RETROSPECTIVE = "retrospective"
    SURVEY = "survey"
    MEMORIAL = "memorial"
    COMMERCIAL = "commercial"  # Gallery sale exhibition
    FAIR = "fair"  # Art fair
    ONLINE = "online"
```

## API Endpoints

### Exhibitions

#### GET /api/exhibitions
List all exhibitions.

**Query Parameters:**
- `search`: Search venue/title
- `year_from`, `year_to`: Filter by year range
- `type`: Exhibition type
- `is_solo`: Boolean filter
- `artwork_id`: Filter by artwork shown
- `sort`: year, venue_name
- `limit`, `offset`: Pagination

**Response:**
```json
{
  "exhibitions": [
    {
      "id": 1,
      "year": 1985,
      "end_date": "1985-12-15",
      "venue_name": "Susan Powell Fine Art",
      "venue_city": "Madison",
      "venue_country": "USA",
      "exhibition_type": "solo",
      "is_solo": true,
      "curator": null,
      "catalog_title": "Dan Brown: Recent Paintings",
      "catalog_isbn": null,
      "traveling": false,
      "artworks_count": 12,
      "notes": null
    }
  ],
  "total": 15
}
```

#### POST /api/exhibitions
Create exhibition.

**Request:**
```json
{
  "year": 1990,
  "end_date": "1990-06-30",
  "venue_name": "New Britain Museum of American Art",
  "venue_city": "New Britain",
  "venue_country": "USA",
  "exhibition_type": "group",
  "is_solo": false,
  "curator": "Jane Smith",
  "catalog_title": "Connecticut Realists",
  "notes": "Group show of Connecticut trompe l'oeil painters"
}
```

#### GET /api/exhibitions/{id}
Get exhibition with artworks.

**Response:**
```json
{
  "id": 1,
  "year": 1985,
  "venue_name": "Susan Powell Fine Art",
  "exhibition_type": "solo",
  "artworks": [
    {
      "id": 42,
      "title": "The Harbor",
      "year_created": 1985,
      "thumbnail_url": "/api/images/42/thumbnail",
      "exhibition_details": {
        "catalog_number": "12",
        "is_illustrated": true,
        "plate_number": "Plate VII",
        "lent_by": "Private Collection"
      }
    }
  ],
  "artworks_count": 12
}
```

#### PATCH /api/exhibitions/{id}
Update exhibition.

#### DELETE /api/exhibitions/{id}
Delete exhibition (removes artwork links).

### Artwork-Exhibition Links

#### POST /api/exhibitions/{id}/artworks
Add artwork to exhibition.

**Request:**
```json
{
  "artwork_id": 42,
  "catalog_number": "12",
  "plate_number": "Plate VII",
  "is_illustrated": true,
  "lent_by": "Private Collection",
  "label_text": "Oil on canvas, 24 x 36 inches...",
  "notes": "Highlight of the exhibition"
}
```

#### PATCH /api/exhibitions/{exhibition_id}/artworks/{artwork_id}
Update artwork-exhibition link details.

#### DELETE /api/exhibitions/{exhibition_id}/artworks/{artwork_id}
Remove artwork from exhibition.

### Artwork Exhibition History

#### GET /api/artworks/{id}/exhibitions
Get exhibitions for an artwork.

**Response:**
```json
{
  "artwork_id": 42,
  "exhibitions": [
    {
      "exhibition_id": 1,
      "year": 1985,
      "venue_name": "Susan Powell Fine Art",
      "venue_city": "Madison",
      "exhibition_type": "solo",
      "catalog_number": "12",
      "is_illustrated": true
    },
    {
      "exhibition_id": 5,
      "year": 1990,
      "venue_name": "New Britain Museum",
      "venue_city": "New Britain",
      "exhibition_type": "group",
      "catalog_number": null,
      "is_illustrated": false
    }
  ],
  "total": 2
}
```

### Import

#### POST /api/exhibitions/import
Import exhibitions from CSV.

**Request (multipart/form-data):**
- `file`: CSV file

**CSV Format:**
```csv
year,venue_name,venue_city,exhibition_type,is_solo,curator,catalog_title
1985,Susan Powell Fine Art,Madison,solo,true,,Dan Brown: Recent Paintings
1990,New Britain Museum,New Britain,group,false,Jane Smith,Connecticut Realists
```

## UI Requirements

### Exhibitions List Page

Location: `/exhibitions` (new page)

**Layout:**

1. **Header**
   - "Exhibitions" title
   - "Add Exhibition" button
   - "Import CSV" button

2. **Filters Bar**
   - Search input
   - Year range (from/to)
   - Type dropdown
   - Solo/Group toggle

3. **Timeline View** (default)
   - Vertical timeline by year
   - Exhibition cards with:
     - Venue name
     - Date range
     - Type badge
     - Artworks count
   - Click to expand/view details

4. **List View** (toggle)
   - Table with sortable columns
   - Venue, Year, Type, Artworks, Actions

### Exhibition Detail Page

Location: `/exhibitions/{id}`

**Layout:**

1. **Header**
   - Exhibition title/venue
   - Date range
   - Type badge
   - Edit/Delete buttons

2. **Details Panel**
   - Venue and location
   - Curator
   - Catalog info with ISBN
   - Notes
   - Source link

3. **Artworks Grid**
   - All artworks in exhibition
   - Thumbnail, title, catalog #
   - "Add Artwork" button
   - Click to view artwork
   - Edit link button per artwork

### Artwork Detail - Exhibitions Tab

Add to `/artwork/{id}`:

1. **Exhibition History Section**
   - Chronological list
   - Each entry shows:
     - Year and venue
     - Type badge
     - Catalog # if any
     - "Illustrated" badge if illustrated
   - "Add to Exhibition" button

### Add/Edit Exhibition Modal

**Fields:**
- Year (required)
- End date (optional)
- Venue name (required)
- Venue city
- Venue country
- Exhibition type dropdown
- Solo/Group toggle
- Traveling exhibition checkbox
- Curator
- Catalog title
- Catalog ISBN
- Notes
- Source URL

### Add Artwork to Exhibition Modal

**Fields:**
- Artwork selector (search/autocomplete)
- Catalog number
- Plate number
- Illustrated checkbox
- Lent by
- Label text
- Notes

## Implementation Steps

### Step 1: Database Migration

```python
# scripts/migrations/005_exhibitions_enhanced.py
"""
Migration: Enhanced Exhibition History
Date: YYYY-MM-DD
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add columns to exhibitions table
    exhibition_columns = [
        ("end_date", "TEXT"),
        ("curator", "TEXT"),
        ("catalog_title", "TEXT"),
        ("catalog_isbn", "TEXT"),
        ("traveling", "INTEGER DEFAULT 0"),
        ("venue_city", "TEXT"),
        ("venue_country", "TEXT DEFAULT 'USA'"),
        ("exhibition_type", "TEXT DEFAULT 'solo'"),
        ("notes", "TEXT"),
        ("source_url", "TEXT"),
        ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ]

    cursor.execute("PRAGMA table_info(exhibitions)")
    existing = [col[1] for col in cursor.fetchall()]

    for col_name, col_def in exhibition_columns:
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE exhibitions ADD COLUMN {col_name} {col_def}")
            print(f"Added {col_name} to exhibitions")

    # Add columns to artwork_exhibitions table
    link_columns = [
        ("catalog_number", "TEXT"),
        ("plate_number", "TEXT"),
        ("is_illustrated", "INTEGER DEFAULT 0"),
        ("label_text", "TEXT"),
        ("lent_by", "TEXT"),
        ("notes", "TEXT"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ]

    cursor.execute("PRAGMA table_info(artwork_exhibitions)")
    existing = [col[1] for col in cursor.fetchall()]

    for col_name, col_def in link_columns:
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE artwork_exhibitions ADD COLUMN {col_name} {col_def}")
            print(f"Added {col_name} to artwork_exhibitions")

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exhibitions_year ON exhibitions(year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exhibitions_type ON exhibitions(exhibition_type)")

    conn.commit()
    conn.close()
    print("Migration completed successfully")

if __name__ == "__main__":
    migrate()
```

### Step 2: Update Models

Add to `src/database/models.py`:
- `ExhibitionType` enum
- Update `Exhibition` model with new columns
- Update `ArtworkExhibition` model (or create if missing)

### Step 3: Create Exhibition Service

Create `src/services/exhibition_service.py`:

```python
class ExhibitionService:
    """Manage exhibitions and artwork links."""

    async def list_exhibitions(
        self,
        search: str = None,
        year_from: int = None,
        year_to: int = None,
        exhibition_type: str = None,
        artwork_id: int = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """List exhibitions with filters."""
        pass

    async def get_exhibition(self, exhibition_id: int) -> dict:
        """Get exhibition with artworks."""
        pass

    async def create_exhibition(self, data: dict) -> Exhibition:
        """Create new exhibition."""
        pass

    async def update_exhibition(self, exhibition_id: int, data: dict) -> Exhibition:
        """Update exhibition."""
        pass

    async def delete_exhibition(self, exhibition_id: int) -> None:
        """Delete exhibition and links."""
        pass

    async def add_artwork(
        self,
        exhibition_id: int,
        artwork_id: int,
        details: dict
    ) -> ArtworkExhibition:
        """Add artwork to exhibition."""
        pass

    async def update_artwork_link(
        self,
        exhibition_id: int,
        artwork_id: int,
        details: dict
    ) -> ArtworkExhibition:
        """Update artwork-exhibition link."""
        pass

    async def remove_artwork(
        self,
        exhibition_id: int,
        artwork_id: int
    ) -> None:
        """Remove artwork from exhibition."""
        pass

    async def get_artwork_exhibitions(self, artwork_id: int) -> list:
        """Get exhibitions for an artwork."""
        pass

    async def import_from_csv(self, file_path: str) -> dict:
        """Import exhibitions from CSV."""
        pass

    def format_exhibition_history(self, exhibitions: list) -> str:
        """Format exhibition history for display/export."""
        lines = []
        for ex in exhibitions:
            line = f"{ex['year']}, {ex['venue_name']}"
            if ex.get('venue_city'):
                line += f", {ex['venue_city']}"
            if ex.get('catalog_number'):
                line += f", cat. no. {ex['catalog_number']}"
            lines.append(line)
        return ".\n".join(lines) + "."
```

### Step 4: Create API Routes

Create `src/api/routes/exhibitions.py`:

```python
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/exhibitions", tags=["exhibitions"])

class ExhibitionCreate(BaseModel):
    year: int
    end_date: Optional[str] = None
    venue_name: str
    venue_city: Optional[str] = None
    venue_country: str = "USA"
    exhibition_type: str = "solo"
    is_solo: bool = True
    traveling: bool = False
    curator: Optional[str] = None
    catalog_title: Optional[str] = None
    catalog_isbn: Optional[str] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None

class ArtworkExhibitionLink(BaseModel):
    artwork_id: int
    catalog_number: Optional[str] = None
    plate_number: Optional[str] = None
    is_illustrated: bool = False
    lent_by: Optional[str] = None
    label_text: Optional[str] = None
    notes: Optional[str] = None

@router.get("")
async def list_exhibitions(
    search: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    type: Optional[str] = None,
    is_solo: Optional[bool] = None,
    artwork_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0
):
    pass

@router.post("")
async def create_exhibition(exhibition: ExhibitionCreate):
    pass

@router.get("/{id}")
async def get_exhibition(id: int):
    pass

@router.patch("/{id}")
async def update_exhibition(id: int, exhibition: ExhibitionCreate):
    pass

@router.delete("/{id}")
async def delete_exhibition(id: int):
    pass

@router.post("/{id}/artworks")
async def add_artwork_to_exhibition(id: int, link: ArtworkExhibitionLink):
    pass

@router.patch("/{exhibition_id}/artworks/{artwork_id}")
async def update_artwork_link(exhibition_id: int, artwork_id: int, link: ArtworkExhibitionLink):
    pass

@router.delete("/{exhibition_id}/artworks/{artwork_id}")
async def remove_artwork_from_exhibition(exhibition_id: int, artwork_id: int):
    pass

@router.post("/import")
async def import_exhibitions(file: UploadFile = File(...)):
    pass
```

Add to artworks routes:
```python
@router.get("/{id}/exhibitions")
async def get_artwork_exhibitions(id: int):
    pass
```

### Step 5: Create Templates

Create `src/api/templates/exhibitions.html`:
- List page with timeline/table views
- Filters

Create `src/api/templates/exhibition.html`:
- Detail page
- Artworks grid

Update `src/api/templates/artwork.html`:
- Add Exhibitions tab

### Step 6: Add JavaScript

Create `src/api/static/js/exhibitions.js`:
- Timeline rendering
- List/grid toggle
- Modal handling
- CSV import

## Testing Requirements

### Unit Tests

```python
# tests/test_exhibition_service.py

def test_create_exhibition():
    """Creates exhibition with all fields."""

def test_add_artwork_to_exhibition():
    """Links artwork correctly."""

def test_remove_artwork():
    """Removes link."""

def test_exhibition_with_artworks():
    """Returns artworks with link details."""

def test_artwork_exhibition_history():
    """Returns exhibitions for artwork."""

def test_import_csv():
    """Imports exhibitions from CSV."""
```

### Integration Tests

```python
# tests/test_exhibitions_api.py

def test_list_exhibitions():
    """GET returns list."""

def test_filter_by_year():
    """Year filter works."""

def test_filter_by_artwork():
    """Artwork filter works."""

def test_create_exhibition():
    """POST creates exhibition."""

def test_add_artwork():
    """POST adds artwork link."""

def test_get_artwork_exhibitions():
    """Returns exhibition history."""
```

### Manual Testing Checklist

- [ ] View exhibitions list
- [ ] Filter by year range
- [ ] Filter by type
- [ ] Search exhibitions
- [ ] Toggle timeline/list view
- [ ] Create new exhibition
- [ ] View exhibition detail
- [ ] Add artwork to exhibition
- [ ] Edit artwork link details
- [ ] Remove artwork from exhibition
- [ ] Delete exhibition
- [ ] View exhibition history on artwork page
- [ ] Import exhibitions from CSV

## Edge Cases

1. **No Exhibitions**: Show "No exhibitions recorded" message
2. **Artwork in Multiple Exhibitions**: Handle correctly
3. **Deleting Exhibition**: Cascade delete links
4. **Duplicate Links**: Prevent same artwork twice
5. **Date Parsing**: Handle various date formats
6. **Traveling Exhibitions**: Show all venues
7. **Missing Data**: Handle optional fields gracefully

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/005_exhibitions_enhanced.py` | Create | Database migration |
| `src/database/models.py` | Modify | Add enum, update models |
| `src/services/exhibition_service.py` | Create | Business logic |
| `src/api/routes/exhibitions.py` | Create | API endpoints |
| `src/api/routes/artworks.py` | Modify | Add exhibitions endpoint |
| `src/api/main.py` | Modify | Register routes |
| `src/api/templates/exhibitions.html` | Create | List page |
| `src/api/templates/exhibition.html` | Create | Detail page |
| `src/api/templates/artwork.html` | Modify | Add tab |
| `src/api/static/js/exhibitions.js` | Create | Client logic |
| `tests/test_exhibition_service.py` | Create | Unit tests |
| `tests/test_exhibitions_api.py` | Create | API tests |

---

*Last updated: December 5, 2025*
