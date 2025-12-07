# Import/Migration Tools

> Phase 1, Task 2 | Priority: High | Dependencies: None

## Quick Reference

**Key files to understand before starting:**
- `src/database/models.py` - Artwork model with all importable fields
- `src/api/routes/artworks.py` - Pydantic model patterns (ArtworkResponse, ArtworkUpdate)
- `src/api/main.py` - How routers are registered
- `src/api/templates/base.html` - Template structure and JS utilities
- `src/database/session.py` - Database session management

## Overview

Create a robust import system that allows users to migrate data from external sources (CSV, JSON, Excel) into Atelier. The system tracks all imports for auditing, provides field mapping, handles errors gracefully, and supports rollback of failed imports.

## Success Criteria

- [ ] Import CSV files with configurable field mapping
- [ ] Import JSON files (single records or arrays)
- [ ] Import Excel files (.xlsx)
- [ ] Preview data before importing
- [ ] Map source fields to Atelier fields
- [ ] Track all imports with full audit trail
- [ ] Rollback capability for any import
- [ ] Skip duplicates or merge with existing records
- [ ] Clear error reporting per row
- [ ] Support for importing images via URL

## Database Changes

### New `import_jobs` Table

```sql
CREATE TABLE import_jobs (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_file TEXT,
    status TEXT DEFAULT 'pending',
    total_rows INTEGER DEFAULT 0,
    imported_count INTEGER DEFAULT 0,
    skipped_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    field_mapping TEXT,  -- JSON
    errors TEXT,         -- JSON
    started_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_import_jobs_status ON import_jobs(status);
CREATE INDEX idx_import_jobs_created ON import_jobs(created_at);
```

### New `imported_artworks` Table

```sql
CREATE TABLE imported_artworks (
    id INTEGER PRIMARY KEY,
    import_job_id INTEGER NOT NULL REFERENCES import_jobs(id) ON DELETE CASCADE,
    artwork_id INTEGER NOT NULL REFERENCES artworks(id),
    source_row INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_imported_artworks_job ON imported_artworks(import_job_id);
CREATE INDEX idx_imported_artworks_artwork ON imported_artworks(artwork_id);
```

### Enums

