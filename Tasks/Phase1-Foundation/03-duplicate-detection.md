# Duplicate Detection

> Phase 1, Task 3 | Priority: High | Dependencies: Enhanced Image Management (for perceptual hashing)

## Overview

Implement a comprehensive duplicate detection system that identifies potential duplicate artworks in the database using multiple detection methods: perceptual image hashing, title similarity, and metadata matching. Provides a review interface for confirming or rejecting matches and merging duplicate records.

## Success Criteria

- [ ] Automatically detect potential duplicates when new artworks are added
- [ ] Batch scan existing artworks for duplicates
- [ ] Use perceptual hashing for image similarity (requires Task 01)
- [ ] Use fuzzy string matching for title similarity
- [ ] Use metadata matching (year, medium, dimensions)
- [ ] Review interface for confirming/rejecting matches
- [ ] Merge functionality combines data from two records
- [ ] Keep audit trail of merge decisions
- [ ] Configurable similarity thresholds
- [ ] Performance: scan 1000 images in under 5 minutes

## Database Changes

### New `duplicate_candidates` Table

```sql
CREATE TABLE duplicate_candidates (
    id INTEGER PRIMARY KEY,
    artwork_id_1 INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    artwork_id_2 INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    detection_method TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    resolution TEXT,
    merged_into_id INTEGER REFERENCES artworks(id),
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    UNIQUE(artwork_id_1, artwork_id_2)
);

CREATE INDEX idx_duplicate_candidates_status ON duplicate_candidates(status);
CREATE INDEX idx_duplicate_candidates_artwork1 ON duplicate_candidates(artwork_id_1);
CREATE INDEX idx_duplicate_candidates_artwork2 ON duplicate_candidates(artwork_id_2);
```

### Enums

```python
class DuplicateStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED_DUPLICATE = "confirmed_duplicate"
    NOT_DUPLICATE = "not_duplicate"
    MERGED = "merged"
    IGNORED = "ignored"
```

## Detection Methods

### 1. Perceptual Image Hashing

Uses `imagehash` library to generate perceptual hashes and compare similarity.

**Algorithm:**
- Generate pHash for each image (64-bit)
- Compare Hamming distance between hashes
- Distance < 10 = highly similar (>85% match)

**Thresholds:**
- `image_high`: 0.90 (very likely duplicate)
- `image_medium`: 0.80 (possible duplicate)
- `image_low`: 0.70 (worth reviewing)

### 2. Title Similarity

Uses fuzzy string matching (Levenshtein distance).

**Algorithm:**
- Normalize titles (lowercase, remove punctuation)
- Calculate similarity ratio using `difflib` or `fuzzywuzzy`
- Weight: exact title + different source = likely duplicate

**Thresholds:**
- `title_high`: 0.95 (nearly identical)
- `title_medium`: 0.85 (very similar)
- `title_low`: 0.75 (similar)

### 3. Metadata Matching

Combines multiple fields for matching.

**Fields checked:**
- Title similarity (weighted 0.4)
- Year match (weighted 0.3)
- Medium match (weighted 0.2)
- Dimensions match (weighted 0.1)

**Score calculation:**
```python
score = (
    title_sim * 0.4 +
    year_match * 0.3 +
    medium_match * 0.2 +
    dims_match * 0.1
)
```

## API Endpoints

### Detection

#### POST /api/duplicates/scan
Run duplicate scan on all artworks.

**Request:**
```json
{
  "methods": ["image_hash", "title", "metadata"],
  "thresholds": {
    "image_hash": 0.80,
    "title": 0.85,
    "metadata": 0.75
  },
  "limit": null
}
```

**Response:**
```json
{
  "scan_id": "abc123",
  "status": "started",
  "total_artworks": 156,
  "message": "Duplicate scan started"
}
```

#### GET /api/duplicates/scan/{scan_id}/status
Get scan progress.

**Response:**
```json
{
  "scan_id": "abc123",
  "status": "in_progress",
  "progress": 45,
  "total": 156,
  "candidates_found": 12
}
```

#### POST /api/artworks/{id}/check-duplicates
Check a single artwork for duplicates (useful when adding new artwork).

