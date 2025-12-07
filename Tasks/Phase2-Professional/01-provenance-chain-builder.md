# Provenance Chain Builder

> Phase 2, Task 1 | Priority: High | Dependencies: None

## Overview

Create a comprehensive provenance tracking system that records the ownership history of each artwork as a chain of entries. Essential for scholarly catalogue raisonné work, authentication, and establishing the legitimacy of artworks.

## Success Criteria

- [ ] Record ownership history as sequential entries
- [ ] Track owner name, type, location, and dates
- [ ] Record acquisition method (purchase, gift, auction, etc.)
- [ ] Include sale details (venue, lot number, price)
- [ ] Link to known owners database for consistency
- [ ] Identify gaps in provenance chain
- [ ] Cite sources for each entry
- [ ] Visual timeline view of ownership history
- [ ] Export provenance in standard formats

## Database Changes

### New `provenance_entries` Table

```sql
CREATE TABLE provenance_entries (
    id INTEGER PRIMARY KEY,
    artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    sequence_order INTEGER NOT NULL,
    owner_name TEXT NOT NULL,
    owner_type TEXT DEFAULT 'private',
    owner_location TEXT,
    date_acquired TEXT,
    date_acquired_precision TEXT DEFAULT 'unknown',
    date_departed TEXT,
    date_departed_precision TEXT DEFAULT 'unknown',
    acquisition_method TEXT DEFAULT 'unknown',
    sale_venue TEXT,
    sale_lot_number TEXT,
    sale_price REAL,
    sale_currency TEXT DEFAULT 'USD',
    source_citation TEXT,
    notes TEXT,
    is_verified INTEGER DEFAULT 0,
    is_gap INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_provenance_artwork ON provenance_entries(artwork_id);
CREATE INDEX idx_provenance_sequence ON provenance_entries(artwork_id, sequence_order);
```

### New `known_owners` Table

```sql
CREATE TABLE known_owners (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    owner_type TEXT NOT NULL,
    location TEXT,
    active_years TEXT,
    website TEXT,
    biography TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_known_owners_name ON known_owners(name);
CREATE INDEX idx_known_owners_type ON known_owners(owner_type);
```

### Enums

```python
class OwnerType(str, Enum):
    ARTIST = "artist"
    ESTATE = "estate"
    PRIVATE = "private"
    GALLERY = "gallery"
    AUCTION_HOUSE = "auction_house"
    MUSEUM = "museum"
    INSTITUTION = "institution"
    CORPORATE = "corporate"
    UNKNOWN = "unknown"

class DatePrecision(str, Enum):
    EXACT = "exact"           # Known exact date
    YEAR = "year"             # Known year only
    CIRCA = "circa"           # Approximate
    DECADE = "decade"         # "1980s"
    RANGE = "range"           # "1985-1990"
    UNKNOWN = "unknown"

class AcquisitionMethod(str, Enum):
    UNKNOWN = "unknown"
    CREATED = "created"       # Artist created it
    INHERITED = "inherited"
    GIFTED = "gifted"
    PURCHASED = "purchased"
    AUCTION = "auction"
    CONSIGNMENT = "consignment"
    COMMISSION = "commission"
    BEQUEST = "bequest"
    EXCHANGE = "exchange"
```

## API Endpoints

### Provenance Entries

#### GET /api/artworks/{id}/provenance
Get provenance chain for an artwork.

**Response:**
```json
{
  "artwork_id": 42,
  "artwork_title": "The Harbor",
  "provenance_entries": [
    {
      "id": 1,
      "sequence_order": 1,
      "owner_name": "Dan Brown",
      "owner_type": "artist",
      "owner_location": "Connecticut",
      "date_acquired": null,
      "date_acquired_precision": "unknown",
      "date_departed": "1985",
      "date_departed_precision": "year",
      "acquisition_method": "created",
      "is_verified": true,
      "is_gap": false
    },
    {
      "id": 2,
      "sequence_order": 2,
      "owner_name": "Susan Powell Fine Art",
      "owner_type": "gallery",
      "owner_location": "Madison, CT",
      "date_acquired": "1985",
      "date_acquired_precision": "year",
      "date_departed": "1986",
      "date_departed_precision": "year",
      "acquisition_method": "consignment",
      "sale_venue": "Susan Powell Fine Art",
      "sale_price": 4500,
      "sale_currency": "USD",
      "source_citation": "Gallery records",
      "is_verified": true,
      "is_gap": false
    },
    {
      "id": 3,
      "sequence_order": 3,
      "owner_name": "Private Collection",
      "owner_type": "private",
      "owner_location": "New York",
      "date_acquired": "1986",
      "date_acquired_precision": "year",
      "date_departed": "2020",
      "date_departed_precision": "year",
      "acquisition_method": "purchased",
      "is_verified": false,
      "is_gap": false
    }
  ],
  "has_gaps": false,
  "total_entries": 3
}
```

