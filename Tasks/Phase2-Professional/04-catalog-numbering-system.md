# Catalog Numbering System

> Phase 2, Task 4 | Priority: Medium | Dependencies: None

## Overview

Implement a flexible catalog numbering system that assigns unique identifiers to artworks following scholarly catalogue raisonné conventions. Supports multiple numbering schemes, automatic number generation, and maintains referential integrity across the catalog.

## Success Criteria

- [ ] Configure multiple numbering schemes (e.g., chronological, by medium)
- [ ] Auto-generate catalog numbers based on scheme rules
- [ ] Manual number assignment with validation
- [ ] Prevent duplicate numbers within scheme
- [ ] Support prefixes and format patterns
- [ ] Track number changes with history
- [ ] Bulk number assignment
- [ ] Export numbered catalog

## Database Changes

### New `catalog_schemes` Table

```sql
CREATE TABLE catalog_schemes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    prefix TEXT DEFAULT '',
    number_format TEXT DEFAULT '{prefix}{number:04d}',
    next_number INTEGER DEFAULT 1,
    include_year INTEGER DEFAULT 0,
    include_medium_code INTEGER DEFAULT 0,
    medium_codes TEXT,  -- JSON
    is_default INTEGER DEFAULT 0,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_catalog_schemes_name ON catalog_schemes(name);
```

### Modify `artworks` Table

Add columns for catalog numbering:

```sql
ALTER TABLE artworks ADD COLUMN catalog_number TEXT UNIQUE;
ALTER TABLE artworks ADD COLUMN catalog_scheme_id INTEGER REFERENCES catalog_schemes(id);
ALTER TABLE artworks ADD COLUMN catalog_number_notes TEXT;
```

### New `catalog_number_history` Table

```sql
CREATE TABLE catalog_number_history (
    id INTEGER PRIMARY KEY,
    artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    old_number TEXT,
    new_number TEXT,
    reason TEXT,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_catalog_history_artwork ON catalog_number_history(artwork_id);
```

### New `related_artworks` Table

For tracking relationships (study/finished, series, etc.):

```sql
CREATE TABLE related_artworks (
    id INTEGER PRIMARY KEY,
    artwork_id_1 INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    artwork_id_2 INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(artwork_id_1, artwork_id_2)
);

CREATE INDEX idx_related_artwork1 ON related_artworks(artwork_id_1);
CREATE INDEX idx_related_artwork2 ON related_artworks(artwork_id_2);
```

### Enums

```python
class RelationshipType(str, Enum):
    STUDY_FOR = "study_for"        # artwork_1 is study for artwork_2
    VARIANT_OF = "variant_of"      # Different version
    COPY_OF = "copy_of"            # Copy by same artist
    AFTER = "after"                # Copy by different artist
    PENDANT = "pendant"            # Companion piece
    SERIES = "series"              # Part of same series
    RELATED = "related"            # General relationship
```

## Numbering Schemes

### Scheme Configuration

**Standard Chronological:**
- Prefix: "CR-" (Catalogue Raisonné)
- Format: `{prefix}{number:04d}`
- Example: CR-0001, CR-0002, CR-0053

**By Year and Sequence:**
- Format: `{prefix}{year}.{number:02d}`
- Example: DB-1985.01, DB-1985.02

**By Medium:**
- Prefix: varies by medium
- Medium codes: {"Painting": "P", "Drawing": "D", "Print": "PR"}
- Format: `{medium_code}{number:03d}`
- Example: P001, D001, PR001

### Number Format Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{prefix}` | Scheme prefix | "CR-" |
| `{number}` | Sequence number | 1, 2, 3... |
| `{number:04d}` | Zero-padded | 0001, 0002 |
| `{year}` | Artwork year | 1985 |
| `{medium_code}` | Medium code | P, D, PR |

## API Endpoints

### Schemes

#### GET /api/catalog-schemes
List all numbering schemes.

**Response:**
```json
{
  "schemes": [
    {
      "id": 1,
      "name": "Dan Brown Catalogue Raisonné",
      "prefix": "DB-",
      "number_format": "{prefix}{number:04d}",
      "next_number": 53,
      "is_default": true,
      "include_year": false,
      "include_medium_code": false,
      "artworks_count": 52
    }
  ]
}
```