```python
class ImportStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

## API Endpoints

### Import Jobs

#### POST /api/import/upload
Upload file for import.

**Request (multipart/form-data):**
- `file`: CSV, JSON, or Excel file (required)
- `name`: Job name (optional, defaults to filename)

**Response:**
```json
{
  "job_id": 1,
  "name": "artwork_data.csv",
  "source_type": "csv",
  "total_rows": 150,
  "preview": [
    {"title": "The Harbor", "year": "1985", "medium": "Oil on canvas"},
    {"title": "Duck Decoy", "year": "1990", "medium": "Oil on panel"}
  ],
  "detected_columns": ["title", "year", "medium", "dimensions", "price"],
  "suggested_mapping": {
    "title": "title",
    "year": "year_created",
    "medium": "medium",
    "dimensions": "dimensions",
    "price": "last_sale_price"
  }
}
```

#### GET /api/import/jobs
List all import jobs.

**Query Parameters:**
- `status`: Filter by status
- `limit`: Default 50
- `offset`: Pagination

**Response:**
```json
{
  "jobs": [
    {
      "id": 1,
      "name": "Susan Powell Gallery Export",
      "source_type": "csv",
      "status": "completed",
      "total_rows": 150,
      "imported_count": 145,
      "skipped_count": 3,
      "error_count": 2,
      "created_at": "2025-12-05T10:30:00",
      "completed_at": "2025-12-05T10:32:15"
    }
  ],
  "total": 5
}
```

#### GET /api/import/jobs/{id}
Get import job details.

**Response:**
```json
{
  "id": 1,
  "name": "Susan Powell Gallery Export",
  "source_type": "csv",
  "status": "completed",
  "total_rows": 150,
  "imported_count": 145,
  "skipped_count": 3,
  "error_count": 2,
  "field_mapping": {
    "title": "title",
    "year": "year_created",
    "medium": "medium"
  },
  "errors": [
    {"row": 45, "field": "year", "error": "Invalid year format: 'circa 1985'"},
    {"row": 89, "field": "price", "error": "Cannot parse price: '$1,200-1,500'"}
  ],
  "created_at": "2025-12-05T10:30:00",
  "started_at": "2025-12-05T10:30:05",
  "completed_at": "2025-12-05T10:32:15"
}
```

#### POST /api/import/jobs/{id}/execute
Execute the import with field mapping.

**Request:**
```json
{
  "field_mapping": {
    "Title": "title",
    "Year": "year_created",
    "Medium": "medium",
    "Size": "dimensions",
    "Price": "last_sale_price",
    "Image URL": "image_url"
  },
  "options": {
    "skip_duplicates": true,
    "duplicate_check_fields": ["title", "year_created"],
    "download_images": true,
    "set_verified": false,
    "default_source_platform": "manual"
  }
}
```

**Response:**
```json
{
  "job_id": 1,
  "status": "in_progress",
  "message": "Import started. Processing 150 rows."
}
```

#### POST /api/import/jobs/{id}/cancel
Cancel a running import.

#### DELETE /api/import/jobs/{id}/rollback
Rollback an import (delete all imported artworks).

**Response:**
```json
{
  "message": "Rolled back 145 artworks from import job 1",
  "deleted_count": 145
}
```

### Field Mapping

#### GET /api/import/fields
Get list of available Atelier fields for mapping.

**Response:**
```json
{
  "fields": [
    {
      "name": "title",
      "type": "string",
      "required": true,
      "description": "Artwork title"
    },
    {
      "name": "year_created",
      "type": "integer",
      "required": false,
      "description": "Year artwork was created"
    },
    {
      "name": "medium",
      "type": "string",
      "required": false,
      "description": "Medium (e.g., 'Oil on canvas')"
    },
    {
      "name": "dimensions",
      "type": "string",
      "required": false,
      "description": "Dimensions in inches"
    },
    {
      "name": "image_url",
      "type": "url",
      "required": false,
      "description": "URL to download image from",
      "special": "Will be downloaded and stored locally"
    }
  ]
}
```

## UI Requirements

### Import Page

Location: `/import` (new page)

**Navigation:** Add "Import" link to main navigation

**Layout:**

1. **Upload Section**
   - Drag-and-drop file upload zone
   - Supported formats: CSV, JSON, XLSX
   - Max file size: 50MB
   - "Browse Files" button fallback

2. **Preview Section** (after upload)
   - Table showing first 10 rows
   - Column headers from source file
   - Row count indicator

3. **Field Mapping Section**
   - Two-column layout
   - Left: Source columns (from file)
   - Right: Dropdown of Atelier fields + "Skip" option
   - Auto-suggest based on column name similarity
   - Required fields highlighted

4. **Import Options**
   - [ ] Skip duplicates (checkbox)
   - Duplicate detection fields (multi-select)
   - [ ] Download images (checkbox)
   - [ ] Mark as verified (checkbox)
   - Source platform dropdown

5. **Action Buttons**
   - "Start Import" - Primary button
   - "Cancel" - Secondary button

### Import Progress Modal

- Progress bar (X of Y rows)
- Live status updates
- Error count
- "Cancel Import" button

### Import History Section

- Table of past imports
- Columns: Name, Date, Status, Imported/Total, Actions
- Actions: View Details, Rollback (if completed)

### Import Details Modal

- Full job metadata
- Error list with row numbers
- List of imported artworks (links)
- Rollback button

## Implementation Steps

### Step 1: Database Migration

```python
# scripts/migrations/002_import_tools.py
"""
Migration: Import/Migration Tools
Date: YYYY-MM-DD
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create import_jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_jobs (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_file TEXT,
            status TEXT DEFAULT 'pending',
            total_rows INTEGER DEFAULT 0,
            imported_count INTEGER DEFAULT 0,
            skipped_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            field_mapping TEXT,
            errors TEXT,
            started_at DATETIME,
            completed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create imported_artworks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS imported_artworks (
            id INTEGER PRIMARY KEY,
            import_job_id INTEGER NOT NULL REFERENCES import_jobs(id) ON DELETE CASCADE,
            artwork_id INTEGER NOT NULL REFERENCES artworks(id),
            source_row INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_jobs_status ON import_jobs(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_jobs_created ON import_jobs(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_imported_artworks_job ON imported_artworks(import_job_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_imported_artworks_artwork ON imported_artworks(artwork_id)")

    conn.commit()
    conn.close()
    print("Migration completed successfully")

if __name__ == "__main__":
    migrate()
```

### Step 2: Update Models

Add to `src/database/models.py`:
- `ImportStatus` enum
- `ImportJob` model
- `ImportedArtwork` model

### Step 3: Create Import Service

Create `src/services/import_service.py`:

```python
from pathlib import Path
import csv
import json
from typing import Optional
import pandas as pd  # For Excel support

class ImportService:
    """Handles data import from external files."""

    SUPPORTED_FORMATS = ['csv', 'json', 'xlsx']

    # Field name variations for auto-mapping
    FIELD_ALIASES = {
        'title': ['title', 'name', 'artwork_title', 'work_title'],
        'year_created': ['year', 'year_created', 'date', 'creation_date'],
        'medium': ['medium', 'media', 'materials', 'technique'],
        'dimensions': ['dimensions', 'size', 'measurement', 'dim'],
        'last_sale_price': ['price', 'sale_price', 'value', 'cost'],
        'description': ['description', 'desc', 'notes', 'details'],
        'signed': ['signed', 'signature', 'sign'],
        'provenance': ['provenance', 'history', 'ownership'],
    }

    async def parse_file(self, file_path: Path) -> dict:
        """Parse uploaded file and return preview data."""
        pass

    async def suggest_mapping(self, columns: list[str]) -> dict:
        """Suggest field mapping based on column names."""
        pass

    async def execute_import(
        self,
        job_id: int,
        mapping: dict,
        options: dict
    ) -> None:
        """Execute the import job."""
        pass

    async def rollback_import(self, job_id: int) -> int:
        """Delete all artworks from an import job."""
        pass

    async def check_duplicate(
        self,
        data: dict,
        check_fields: list[str]
    ) -> Optional[int]:
        """Check if artwork already exists. Returns artwork_id if found."""
        pass
```

### Step 4: Create API Routes

Create `src/api/routes/import_routes.py`:

```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/import", tags=["import"])

class FieldMapping(BaseModel):
    mapping: dict[str, str]

class ImportOptions(BaseModel):
    skip_duplicates: bool = True
    duplicate_check_fields: list[str] = ["title"]
    download_images: bool = True
    set_verified: bool = False
    default_source_platform: str = "manual"

class ExecuteImportRequest(BaseModel):
    field_mapping: dict[str, str]
    options: ImportOptions

@router.post("/upload")
async def upload_import_file(
    file: UploadFile = File(...),
    name: Optional[str] = None
):
    """Upload file and get preview."""
    pass

@router.get("/jobs")
async def list_import_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List all import jobs."""
    pass