**Response:**
```json
{
  "artwork_id": 42,
  "potential_duplicates": [
    {
      "artwork_id": 15,
      "title": "The Harbor",
      "confidence": 0.92,
      "detection_method": "image_hash",
      "image_url": "/api/images/15/primary"
    }
  ]
}
```

### Candidates Management

#### GET /api/duplicates/candidates
List duplicate candidates.

**Query Parameters:**
- `status`: Filter by status (default: pending)
- `min_confidence`: Minimum confidence score
- `detection_method`: Filter by method
- `limit`: Default 50
- `offset`: Pagination

**Response:**
```json
{
  "candidates": [
    {
      "id": 1,
      "artwork_1": {
        "id": 42,
        "title": "The Harbor",
        "year": 1985,
        "image_url": "/api/images/42/primary"
      },
      "artwork_2": {
        "id": 15,
        "title": "The Harbor at Dawn",
        "year": 1985,
        "image_url": "/api/images/15/primary"
      },
      "detection_method": "image_hash",
      "confidence_score": 0.92,
      "status": "pending",
      "detected_at": "2025-12-05T10:30:00"
    }
  ],
  "total": 25
}
```

#### GET /api/duplicates/candidates/{id}
Get candidate details with full artwork data.

#### POST /api/duplicates/candidates/{id}/resolve
Resolve a duplicate candidate.

**Request:**
```json
{
  "resolution": "merged",
  "merge_into_id": 42,
  "notes": "Same artwork, different auction listings"
}
```

**Resolution options:**
- `merged`: Combine records (specify merge_into_id)
- `not_duplicate`: Mark as not a duplicate
- `ignored`: Ignore this match

#### POST /api/duplicates/candidates/bulk-resolve
Bulk resolve multiple candidates.

**Request:**
```json
{
  "candidate_ids": [1, 2, 3],
  "resolution": "not_duplicate"
}
```

### Merging

#### POST /api/artworks/merge
Merge two artworks.

**Request:**
```json
{
  "source_id": 15,
  "target_id": 42,
  "field_selections": {
    "title": "target",
    "description": "source",
    "medium": "target",
    "provenance": "combine"
  }
}
```

**Field selection options:**
- `source`: Use value from source artwork
- `target`: Use value from target artwork
- `combine`: Combine values (for text fields like description, provenance)

**Response:**
```json
{
  "message": "Artworks merged successfully",
  "merged_artwork_id": 42,
  "deleted_artwork_id": 15,
  "changes": {
    "images_transferred": 2,
    "fields_updated": ["description", "provenance"]
  }
}
```

## UI Requirements

### Duplicate Review Page

Location: `/duplicates` (new page)

**Navigation:** Add "Duplicates" link to main navigation (show badge with pending count)

**Layout:**

1. **Stats Bar**
   - Total pending reviews
   - Total confirmed duplicates
   - Total resolved this week

2. **Actions Bar**
   - "Run Full Scan" button
   - Filter dropdown (status, method, confidence)
   - Search

3. **Candidate List**
   - Side-by-side comparison cards
   - Each card shows:
     - Primary image
     - Title
     - Year, Medium, Dimensions
     - Source platform
     - Confidence badge
     - Detection method badge
   - Quick action buttons: Merge, Not Duplicate, Ignore

### Merge Dialog

When user clicks "Merge":

1. **Field Selection**
   - List all fields side by side
   - Radio buttons: Use Left / Use Right / Combine
   - Preview of combined result

2. **Image Selection**
   - Checkboxes for which images to keep
   - All checked by default

3. **Confirmation**
   - Summary of changes
   - Warning: "This will delete artwork #15"
   - Confirm / Cancel buttons

### Dashboard Integration

Add to main dashboard:
- "X Potential Duplicates" card linking to /duplicates
- Alert when new duplicates detected

## Implementation Steps

### Step 1: Database Migration