#### POST /api/catalog-schemes
Create numbering scheme.

**Request:**
```json
{
  "name": "Dan Brown Catalogue Raisonné",
  "prefix": "DB-",
  "number_format": "{prefix}{number:04d}",
  "include_year": false,
  "include_medium_code": false,
  "is_default": true,
  "description": "Primary numbering for catalogue raisonné"
}
```

#### PATCH /api/catalog-schemes/{id}
Update scheme.

#### DELETE /api/catalog-schemes/{id}
Delete scheme (fails if artworks assigned).

#### POST /api/catalog-schemes/{id}/set-default
Set as default scheme.

### Number Assignment

#### POST /api/artworks/{id}/assign-number
Assign catalog number to artwork.

**Request:**
```json
{
  "scheme_id": 1,
  "number": null,  // null = auto-generate
  "reason": "Initial cataloging"
}
```

Or manual:
```json
{
  "scheme_id": 1,
  "number": "DB-0053",
  "reason": "Manually assigned per scholarly convention"
}
```

**Response:**
```json
{
  "artwork_id": 42,
  "catalog_number": "DB-0053",
  "scheme_id": 1,
  "message": "Catalog number assigned"
}
```

#### POST /api/artworks/{id}/change-number
Change existing catalog number.

**Request:**
```json
{
  "new_number": "DB-0053A",
  "reason": "Variant discovered, renumbered as sub-entry"
}
```

#### DELETE /api/artworks/{id}/catalog-number
Remove catalog number.

#### POST /api/catalog/bulk-assign
Bulk assign numbers.

**Request:**
```json
{
  "scheme_id": 1,
  "artwork_ids": [1, 2, 3, 4, 5],
  "start_number": null,  // Continue from next_number
  "reason": "Batch cataloging"
}
```

**Response:**
```json
{
  "assigned": [
    {"artwork_id": 1, "catalog_number": "DB-0053"},
    {"artwork_id": 2, "catalog_number": "DB-0054"},
    {"artwork_id": 3, "catalog_number": "DB-0055"}
  ],
  "total": 5
}
```

### Number Validation

#### GET /api/catalog/validate/{number}
Check if number is valid and available.

**Response:**
```json
{
  "number": "DB-0053",
  "valid": true,
  "available": false,
  "assigned_to_artwork_id": 42,
  "reason": "Number already assigned"
}
```

### History

#### GET /api/artworks/{id}/catalog-history
Get number change history.

**Response:**
```json
{
  "artwork_id": 42,
  "current_number": "DB-0053A",
  "history": [
    {
      "id": 1,
      "old_number": null,
      "new_number": "DB-0053",
      "reason": "Initial cataloging",
      "changed_at": "2025-12-01T10:00:00"
    },
    {
      "id": 2,
      "old_number": "DB-0053",
      "new_number": "DB-0053A",
      "reason": "Variant discovered",
      "changed_at": "2025-12-05T15:30:00"
    }
  ]
}
```

### Related Works

#### POST /api/artworks/{id}/related
Add related artwork.

**Request:**
```json
{
  "related_artwork_id": 45,
  "relationship_type": "study_for",
  "notes": "Oil sketch for the larger finished work"
}
```

#### GET /api/artworks/{id}/related
Get related artworks.

**Response:**
```json
{
  "artwork_id": 42,
  "related": [
    {
      "id": 1,
      "artwork": {
        "id": 45,
        "title": "Harbor Study",
        "catalog_number": "DB-0052",
        "year_created": 1985
      },
      "relationship_type": "study_for",
      "direction": "from",  // 45 is study FOR 42
      "notes": "Oil sketch for the larger finished work"
    }
  ]
}
```

#### DELETE /api/related/{id}
Remove relationship.

### Export

#### GET /api/catalog/export
Export numbered catalog.

**Query Parameters:**
- `scheme_id`: Filter by scheme
- `format`: csv, json, pdf
- `include_unnumbered`: Boolean

## UI Requirements

### Catalog Settings Page

Location: `/settings/catalog` (new page)

**Layout:**