@router.get("/jobs/{job_id}")
async def get_import_job(job_id: int):
    """Get import job details."""
    pass

@router.post("/jobs/{job_id}/execute")
async def execute_import(job_id: int, request: ExecuteImportRequest):
    """Execute import with mapping."""
    pass

@router.post("/jobs/{job_id}/cancel")
async def cancel_import(job_id: int):
    """Cancel running import."""
    pass

@router.delete("/jobs/{job_id}/rollback")
async def rollback_import(job_id: int):
    """Rollback completed import."""
    pass

@router.get("/fields")
async def get_importable_fields():
    """Get list of fields available for mapping."""
    pass
```

### Step 5: Register Routes

Update `src/api/main.py`:
```python
from src.api.routes.import_routes import router as import_router
app.include_router(import_router)
```

### Step 6: Create Import Page Template

Create `src/api/templates/import.html`:
- File upload dropzone
- Preview table
- Field mapping interface
- Options panel
- Progress modal
- History table

### Step 7: Add Navigation Link

Update `src/api/templates/base.html`:
- Add "Import" link to sidebar/navigation

### Step 8: Create JavaScript

Create `src/api/static/js/import.js`:
- File drag-and-drop handling
- AJAX for all operations
- Progress polling
- Mapping interface logic

## Testing Requirements

### Unit Tests

```python
# tests/test_import_service.py

