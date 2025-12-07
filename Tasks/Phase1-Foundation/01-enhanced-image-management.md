# Enhanced Image Management

> Phase 1, Task 1 | Priority: High | Dependencies: None

## Quick Reference

**Key files to understand before starting:**
- `src/database/models.py` - Current model definitions (see Existing Code section below)
- `src/api/routes/images.py` - Current image endpoints pattern
- `src/api/routes/artworks.py` - Pydantic response model patterns
- `src/api/templates/artwork.html` - Current artwork detail page
- `src/api/templates/base.html` - Base template with blocks and JS utilities

## Overview

Expand the image management system to support professional catalogue raisonné requirements including multiple image types (recto, verso, details, UV photography), image annotations, sort ordering, and perceptual hashing for duplicate detection.

## Success Criteria

- [ ] Each artwork can have multiple images with different types (front, back, signature detail, etc.)
- [ ] Images can be manually reordered with drag-and-drop
- [ ] Images can have captions and source attributions
- [ ] Image annotations can mark signature locations, damage, labels, etc.
- [ ] Perceptual hashes are generated for duplicate detection
- [ ] All existing images continue to work without migration issues
- [ ] API endpoints support all new fields
- [ ] UI provides intuitive image management

## Database Changes

### Modify `artwork_images` Table

Add these columns to the existing `artwork_images` table:

```sql
ALTER TABLE artwork_images ADD COLUMN image_type TEXT DEFAULT 'general';
ALTER TABLE artwork_images ADD COLUMN sort_order INTEGER DEFAULT 0;
ALTER TABLE artwork_images ADD COLUMN caption TEXT;
ALTER TABLE artwork_images ADD COLUMN source_attribution TEXT;
ALTER TABLE artwork_images ADD COLUMN date_taken DATETIME;
ALTER TABLE artwork_images ADD COLUMN perceptual_hash TEXT;
```

**Column Definitions:**

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `image_type` | TEXT | 'general' | ImageType enum value |
| `sort_order` | INTEGER | 0 | Display order (lower = first) |
| `caption` | TEXT | NULL | Image caption for display |
| `source_attribution` | TEXT | NULL | e.g., "Photo: Susan Powell Fine Art" |
| `date_taken` | DATETIME | NULL | When the photograph was taken |
| `perceptual_hash` | TEXT | NULL | 64-char hex hash for duplicate detection |

### New `image_annotations` Table

```sql
CREATE TABLE image_annotations (
    id INTEGER PRIMARY KEY,
    image_id INTEGER NOT NULL REFERENCES artwork_images(id) ON DELETE CASCADE,
    x_percent REAL NOT NULL,
    y_percent REAL NOT NULL,
    width_percent REAL,
    height_percent REAL,
    annotation_type TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT,
    color TEXT DEFAULT '#FFD700',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_image_annotations_image_id ON image_annotations(image_id);
```

**Column Definitions:**

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `x_percent` | REAL | Yes | X position as percentage (0-100) |
| `y_percent` | REAL | Yes | Y position as percentage (0-100) |
| `width_percent` | REAL | No | Width for rectangles (percentage) |
| `height_percent` | REAL | No | Height for rectangles (percentage) |
| `annotation_type` | TEXT | Yes | AnnotationType enum value |
| `label` | TEXT | Yes | Short label ("Signature", "Damage") |
| `description` | TEXT | No | Detailed description |
| `color` | TEXT | #FFD700 | Hex color for display marker |

### Enums (add to models.py)

```python
class ImageType(str, Enum):
    GENERAL = "general"
    FRONT = "front"           # Recto/main view
    BACK = "back"             # Verso
    SIGNATURE = "signature"   # Signature detail
    DETAIL = "detail"         # Other detail
    FRAME = "frame"           # Frame view
    UV = "uv"                 # UV photography
    IR = "ir"                 # Infrared
    XRAY = "xray"             # X-ray
    INSTALLATION = "installation"  # Installation view

class AnnotationType(str, Enum):
    SIGNATURE = "signature"
    INSCRIPTION = "inscription"
    DAMAGE = "damage"
    RESTORATION = "restoration"
    LABEL = "label"
    STAMP = "stamp"
    GENERAL = "general"
```

## API Endpoints

### Image Management

#### GET /api/artworks/{id}/images
Get all images for an artwork.