1. **Schemes List**
   - Table of schemes
   - Name, Prefix, Format, Next #
   - Default badge
   - Edit/Delete buttons
   - "Add Scheme" button

2. **Add/Edit Scheme Modal**
   - Name
   - Prefix
   - Format pattern with preview
   - Include year checkbox
   - Include medium code checkbox
   - Medium codes JSON editor (if enabled)
   - Set as default checkbox
   - Description

3. **Format Preview**
   - Shows example number based on settings
   - Updates live as settings change

### Artwork Detail - Catalog Number

On `/artwork/{id}`:

1. **Catalog Number Display**
   - Show number prominently in header
   - "Not cataloged" if no number
   - Edit button

2. **Assign Number Panel** (if not numbered)
   - Scheme selector
   - Auto/Manual toggle
   - Preview next number
   - Assign button

3. **Edit Number Modal**
   - Current number
   - New number field
   - Reason text area
   - Change button

4. **Number History** (collapsible)
   - Timeline of changes

5. **Related Works Section**
   - List of related artworks
   - Relationship type badge
   - Add related work button

### Dashboard - Bulk Numbering

Add "Bulk Catalog" action:
- Select multiple artworks
- Choose scheme
- Assign numbers in batch

### Catalog Report Page

Location: `/catalog/report`

- List all artworks by catalog number
- Gaps in numbering highlighted
- Export options
- Unnumbered artworks section

## Implementation Steps

### Step 1: Database Migration

```python
# scripts/migrations/007_catalog_numbering.py
"""
Migration: Catalog Numbering System
Date: YYYY-MM-DD
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create catalog_schemes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS catalog_schemes (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            prefix TEXT DEFAULT '',
            number_format TEXT DEFAULT '{prefix}{number:04d}',
            next_number INTEGER DEFAULT 1,
            include_year INTEGER DEFAULT 0,
            include_medium_code INTEGER DEFAULT 0,
            medium_codes TEXT,
            is_default INTEGER DEFAULT 0,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_catalog_schemes_name ON catalog_schemes(name)")

    # Add columns to artworks
    cursor.execute("PRAGMA table_info(artworks)")
    existing = [col[1] for col in cursor.fetchall()]

    if 'catalog_number' not in existing:
        cursor.execute("ALTER TABLE artworks ADD COLUMN catalog_number TEXT UNIQUE")
    if 'catalog_scheme_id' not in existing:
        cursor.execute("ALTER TABLE artworks ADD COLUMN catalog_scheme_id INTEGER REFERENCES catalog_schemes(id)")
    if 'catalog_number_notes' not in existing:
        cursor.execute("ALTER TABLE artworks ADD COLUMN catalog_number_notes TEXT")

    # Create catalog_number_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS catalog_number_history (
            id INTEGER PRIMARY KEY,
            artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
            old_number TEXT,
            new_number TEXT,
            reason TEXT,
            changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_catalog_history_artwork ON catalog_number_history(artwork_id)")

    # Create related_artworks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS related_artworks (
            id INTEGER PRIMARY KEY,
            artwork_id_1 INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
            artwork_id_2 INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
            relationship_type TEXT NOT NULL,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(artwork_id_1, artwork_id_2)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_related_artwork1 ON related_artworks(artwork_id_1)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_related_artwork2 ON related_artworks(artwork_id_2)")

    conn.commit()
    conn.close()
    print("Migration completed successfully")

if __name__ == "__main__":
    migrate()
```

### Step 2: Update Models

Add to `src/database/models.py`:
- `RelationshipType` enum
- `CatalogScheme` model
- `CatalogNumberHistory` model
- `RelatedArtwork` model
- Update `Artwork` with new columns

### Step 3: Create Catalog Service

Create `src/services/catalog_service.py`:

```python
import re
from typing import Optional

class CatalogService:
    """Manage catalog numbering."""

    async def list_schemes(self) -> list:
        """List all schemes."""
        pass

    async def get_scheme(self, scheme_id: int) -> dict:
        """Get scheme details."""
        pass

    async def create_scheme(self, data: dict) -> CatalogScheme:
        """Create new scheme."""
        pass

    async def update_scheme(self, scheme_id: int, data: dict) -> CatalogScheme:
        """Update scheme."""
        pass

    async def delete_scheme(self, scheme_id: int) -> None:
        """Delete scheme (fails if artworks assigned)."""
        pass

    async def set_default_scheme(self, scheme_id: int) -> None:
        """Set as default scheme."""
        pass

    def generate_number(
        self,
        scheme: CatalogScheme,
        artwork: dict = None
    ) -> str:
        """Generate next catalog number."""
        format_str = scheme.number_format
        values = {
            'prefix': scheme.prefix,
            'number': scheme.next_number,
        }

        if scheme.include_year and artwork:
            values['year'] = artwork.get('year_created', '????')

        if scheme.include_medium_code and artwork:
            medium = artwork.get('medium', '')
            codes = scheme.medium_codes or {}
            values['medium_code'] = codes.get(medium, 'X')

        # Custom format parsing
        return self._format_number(format_str, values)

    def _format_number(self, format_str: str, values: dict) -> str:
        """Parse format string with values."""
        result = format_str
        for key, value in values.items():
            # Handle {number:04d} style formatting
            pattern = r'\{' + key + r'(?::(\d+)d)?\}'
            match = re.search(pattern, result)
            if match:
                if match.group(1):  # Zero-padding specified
                    pad = int(match.group(1))
                    formatted = str(value).zfill(pad)
                else:
                    formatted = str(value)
                result = re.sub(pattern, formatted, result)
        return result

    async def assign_number(
        self,
        artwork_id: int,
        scheme_id: int,
        number: Optional[str] = None,
        reason: str = None
    ) -> str:
        """Assign catalog number to artwork."""
        pass

    async def change_number(
        self,
        artwork_id: int,
        new_number: str,
        reason: str = None
    ) -> str:
        """Change artwork's catalog number."""
        pass

    async def remove_number(self, artwork_id: int) -> None:
        """Remove catalog number."""
        pass

    async def validate_number(
        self,
        number: str,
        exclude_artwork_id: int = None
    ) -> dict:
        """Validate number format and availability."""
        pass

    async def bulk_assign(
        self,
        scheme_id: int,
        artwork_ids: list[int],
        start_number: Optional[int] = None,
        reason: str = None
    ) -> list[dict]:
        """Bulk assign numbers to artworks."""
        pass

    async def get_number_history(self, artwork_id: int) -> list:
        """Get number change history."""
        pass

    async def add_related_work(
        self,
        artwork_id: int,
        related_id: int,
        relationship_type: str,
        notes: str = None
    ) -> RelatedArtwork:
        """Add relationship between artworks."""
        pass

    async def get_related_works(self, artwork_id: int) -> list:
        """Get related artworks."""
        pass

    async def remove_relationship(self, relationship_id: int) -> None:
        """Remove relationship."""
        pass

    async def export_catalog(
        self,
        scheme_id: int = None,
        format: str = 'csv',
        include_unnumbered: bool = False
    ) -> bytes:
        """Export catalog."""
        pass
```

### Step 4: Create API Routes