def test_parse_csv():
    """CSV parsing returns correct structure."""

def test_parse_json_array():
    """JSON array parsing works."""

def test_parse_json_single():
    """Single JSON object parsing works."""

def test_parse_excel():
    """Excel parsing extracts data correctly."""

def test_suggest_mapping_exact_match():
    """Exact column name matches to field."""

def test_suggest_mapping_alias():
    """Column alias matches to field."""

def test_duplicate_detection():
    """Duplicate check finds existing artwork."""

def test_rollback_deletes_artworks():
    """Rollback removes all imported artworks."""
```

### Integration Tests

```python
# tests/test_import_api.py

def test_upload_csv():
    """Upload endpoint accepts CSV."""

def test_upload_invalid_format():
    """Upload rejects unsupported format."""

def test_execute_import():
    """Execute import creates artworks."""

def test_import_with_duplicates_skipped():
    """Duplicates are skipped when option set."""

def test_rollback_import():
    """Rollback deletes artworks and updates job."""

def test_cancel_running_import():
    """Cancel stops import in progress."""
```

### Manual Testing Checklist

- [ ] Upload CSV file and see preview
- [ ] Upload JSON file and see preview
- [ ] Upload Excel file and see preview
- [ ] Configure field mapping
- [ ] Execute import and verify artworks created
- [ ] Test with duplicate data (skip duplicates)
- [ ] Test import with image URLs (images downloaded)
- [ ] View import history
- [ ] Rollback an import
- [ ] Cancel a running import

## Edge Cases

1. **Large Files**: Process in chunks, don't load entire file into memory
2. **Encoding Issues**: Handle UTF-8 and Latin-1 encodings
3. **Malformed Data**: Skip bad rows, don't fail entire import
4. **Missing Required Fields**: Clear error for rows missing title
5. **Invalid Image URLs**: Log error but continue import
6. **Concurrent Imports**: Allow multiple imports, track separately
7. **Special Characters**: Handle quotes, commas in CSV fields
8. **Date Formats**: Parse various date formats for year_created
9. **Price Formats**: Parse "$1,200", "1200", "1,200.00"

## Sample Test Files

Create test files in `tests/fixtures/`:

### sample_import.csv
```csv
Title,Year,Medium,Dimensions,Price,Image URL
The Harbor,1985,Oil on canvas,24 x 36 in,$8500,https://example.com/harbor.jpg
Duck Decoy,1990,Oil on panel,12 x 16 in,$4200,
Trompe l'oeil Dollar,1988,Oil on board,8 x 10 in,$3500,https://example.com/dollar.jpg
```

### sample_import.json
```json
[
  {
    "title": "The Harbor",
    "year": 1985,
    "medium": "Oil on canvas",
    "dimensions": "24 x 36 in",
    "price": 8500
  },
  {
    "title": "Duck Decoy",
    "year": 1990,
    "medium": "Oil on panel",
    "dimensions": "12 x 16 in",
    "price": 4200
  }
]
```

## Dependencies

- `pandas` - Excel file support
- `openpyxl` - Excel file support (pandas dependency)
- `aiofiles` - Async file handling

```bash
pip install pandas openpyxl aiofiles
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/002_import_tools.py` | Create | Database migration |
| `src/database/models.py` | Modify | Add models |
| `src/services/import_service.py` | Create | Import logic |
| `src/api/routes/import_routes.py` | Create | API endpoints |
| `src/api/main.py` | Modify | Register routes |
| `src/api/templates/import.html` | Create | Import UI |
| `src/api/templates/base.html` | Modify | Add nav link |
| `src/api/static/js/import.js` | Create | Client logic |
| `tests/test_import_service.py` | Create | Unit tests |
| `tests/test_import_api.py` | Create | API tests |
| `tests/fixtures/sample_import.csv` | Create | Test data |
| `tests/fixtures/sample_import.json` | Create | Test data |

---

## Existing Code Reference

### Artwork Model Fields Available for Import

These are the fields on the `Artwork` model that can be imported (from `src/database/models.py`):

```python
# Basic info
title: str                    # REQUIRED
description: Optional[str]