**Response:**
```json
{
  "images": [
    {
      "id": 1,
      "artwork_id": 42,
      "url": "https://...",
      "local_path": "data/images/artworks/42_1.jpg",
      "is_primary": true,
      "image_type": "front",
      "sort_order": 0,
      "caption": "Front view",
      "source_attribution": "Photo: Susan Powell Fine Art",
      "width": 1200,
      "height": 900,
      "date_taken": "2020-05-15T00:00:00",
      "perceptual_hash": "a1b2c3d4...",
      "annotations": [
        {
          "id": 1,
          "x_percent": 85.5,
          "y_percent": 92.0,
          "annotation_type": "signature",
          "label": "Signature",
          "description": "Signed 'D. Brown' lower right",
          "color": "#FFD700"
        }
      ]
    }
  ]
}
```

#### POST /api/artworks/{id}/images
Upload a new image.

**Request (multipart/form-data):**
- `file`: Image file (required)
- `image_type`: ImageType value (default: "general")
- `caption`: String (optional)
- `source_attribution`: String (optional)
- `is_primary`: Boolean (default: false)

**Response:** Created image object

#### PATCH /api/images/{id}
Update image metadata.

**Request:**
```json
{
  "image_type": "signature",
  "caption": "Artist signature detail",
  "source_attribution": "Photo: Estate of Dan Brown",
  "is_primary": false
}
```

#### POST /api/artworks/{id}/images/reorder
Reorder images.

**Request:**
```json
{
  "image_ids": [3, 1, 2, 5, 4]
}
```

Updates `sort_order` for each image based on array position.

#### DELETE /api/images/{id}
Delete an image and its annotations.

### Annotations

#### POST /api/images/{image_id}/annotations
Add annotation to image.

**Request:**
```json
{
  "x_percent": 85.5,
  "y_percent": 92.0,
  "width_percent": 10.0,
  "height_percent": 5.0,
  "annotation_type": "signature",
  "label": "Signature",
  "description": "Signed 'D. Brown' lower right",
  "color": "#FFD700"
}
```

#### PATCH /api/annotations/{id}
Update annotation.

#### DELETE /api/annotations/{id}
Delete annotation.

### Perceptual Hashing

#### POST /api/images/{id}/generate-hash
Generate perceptual hash for an image.

**Response:**
```json
{
  "id": 1,
  "perceptual_hash": "a1b2c3d4e5f6...",
  "similar_images": [
    {
      "image_id": 15,
      "artwork_id": 23,
      "similarity": 0.95
    }
  ]
}
```

#### POST /api/artworks/{id}/images/generate-all-hashes
Generate hashes for all images of an artwork.

## UI Requirements

### Artwork Detail Page - Image Gallery

Location: `/artwork/{id}` - Images section

**Requirements:**

1. **Image Grid View**
   - Show thumbnails in a responsive grid
   - Badge showing image type (e.g., "VERSO", "SIGNATURE")
   - Star icon on primary image
   - Drag handles for reordering

2. **Image Lightbox**
   - Full-size image view on click
   - Previous/Next navigation
   - Image metadata panel (type, caption, attribution)
   - Annotation overlay toggle
   - Annotation markers clickable to show details

3. **Image Management Panel**
   - Upload button (accepts multiple files)
   - Set image type dropdown
   - Caption text field
   - Source attribution field
   - Set as primary button
   - Delete button with confirmation

4. **Annotation Tool**
   - Toggle annotation mode
   - Click/drag to create annotation box
   - Annotation type selector
   - Label and description fields
   - Color picker
   - Save/Cancel buttons

### Dashboard - Bulk Image Operations

Add to dashboard toolbar:
- "Generate Image Hashes" button (processes all images without hashes)
- Progress indicator during processing

## Implementation Steps

### Step 1: Database Migration (scripts/migrations/001_enhanced_images.py)

```python
"""
Migration: Enhanced Image Management
Date: YYYY-MM-DD
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add columns to artwork_images
    columns_to_add = [
        ("image_type", "TEXT DEFAULT 'general'"),
        ("sort_order", "INTEGER DEFAULT 0"),
        ("caption", "TEXT"),
        ("source_attribution", "TEXT"),
        ("date_taken", "DATETIME"),
        ("perceptual_hash", "TEXT"),
    ]

    cursor.execute("PRAGMA table_info(artwork_images)")
    existing_columns = [col[1] for col in cursor.fetchall()]

    for col_name, col_def in columns_to_add:
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE artwork_images ADD COLUMN {col_name} {col_def}")
            print(f"Added {col_name} column")

    # Create image_annotations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS image_annotations (
            id INTEGER PRIMARY KEY,
            image_id INTEGER NOT NULL REFERENCES artwork_images(id) ON DELETE CASCADE,
            x_percent REAL NOT NULL,
            y_percent REAL NOT NULL,
            width_percent REAL,
            height_percent REAL,
            annotation_type TEXT NOT NULL,
            label TEXT NOT NULL,
            description TEXT,
            color TEXT DEFAULT '#FFD700',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_image_annotations_image_id
        ON image_annotations(image_id)
    """)

    conn.commit()
    conn.close()
    print("Migration completed successfully")

if __name__ == "__main__":
    migrate()
```