#### POST /api/artworks/{id}/provenance
Add provenance entry.

**Request:**
```json
{
  "owner_name": "John Smith",
  "owner_type": "private",
  "owner_location": "Boston, MA",
  "date_acquired": "1990",
  "date_acquired_precision": "year",
  "acquisition_method": "purchased",
  "sale_venue": "Sotheby's",
  "sale_lot_number": "245",
  "sale_price": 8500,
  "source_citation": "Sotheby's catalog, May 1990",
  "notes": "Purchased at American Art sale",
  "insert_after": 2
}
```

`insert_after` specifies position; entries after are renumbered.

#### PATCH /api/provenance/{id}
Update provenance entry.

#### DELETE /api/provenance/{id}
Delete provenance entry. Renumbers remaining entries.

#### POST /api/artworks/{id}/provenance/reorder
Reorder provenance entries.

**Request:**
```json
{
  "entry_ids": [3, 1, 2, 5, 4]
}
```

#### POST /api/artworks/{id}/provenance/add-gap
Insert a gap marker.

**Request:**
```json
{
  "insert_after": 2,
  "estimated_years": "1990-2000",
  "notes": "Ownership unknown during this period"
}
```

### Known Owners

#### GET /api/known-owners
List known owners.

**Query Parameters:**
- `search`: Search by name
- `type`: Filter by owner type
- `limit`, `offset`: Pagination

**Response:**
```json
{
  "owners": [
    {
      "id": 1,
      "name": "Susan Powell Fine Art",
      "owner_type": "gallery",
      "location": "Madison, CT",
      "active_years": "1990-present",
      "artworks_count": 15
    }
  ],
  "total": 25
}
```

#### POST /api/known-owners
Create known owner.

#### GET /api/known-owners/{id}
Get known owner with associated artworks.

#### PATCH /api/known-owners/{id}
Update known owner.

#### DELETE /api/known-owners/{id}
Delete known owner.

### Export

#### GET /api/artworks/{id}/provenance/export
Export provenance in standard format.

**Query Parameters:**
- `format`: text, csv, or json (default: text)

**Response (text format):**
```
PROVENANCE

The Artist, Connecticut (until 1985);
Susan Powell Fine Art, Madison, CT (1985-1986);
Private Collection, New York (1986-2020);
Private Collection, current owner (2020-present).
```

## UI Requirements

### Provenance Tab on Artwork Detail

Location: `/artwork/{id}` - new "Provenance" tab

**Layout:**

1. **Timeline View**
   - Vertical timeline with entries
   - Each entry shows:
     - Owner name and type icon
     - Location
     - Date range
     - Acquisition method badge
     - Verified checkmark if verified
   - Gap markers shown with dashed line
   - "Add Entry" buttons between entries

2. **Entry Detail Panel** (on entry click)
   - Full entry details
   - Edit / Delete buttons
   - Source citation
   - Notes

3. **Actions**
   - "Add Entry" button
   - "Add Gap Marker" button
   - "Export Provenance" dropdown
   - "Verify Entry" toggle

### Add/Edit Entry Modal

**Fields:**
- Owner name (with autocomplete from known_owners)
- Owner type dropdown
- Location text field
- Date acquired (with precision selector)
- Date departed (with precision selector)
- Acquisition method dropdown
- Sale venue (optional)
- Sale lot number (optional)
- Sale price + currency (optional)
- Source citation text area
- Notes text area
- Verified checkbox

### Known Owners Management Page

Location: `/owners` (new page)

**Layout:**
- Search and filter bar
- Table of known owners
- Add Owner button
- Click row to edit

### Dashboard Integration

Add "Provenance Coverage" stat:
- "X artworks with provenance"
- "Y artworks with gaps"

## Implementation Steps

### Step 1: Database Migration