```python
# scripts/migrations/003_duplicate_detection.py
"""
Migration: Duplicate Detection
Date: YYYY-MM-DD
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS duplicate_candidates (
            id INTEGER PRIMARY KEY,
            artwork_id_1 INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
            artwork_id_2 INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
            detection_method TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            resolution TEXT,
            merged_into_id INTEGER REFERENCES artworks(id),
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME,
            UNIQUE(artwork_id_1, artwork_id_2)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_duplicate_candidates_status
        ON duplicate_candidates(status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_duplicate_candidates_artwork1
        ON duplicate_candidates(artwork_id_1)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_duplicate_candidates_artwork2
        ON duplicate_candidates(artwork_id_2)
    """)

    conn.commit()
    conn.close()
    print("Migration completed successfully")

if __name__ == "__main__":
    migrate()
```

### Step 2: Update Models

Add to `src/database/models.py`:
- `DuplicateStatus` enum
- `DuplicateCandidate` model

### Step 3: Create Duplicate Service

Create `src/services/duplicate_service.py`:

```python
from typing import Optional
from difflib import SequenceMatcher
import imagehash
from PIL import Image

class DuplicateService:
    """Handles duplicate detection and merging."""

    DEFAULT_THRESHOLDS = {
        'image_hash': 0.80,
        'title': 0.85,
        'metadata': 0.75
    }

    async def scan_all(
        self,
        methods: list[str],
        thresholds: dict = None
    ) -> str:
        """Run full duplicate scan. Returns scan_id."""
        pass

    async def check_artwork(
        self,
        artwork_id: int,
        methods: list[str] = None
    ) -> list[dict]:
        """Check single artwork for duplicates."""
        pass

    def compare_images(
        self,
        hash1: str,
        hash2: str
    ) -> float:
        """Compare two perceptual hashes. Returns similarity 0-1."""
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        max_distance = 64
        distance = h1 - h2
        return 1 - (distance / max_distance)

    def compare_titles(
        self,
        title1: str,
        title2: str
    ) -> float:
        """Compare two titles. Returns similarity 0-1."""
        # Normalize
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()
        return SequenceMatcher(None, t1, t2).ratio()

    def compare_metadata(
        self,
        artwork1: dict,
        artwork2: dict
    ) -> float:
        """Compare metadata fields. Returns weighted similarity 0-1."""
        pass

    async def merge_artworks(
        self,
        source_id: int,
        target_id: int,
        field_selections: dict
    ) -> dict:
        """Merge source into target artwork."""
        pass

    async def resolve_candidate(
        self,
        candidate_id: int,
        resolution: str,
        merge_into_id: Optional[int] = None,
        notes: str = None
    ) -> None:
        """Resolve a duplicate candidate."""
        pass
```

### Step 4: Create API Routes

Create `src/api/routes/duplicates.py`:

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/duplicates", tags=["duplicates"])

class ScanRequest(BaseModel):
    methods: list[str] = ["image_hash", "title", "metadata"]
    thresholds: Optional[dict] = None
    limit: Optional[int] = None

class ResolveRequest(BaseModel):
    resolution: str
    merge_into_id: Optional[int] = None
    notes: Optional[str] = None

class MergeRequest(BaseModel):
    source_id: int
    target_id: int
    field_selections: dict[str, str]

@router.post("/scan")
async def start_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks
):
    """Start duplicate scan."""
    pass

@router.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str):
    """Get scan progress."""
    pass