### Step 2: Update Models (src/database/models.py)

1. Add `ImageType` and `AnnotationType` enums
2. Add new columns to `ArtworkImage` model
3. Add `ImageAnnotation` model
4. Add relationship: `ArtworkImage.annotations`

### Step 3: Create Image Service (src/services/image_service.py)

Update or create service with:
- `generate_perceptual_hash(image_path: str) -> str`
- `find_similar_images(hash: str, threshold: float = 0.9) -> list`
- `reorder_images(artwork_id: int, image_ids: list[int])`

**Perceptual Hashing Library:** Use `imagehash` package
```bash
pip install imagehash Pillow
```

```python
import imagehash
from PIL import Image

def generate_perceptual_hash(image_path: str) -> str:
    img = Image.open(image_path)
    return str(imagehash.phash(img))

def calculate_similarity(hash1: str, hash2: str) -> float:
    h1 = imagehash.hex_to_hash(hash1)
    h2 = imagehash.hex_to_hash(hash2)
    # Hamming distance - lower is more similar
    # Convert to similarity score (0-1)
    max_distance = 64  # For 64-bit hash
    distance = h1 - h2
    return 1 - (distance / max_distance)
```

### Step 4: API Routes (src/api/routes/images.py)

Expand existing routes with new endpoints listed above.

### Step 5: Update Templates

1. Update `artwork.html` with enhanced image gallery
2. Add annotation UI components
3. Add image type badges and management controls

### Step 6: Add JavaScript for Interactions

Create `static/js/image-manager.js`:
- Drag-and-drop reordering (use Sortable.js or similar)
- Lightbox with annotation overlay
- Annotation drawing tool
- AJAX calls for all operations

## Testing Requirements

### Unit Tests

```python
# tests/test_image_service.py

def test_generate_perceptual_hash():
    """Hash generation produces consistent 64-char hex string."""

def test_similar_images_detected():
    """Two similar images return high similarity score."""

def test_different_images_not_similar():
    """Two different images return low similarity score."""

def test_reorder_images_updates_sort_order():
    """Reordering updates sort_order correctly."""
```

### Integration Tests

```python
# tests/test_image_api.py

def test_upload_image_with_type():
    """Upload image with image_type sets correctly."""

def test_update_image_caption():
    """PATCH updates caption."""

def test_create_annotation():
    """POST creates annotation at correct position."""

def test_delete_annotation():
    """DELETE removes annotation."""

def test_reorder_images_endpoint():
    """POST reorder updates all sort_orders."""
```

### Manual Testing Checklist

- [ ] Upload multiple images to an artwork
- [ ] Set different image types
- [ ] Reorder images via drag-and-drop
- [ ] Create annotation on image
- [ ] Edit annotation position
- [ ] Delete annotation
- [ ] View annotations in lightbox
- [ ] Generate perceptual hashes
- [ ] Check that similar images are flagged

## Edge Cases

1. **Large Images**: Resize before hashing for performance
2. **Missing Images**: Handle missing files gracefully when generating hashes
3. **Annotation on Resized Display**: Use percentages, not pixels
4. **Primary Image Deletion**: Automatically set next image as primary
5. **Hash Collisions**: Use multiple hash algorithms for better accuracy
6. **Concurrent Uploads**: Handle race conditions in sort_order

## Dependencies

- `imagehash` - Perceptual hashing
- `Pillow` - Image processing
- Sortable.js (CDN) - Drag-and-drop reordering

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/001_enhanced_images.py` | Create | Database migration |
| `src/database/models.py` | Modify | Add enums, columns, ImageAnnotation |
| `src/services/image_service.py` | Modify | Hash generation, similarity |
| `src/api/routes/images.py` | Modify | New API endpoints |
| `src/api/templates/artwork.html` | Modify | Enhanced gallery UI |
| `src/api/static/js/image-manager.js` | Create | Client-side interactions |
| `tests/test_image_service.py` | Create | Unit tests |
| `tests/test_image_api.py` | Create | API tests |

---

## Existing Code Reference

### Current ArtworkImage Model (src/database/models.py)

This is the existing model you'll be modifying:

```python
class ArtworkImage(Base):
    """Images associated with an artwork listing."""
    __tablename__ = "artwork_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    artwork_id: Mapped[int] = mapped_column(ForeignKey("artworks.id"))

    url: Mapped[str] = mapped_column(Text)
    local_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False)

    # Image metadata
    width: Mapped[Optional[int]] = mapped_column(nullable=True)
    height: Mapped[Optional[int]] = mapped_column(nullable=True)

    date_downloaded: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    artwork: Mapped["Artwork"] = relationship(back_populates="images")