```python
# scripts/migrations/004_provenance.py
"""
Migration: Provenance Chain Builder
Date: YYYY-MM-DD
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create provenance_entries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS provenance_entries (
            id INTEGER PRIMARY KEY,
            artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
            sequence_order INTEGER NOT NULL,
            owner_name TEXT NOT NULL,
            owner_type TEXT DEFAULT 'private',
            owner_location TEXT,
            date_acquired TEXT,
            date_acquired_precision TEXT DEFAULT 'unknown',
            date_departed TEXT,
            date_departed_precision TEXT DEFAULT 'unknown',
            acquisition_method TEXT DEFAULT 'unknown',
            sale_venue TEXT,
            sale_lot_number TEXT,
            sale_price REAL,
            sale_currency TEXT DEFAULT 'USD',
            source_citation TEXT,
            notes TEXT,
            is_verified INTEGER DEFAULT 0,
            is_gap INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create known_owners table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS known_owners (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            owner_type TEXT NOT NULL,
            location TEXT,
            active_years TEXT,
            website TEXT,
            biography TEXT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_provenance_artwork ON provenance_entries(artwork_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_provenance_sequence ON provenance_entries(artwork_id, sequence_order)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_known_owners_name ON known_owners(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_known_owners_type ON known_owners(owner_type)")

    conn.commit()
    conn.close()
    print("Migration completed successfully")

if __name__ == "__main__":
    migrate()
```

### Step 2: Update Models

Add to `src/database/models.py`:
- `OwnerType`, `DatePrecision`, `AcquisitionMethod` enums
- `ProvenanceEntry` model
- `KnownOwner` model
- Relationship: `Artwork.provenance_entries`

### Step 3: Create Provenance Service

Create `src/services/provenance_service.py`:

```python
class ProvenanceService:
    """Manage artwork provenance chains."""

    async def get_provenance_chain(self, artwork_id: int) -> dict:
        """Get ordered provenance entries for artwork."""
        pass

    async def add_entry(
        self,
        artwork_id: int,
        entry_data: dict,
        insert_after: int = None
    ) -> ProvenanceEntry:
        """Add provenance entry, handling sequence ordering."""
        pass

    async def update_entry(
        self,
        entry_id: int,
        entry_data: dict
    ) -> ProvenanceEntry:
        """Update provenance entry."""
        pass

    async def delete_entry(self, entry_id: int) -> None:
        """Delete entry and renumber sequence."""
        pass

    async def reorder_entries(
        self,
        artwork_id: int,
        entry_ids: list[int]
    ) -> None:
        """Reorder entries by ID list."""
        pass

    async def add_gap_marker(
        self,
        artwork_id: int,
        insert_after: int,
        estimated_years: str = None,
        notes: str = None
    ) -> ProvenanceEntry:
        """Insert gap marker in chain."""
        pass

    async def export_provenance(
        self,
        artwork_id: int,
        format: str = 'text'
    ) -> str:
        """Export provenance in standard formats."""
        pass

    def format_provenance_text(self, entries: list) -> str:
        """Format entries as scholarly provenance text."""
        lines = []
        for entry in entries:
            if entry.is_gap:
                lines.append("[Gap in provenance]")
                continue

            line = entry.owner_name
            if entry.owner_location:
                line += f", {entry.owner_location}"

            dates = []
            if entry.date_acquired:
                dates.append(entry.date_acquired)
            if entry.date_departed:
                dates.append(entry.date_departed)

            if dates:
                line += f" ({'-'.join(dates)})"

            lines.append(line)

        return ";\n".join(lines) + "."
```

### Step 4: Create API Routes

Create `src/api/routes/provenance.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["provenance"])

class ProvenanceEntryCreate(BaseModel):
    owner_name: str
    owner_type: str = "private"
    owner_location: Optional[str] = None
    date_acquired: Optional[str] = None
    date_acquired_precision: str = "unknown"
    date_departed: Optional[str] = None
    date_departed_precision: str = "unknown"
    acquisition_method: str = "unknown"
    sale_venue: Optional[str] = None
    sale_lot_number: Optional[str] = None
    sale_price: Optional[float] = None
    sale_currency: str = "USD"
    source_citation: Optional[str] = None
    notes: Optional[str] = None
    is_verified: bool = False
    insert_after: Optional[int] = None

@router.get("/api/artworks/{artwork_id}/provenance")
async def get_provenance(artwork_id: int):
    """Get provenance chain."""
    pass

@router.post("/api/artworks/{artwork_id}/provenance")
async def add_provenance_entry(artwork_id: int, entry: ProvenanceEntryCreate):
    """Add provenance entry."""
    pass

@router.patch("/api/provenance/{entry_id}")
async def update_provenance_entry(entry_id: int, entry: ProvenanceEntryCreate):
    """Update provenance entry."""
    pass

@router.delete("/api/provenance/{entry_id}")
async def delete_provenance_entry(entry_id: int):
    """Delete provenance entry."""
    pass

@router.post("/api/artworks/{artwork_id}/provenance/reorder")
async def reorder_provenance(artwork_id: int, entry_ids: list[int]):
    """Reorder entries."""
    pass

@router.post("/api/artworks/{artwork_id}/provenance/add-gap")
async def add_gap_marker(artwork_id: int, insert_after: int, notes: Optional[str] = None):
    """Add gap marker."""
    pass

@router.get("/api/artworks/{artwork_id}/provenance/export")
async def export_provenance(artwork_id: int, format: str = "text"):
    """Export provenance."""
    pass

# Known Owners endpoints
@router.get("/api/known-owners")
async def list_known_owners(search: Optional[str] = None, type: Optional[str] = None):
    pass

@router.post("/api/known-owners")
async def create_known_owner(owner: KnownOwnerCreate):
    pass

@router.get("/api/known-owners/{owner_id}")
async def get_known_owner(owner_id: int):
    pass

@router.patch("/api/known-owners/{owner_id}")
async def update_known_owner(owner_id: int, owner: KnownOwnerCreate):
    pass

@router.delete("/api/known-owners/{owner_id}")
async def delete_known_owner(owner_id: int):
    pass
```