@router.get("/candidates")
async def list_candidates(
    status: Optional[str] = "pending",
    min_confidence: Optional[float] = None,
    detection_method: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List duplicate candidates."""
    pass

@router.get("/candidates/{id}")
async def get_candidate(id: int):
    """Get candidate details."""
    pass

@router.post("/candidates/{id}/resolve")
async def resolve_candidate(id: int, request: ResolveRequest):
    """Resolve duplicate candidate."""
    pass

@router.post("/candidates/bulk-resolve")
async def bulk_resolve(candidate_ids: list[int], resolution: str):
    """Bulk resolve candidates."""
    pass
```

Add to `src/api/routes/artworks.py`:

```python
@router.post("/{id}/check-duplicates")
async def check_duplicates(id: int):
    """Check artwork for duplicates."""
    pass

@router.post("/merge")
async def merge_artworks(request: MergeRequest):
    """Merge two artworks."""
    pass
```

### Step 5: Create Templates

Create `src/api/templates/duplicates.html`:
- Stats bar
- Candidate list with side-by-side cards
- Merge dialog
- Filters

### Step 6: Add JavaScript

Create `src/api/static/js/duplicates.js`:
- Load candidates
- Side-by-side comparison
- Merge dialog logic
- Quick actions
- Scan progress polling

### Step 7: Dashboard Integration

Update `src/api/templates/dashboard.html`:
- Add duplicate count card
- Add link to duplicates page

## Testing Requirements

### Unit Tests

```python
# tests/test_duplicate_service.py

def test_compare_images_identical():
    """Identical images return 1.0 similarity."""

def test_compare_images_similar():
    """Similar images return high similarity."""

def test_compare_images_different():
    """Different images return low similarity."""

def test_compare_titles_exact():
    """Exact titles return 1.0."""

def test_compare_titles_similar():
    """Similar titles return high score."""

def test_compare_titles_different():
    """Different titles return low score."""

def test_metadata_matching():
    """Metadata matching calculates correct weighted score."""

def test_merge_transfers_images():
    """Merge moves images from source to target."""

def test_merge_combines_provenance():
    """Merge combines text fields when requested."""
```

### Integration Tests

```python
# tests/test_duplicate_api.py

def test_start_scan():
    """Scan endpoint starts background task."""

def test_check_artwork_duplicates():
    """Check endpoint finds matching artworks."""

def test_resolve_as_duplicate():
    """Resolve marks candidate correctly."""

def test_resolve_as_not_duplicate():
    """Resolve updates status."""

def test_merge_artworks():
    """Merge combines and deletes correctly."""

def test_scan_progress():
    """Progress endpoint returns correct status."""
```

### Manual Testing Checklist

- [ ] Run full duplicate scan
- [ ] Monitor scan progress
- [ ] Review candidate list
- [ ] View candidate comparison
- [ ] Mark as not duplicate
- [ ] Ignore a candidate
- [ ] Open merge dialog
- [ ] Select field sources
- [ ] Complete merge
- [ ] Verify merged artwork has all data
- [ ] Verify source artwork deleted
- [ ] Check dashboard shows count

## Edge Cases

1. **Self-Comparison**: Never compare artwork to itself
2. **Reverse Duplicates**: Don't create (A,B) and (B,A) pairs
3. **Deleted Artworks**: Clean up candidates when artwork deleted
4. **No Images**: Skip image comparison, use other methods
5. **Missing Fields**: Handle NULL values in metadata matching
6. **Large Scans**: Process in batches, show progress
7. **Concurrent Scans**: Prevent duplicate scan jobs
8. **Circular Merges**: Prevent merging into already-merged artwork

## Performance Considerations

### Image Hash Generation
- Generate hashes on image upload (not scan time)
- Store hash in `artwork_images.perceptual_hash`
- Only compare artworks that have hashes

### Scan Optimization
- Use database query for title similarity (LIKE)
- Only compare artworks with similar years (±5 years)
- Batch image hash comparisons
- Cache comparison results

### Indexing
- Index on `perceptual_hash` for quick lookups
- Index on `year_created` for filtering
- Composite index on detection fields

## Dependencies

- `imagehash` - Perceptual hashing
- `Pillow` - Image processing
- `fuzzywuzzy` or `rapidfuzz` - Fast fuzzy matching (optional, `difflib` works too)

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/003_duplicate_detection.py` | Create | Database migration |
| `src/database/models.py` | Modify | Add enum and model |
| `src/services/duplicate_service.py` | Create | Detection logic |
| `src/api/routes/duplicates.py` | Create | API endpoints |
| `src/api/routes/artworks.py` | Modify | Add check/merge endpoints |
| `src/api/main.py` | Modify | Register routes |
| `src/api/templates/duplicates.html` | Create | Review UI |
| `src/api/templates/dashboard.html` | Modify | Add duplicate count |
| `src/api/static/js/duplicates.js` | Create | Client logic |
| `tests/test_duplicate_service.py` | Create | Unit tests |
| `tests/test_duplicate_api.py` | Create | API tests |

---

*Last updated: December 5, 2025*