Create `src/api/routes/catalog.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api", tags=["catalog"])

class SchemeCreate(BaseModel):
    name: str
    prefix: str = ""
    number_format: str = "{prefix}{number:04d}"
    include_year: bool = False
    include_medium_code: bool = False
    medium_codes: Optional[dict] = None
    is_default: bool = False
    description: Optional[str] = None

class AssignNumber(BaseModel):
    scheme_id: int
    number: Optional[str] = None
    reason: Optional[str] = None

class ChangeNumber(BaseModel):
    new_number: str
    reason: Optional[str] = None

class RelatedWork(BaseModel):
    related_artwork_id: int
    relationship_type: str
    notes: Optional[str] = None

# Scheme endpoints
@router.get("/catalog-schemes")
async def list_schemes():
    pass

@router.post("/catalog-schemes")
async def create_scheme(scheme: SchemeCreate):
    pass

@router.patch("/catalog-schemes/{id}")
async def update_scheme(id: int, scheme: SchemeCreate):
    pass

@router.delete("/catalog-schemes/{id}")
async def delete_scheme(id: int):
    pass

@router.post("/catalog-schemes/{id}/set-default")
async def set_default_scheme(id: int):
    pass

# Number assignment endpoints
@router.post("/artworks/{id}/assign-number")
async def assign_number(id: int, data: AssignNumber):
    pass

@router.post("/artworks/{id}/change-number")
async def change_number(id: int, data: ChangeNumber):
    pass

@router.delete("/artworks/{id}/catalog-number")
async def remove_number(id: int):
    pass

@router.get("/catalog/validate/{number}")
async def validate_number(number: str):
    pass

@router.post("/catalog/bulk-assign")
async def bulk_assign(scheme_id: int, artwork_ids: list[int], reason: Optional[str] = None):
    pass

# History
@router.get("/artworks/{id}/catalog-history")
async def get_history(id: int):
    pass

# Related works
@router.post("/artworks/{id}/related")
async def add_related(id: int, data: RelatedWork):
    pass

@router.get("/artworks/{id}/related")
async def get_related(id: int):
    pass

@router.delete("/related/{id}")
async def remove_related(id: int):
    pass

# Export
@router.get("/catalog/export")
async def export_catalog(
    scheme_id: Optional[int] = None,
    format: str = "csv",
    include_unnumbered: bool = False
):
    pass
```

### Step 5: Create Templates

Create `src/api/templates/catalog-settings.html`:
- Scheme management

Create `src/api/templates/catalog-report.html`:
- Numbered catalog listing

Update `src/api/templates/artwork.html`:
- Add catalog number section
- Add related works section

### Step 6: Add JavaScript

Create `src/api/static/js/catalog.js`:
- Scheme management
- Number assignment
- Format preview
- Related works handling

## Testing Requirements

### Unit Tests

```python
# tests/test_catalog_service.py

def test_generate_simple_number():
    """Simple format generates correctly."""

def test_generate_with_year():
    """Year placeholder works."""

def test_generate_with_medium():
    """Medium code placeholder works."""

def test_validate_duplicate():
    """Duplicate number detected."""

def test_bulk_assign():
    """Bulk assignment increments correctly."""

def test_number_history_recorded():
    """Changes logged to history."""

def test_related_works():
    """Relationships created correctly."""
```

### Integration Tests

```python
# tests/test_catalog_api.py

def test_create_scheme():
    """POST creates scheme."""

def test_assign_auto_number():
    """Auto-generation works."""

def test_assign_manual_number():
    """Manual assignment works."""

def test_prevent_duplicate():
    """Duplicate number rejected."""

def test_change_number():
    """Number change recorded."""

def test_bulk_assign():
    """Bulk endpoint works."""
```

### Manual Testing Checklist

- [ ] Create new numbering scheme
- [ ] Preview number format
- [ ] Set scheme as default
- [ ] Assign auto number to artwork
- [ ] Assign manual number
- [ ] Change existing number
- [ ] View number history
- [ ] Bulk assign numbers
- [ ] Validate number availability
- [ ] Add related artwork
- [ ] View related works
- [ ] Export catalog report

## Edge Cases

1. **Duplicate Numbers**: Reject with clear error
2. **Gap in Sequence**: Allow but highlight in report
3. **Scheme Deletion**: Fail if artworks assigned
4. **Format Validation**: Ensure pattern produces valid strings
5. **Circular Relationships**: Prevent or handle gracefully
6. **Bulk Assign Partial Failure**: Transaction rollback
7. **Number Format Changes**: Warn about inconsistency
8. **Very Large Numbers**: No overflow in padding

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/007_catalog_numbering.py` | Create | Database migration |
| `src/database/models.py` | Modify | Add models |
| `src/services/catalog_service.py` | Create | Business logic |
| `src/api/routes/catalog.py` | Create | API endpoints |
| `src/api/main.py` | Modify | Register routes |
| `src/api/templates/catalog-settings.html` | Create | Settings page |
| `src/api/templates/catalog-report.html` | Create | Report page |
| `src/api/templates/artwork.html` | Modify | Add sections |
| `src/api/static/js/catalog.js` | Create | Client logic |
| `tests/test_catalog_service.py` | Create | Unit tests |
| `tests/test_catalog_api.py` | Create | API tests |

---

*Last updated: December 5, 2025*