# Physical characteristics
medium: Optional[str]         # e.g., "Oil on panel"
dimensions: Optional[str]     # e.g., "12 x 16 in"
dimensions_cm: Optional[str]  # e.g., "30.5 x 40.6 cm"
art_type: Optional[str]       # e.g., "Painting", "Book Cover"

# Dating
year_created: Optional[int]   # e.g., 1985
year_created_circa: bool      # Default: False

# Signature & inscriptions
signed: Optional[str]         # e.g., "Signed lower right"
inscription: Optional[str]

# Provenance & history
provenance: Optional[str]
exhibition_history: Optional[str]
literature: Optional[str]

# Condition & framing
condition: Optional[str]
framed: Optional[bool]
frame_description: Optional[str]

# Subject matter
subject_matter: Optional[str]
category: Optional[str]       # e.g., "Currency", "Still Life"

# Acquisition & Sales
last_sale_price: Optional[float]
last_sale_date: Optional[datetime]
last_sale_venue: Optional[str]
last_known_owner: Optional[str]
current_location: Optional[str]
acquisition_priority: Optional[int]  # 1-5
estimated_value: Optional[float]

# Source (for imported records)
source_platform: str = "manual"
source_url: str               # Must be unique - generate if not provided
```

### Route Registration Pattern (src/api/main.py)

Add the import router like this:

```python
from src.api.routes.import_routes import router as import_router

# In the lifespan or after app creation:
app.include_router(import_router)
```

### Adding Navigation Link (src/api/templates/base.html)

Add to the navigation section (around line 55):

```html
<a href="/import" class="nav-item {% block nav_import %}{% endblock %}" data-nav="import">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
    </svg>
    <span>Import</span>
</a>
```

### Template Pattern

New import page should follow this structure:

```html
{% extends "base.html" %}

{% block title %}Import Data | Dan Brown Catalogue Raisonné{% endblock %}

{% block nav_import %}nav-item-active{% endblock %}

{% block content %}
<div class="p-8">
    <!-- Page content -->
</div>
{% endblock %}

{% block scripts %}
<script src="/api/static/js/import.js"></script>
{% endblock %}
```

### Database Session Pattern

```python
from src.database import get_session_context, Artwork

async def create_artwork_from_import(data: dict) -> Artwork:
    async with get_session_context() as session:
        artwork = Artwork(
            title=data['title'],
            source_platform='manual',
            source_url=f"import://{uuid.uuid4()}",  # Generate unique URL
            # ... other fields
        )
        session.add(artwork)
        await session.commit()
        await session.refresh(artwork)
        return artwork
```

### Pydantic Models for Import API

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ImportSourceType(str, Enum):
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"

class ImportStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ImportPreview(BaseModel):
    """Response after file upload."""
    job_id: int
    name: str
    source_type: ImportSourceType
    total_rows: int
    preview: List[Dict[str, Any]]  # First 10 rows
    detected_columns: List[str]
    suggested_mapping: Dict[str, str]

class ImportOptions(BaseModel):
    """Import configuration options."""
    skip_duplicates: bool = True
    duplicate_check_fields: List[str] = ["title"]
    download_images: bool = True
    set_verified: bool = False
    default_source_platform: str = "manual"

class ExecuteImportRequest(BaseModel):
    """Request to execute import with mapping."""
    field_mapping: Dict[str, str]
    options: ImportOptions

class ImportJobResponse(BaseModel):
    """Response for import job details."""
    id: int
    name: str
    source_type: str
    status: str
    total_rows: int
    imported_count: int
    skipped_count: int
    error_count: int
    field_mapping: Optional[Dict[str, str]]
    errors: Optional[List[Dict[str, Any]]]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class ImportFieldInfo(BaseModel):
    """Information about an importable field."""
    name: str
    type: str
    required: bool
    description: str
    special: Optional[str] = None
```

---

*Last updated: December 2025*