```

**Add these fields to the model:**
```python
    # New fields for enhanced image management
    image_type: Mapped[str] = mapped_column(default="general")
    sort_order: Mapped[int] = mapped_column(default=0)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_attribution: Mapped[Optional[str]] = mapped_column(nullable=True)
    date_taken: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    perceptual_hash: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Relationship to annotations
    annotations: Mapped[list["ImageAnnotation"]] = relationship(
        back_populates="image", cascade="all, delete-orphan"
    )
```

### Current Images Route Pattern (src/api/routes/images.py)

Follow this existing pattern for new endpoints:

```python
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

class ImageDownloadResponse(BaseModel):
    """Response for image download operations."""
    message: str
    downloaded: int
    skipped: int
    failed: int

@router.post("/download", response_model=ImageDownloadStatus)
async def trigger_image_download(
    background_tasks: BackgroundTasks,
    artwork_id: Optional[int] = Query(None, description="Download images for specific artwork"),
    limit: int = Query(100, le=500, description="Maximum images to download"),
):
    """Trigger background download of artwork images."""
    # ... implementation
```

### Pydantic Models to Create

Add these to `src/api/routes/images.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ImageResponse(BaseModel):
    """Response model for a single image."""
    id: int
    artwork_id: int
    url: Optional[str]
    local_path: Optional[str]
    is_primary: bool
    image_type: str
    sort_order: int
    caption: Optional[str]
    source_attribution: Optional[str]
    width: Optional[int]
    height: Optional[int]
    date_taken: Optional[datetime]
    perceptual_hash: Optional[str]
    annotations: List["AnnotationResponse"] = []

    class Config:
        from_attributes = True

class AnnotationResponse(BaseModel):
    """Response model for an image annotation."""
    id: int
    x_percent: float
    y_percent: float
    width_percent: Optional[float]
    height_percent: Optional[float]
    annotation_type: str
    label: str
    description: Optional[str]
    color: str

    class Config:
        from_attributes = True

class ImageUpdate(BaseModel):
    """Request model for updating an image."""
    image_type: Optional[str] = None
    caption: Optional[str] = None
    source_attribution: Optional[str] = None
    is_primary: Optional[bool] = None

class AnnotationCreate(BaseModel):
    """Request model for creating an annotation."""
    x_percent: float = Field(..., ge=0, le=100)
    y_percent: float = Field(..., ge=0, le=100)
    width_percent: Optional[float] = Field(None, ge=0, le=100)
    height_percent: Optional[float] = Field(None, ge=0, le=100)
    annotation_type: str
    label: str
    description: Optional[str] = None
    color: str = "#FFD700"

class ReorderRequest(BaseModel):
    """Request model for reordering images."""
    image_ids: List[int]
```

### Template Pattern (src/api/templates)

Templates extend `base.html` and use these blocks:

```html
{% extends "base.html" %}

{% block title %}Page Title | Dan Brown Catalogue Raisonné{% endblock %}

{% block head %}
<!-- Additional CSS or meta tags -->
{% endblock %}

{% block content %}
<!-- Main page content goes here -->
{% endblock %}

{% block scripts %}
<!-- Page-specific JavaScript -->
<script src="/api/static/js/your-script.js"></script>
{% endblock %}
```

**Base template provides these JS utilities:**
- `showToast(message, type)` - Show toast notifications ('info', 'success', 'error')
- `escapeHtml(text)` - XSS prevention
- `formatCurrency(value, currency)` - Currency formatting
- `debounce(func, wait)` - Debounce utility
- `API.get(endpoint)`, `API.post(endpoint, data)`, `API.patch(endpoint, data)`, `API.delete(endpoint)` - Fetch wrappers

### Database Session Pattern

Use this pattern for database operations:

```python
from src.database import get_session_context

async def my_function():
    async with get_session_context() as session:
        result = await session.execute(select(ArtworkImage).where(...))
        images = result.scalars().all()
        # ... do work
        await session.commit()
```

---

*Last updated: December 2025*