### Step 5: Update Artwork Detail Template

Add Provenance tab to `src/api/templates/artwork.html`:
- Timeline view
- Entry cards
- Add/Edit modal

### Step 6: Create Known Owners Page

Create `src/api/templates/owners.html`:
- Owner management interface

### Step 7: Add JavaScript

Create `src/api/static/js/provenance.js`:
- Timeline rendering
- Modal handling
- Autocomplete for known owners
- Drag-and-drop reordering

## Testing Requirements

### Unit Tests

```python
# tests/test_provenance_service.py

def test_add_entry_at_end():
    """Adding entry appends to chain."""

def test_add_entry_insert_after():
    """Insert after renumbers correctly."""

def test_delete_entry_renumbers():
    """Deleting renumbers remaining entries."""

def test_reorder_entries():
    """Reordering updates sequence_order."""

def test_export_text_format():
    """Text export follows scholarly format."""

def test_gap_marker_creation():
    """Gap marker has correct flags."""
```

### Integration Tests

```python
# tests/test_provenance_api.py

def test_get_provenance_chain():
    """Get returns ordered entries."""

def test_add_entry():
    """POST creates entry."""

def test_update_entry():
    """PATCH updates entry."""

def test_delete_entry():
    """DELETE removes and renumbers."""

def test_export_provenance():
    """Export returns formatted text."""
```

### Manual Testing Checklist

- [ ] View empty provenance (new artwork)
- [ ] Add first entry
- [ ] Add subsequent entries
- [ ] Edit an entry
- [ ] Delete an entry (verify renumbering)
- [ ] Insert entry between existing
- [ ] Add gap marker
- [ ] Reorder entries via drag-drop
- [ ] Export as text
- [ ] Export as CSV
- [ ] Use known owner autocomplete
- [ ] Create new known owner
- [ ] View owner's artworks

## Edge Cases

1. **Empty Provenance**: Show "No provenance recorded" message
2. **Single Entry**: Still show timeline
3. **Delete All Entries**: Reset to empty state
4. **Unknown Dates**: Handle "unknown" precision gracefully
5. **Currency Conversion**: Store original currency, don't convert
6. **Long Owner Names**: Truncate in timeline, full in detail
7. **Special Characters**: Handle quotes, commas in names
8. **Concurrent Edits**: Lock during reorder operation

## Standard Provenance Format

Follow Getty provenance standards:
- Semicolons between entries
- Dates in parentheses
- Location after owner name
- Sale information included

Example:
```
The Artist, Connecticut (until 1985); Susan Powell Fine Art, Madison, CT (1985-1986); Private Collection, New York, acquired from the above (1986-2020); [Current owner].
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/004_provenance.py` | Create | Database migration |
| `src/database/models.py` | Modify | Add enums and models |
| `src/services/provenance_service.py` | Create | Business logic |
| `src/api/routes/provenance.py` | Create | API endpoints |
| `src/api/main.py` | Modify | Register routes |
| `src/api/templates/artwork.html` | Modify | Add provenance tab |
| `src/api/templates/owners.html` | Create | Known owners page |
| `src/api/static/js/provenance.js` | Create | Client logic |
| `tests/test_provenance_service.py` | Create | Unit tests |
| `tests/test_provenance_api.py` | Create | API tests |

---

*Last updated: December 5, 2025*
