# Online Catalog Portal

> Phase 4, Task 4 | Priority: Low | Dependencies: Phase 2 Complete (Professional features)

## Overview

Create a public-facing website for the catalogue raisonné, allowing scholars, collectors, and the public to browse authenticated artworks. Includes search, filtering, and detailed artwork entries while protecting sensitive data.

## Success Criteria

- [ ] Public website with artwork gallery
- [ ] Search and filter capabilities
- [ ] Detailed artwork entries (scholarly format)
- [ ] Responsive design (mobile-friendly)
- [ ] SEO optimized
- [ ] Protected admin data (no prices, contact info)
- [ ] Optional password protection for full catalog
- [ ] Submission form integration
- [ ] Professional design reflecting artist's work

## Public vs Private Data

### Public Data (Visible to All)

- Title
- Catalog number
- Year created
- Medium
- Dimensions
- Signature/inscription
- Primary image
- Provenance (public version)
- Exhibition history
- Literature citations
- Authentication status

### Private Data (Admin Only)

- Current owner details
- Purchase prices
- Contact information
- Internal notes
- Acquisition status
- Source platform details
- Confidence scores

## Database Changes

### Modify `artworks` Table

Add columns for public visibility:

```sql
ALTER TABLE artworks ADD COLUMN is_public INTEGER DEFAULT 0;
ALTER TABLE artworks ADD COLUMN public_provenance TEXT;
ALTER TABLE artworks ADD COLUMN public_notes TEXT;
```

### New `portal_settings` Table

```sql
CREATE TABLE portal_settings (
    id INTEGER PRIMARY KEY,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Seed settings
INSERT INTO portal_settings (setting_key, setting_value) VALUES
('site_title', 'Dan Brown: A Catalogue Raisonné'),
('site_subtitle', 'The Complete Paintings'),
('about_text', ''),
('contact_email', ''),
('require_password', 'false'),
('password_hash', ''),
('google_analytics_id', ''),
('meta_description', ''),
('hero_image_path', '');
```

## API Endpoints

### Public Endpoints (No Auth)

#### GET /api/public/artworks
Get public artworks.

**Query Parameters:**
- `search`: Search title
- `year_from`, `year_to`: Year range
- `medium`: Filter by medium
- `category`: Filter by category
- `catalog_number`: Filter by number
- `sort`: title, year, catalog_number
- `limit`, `offset`: Pagination

**Response:**
```json
{
  "artworks": [
    {
      "id": 42,
      "catalog_number": "DB-0042",
      "title": "The Harbor",
      "year_created": 1985,
      "year_display": "1985",
      "medium": "Oil on canvas",
      "dimensions": "24 × 36 inches",
      "thumbnail_url": "/public/images/42_thumb.jpg",
      "authentication_status": "authenticated"
    }
  ],
  "total": 85,
  "filters": {
    "categories": ["Currency", "Still Life", "Coastal"],
    "mediums": ["Oil on canvas", "Oil on panel"],
    "year_range": [1970, 2020]
  }
}
```

#### GET /api/public/artworks/{id}
Get public artwork details.

**Response:**
```json
{
  "id": 42,
  "catalog_number": "DB-0042",
  "title": "The Harbor",
  "year_created": 1985,
  "year_display": "1985",
  "medium": "Oil on canvas",
  "dimensions": "24 × 36 inches (60.9 × 91.4 cm)",
  "signed": "Signed lower right: \"D. Brown\"",
  "description": "A view of the harbor at sunset...",
  "images": [
    {
      "url": "/public/images/42.jpg",
      "caption": "Front view",
      "is_primary": true
    }
  ],
  "provenance": "The artist; Susan Powell Fine Art, Madison, CT; Private collection.",
  "exhibitions": [
    {
      "year": 1985,
      "venue": "Susan Powell Fine Art, Madison, CT",
      "title": "Dan Brown: Recent Paintings",
      "catalog_number": "12"
    }
  ],
  "literature": [
    {
      "citation": "Doe 1995, pp. 156-157, pl. 45 (illustrated)"
    }
  ],
  "authentication_status": "authenticated",
  "notes": null
}
```

#### GET /api/public/stats
Get catalog statistics.

**Response:**
```json
{
  "total_artworks": 85,
  "authenticated": 80,
  "by_category": {
    "Currency": 25,
    "Still Life": 20,
    "Coastal": 15
  },
  "year_range": {
    "earliest": 1970,
    "latest": 2020
  }
}
```

#### GET /api/public/about
Get about/artist info.

#### GET /api/public/settings
Get portal settings.

### Portal Access (Optional Password)

#### POST /api/public/verify-password
Verify portal password.

**Request:**
```json
{
  "password": "catalog2025"
}
```

**Response:**
```json
{
  "valid": true,
  "token": "...",
  "expires_at": "..."
}
```

### Admin Endpoints

#### GET /api/portal/settings
Get all portal settings.

#### PATCH /api/portal/settings
Update portal settings.

**Request:**
```json
{
  "site_title": "Dan Brown: A Catalogue Raisonné",
  "require_password": true,
  "password": "newpassword"
}
```

#### POST /api/artworks/{id}/publish
Publish artwork to public portal.

#### POST /api/artworks/{id}/unpublish
Remove from public portal.

#### POST /api/artworks/bulk-publish
Bulk publish artworks.

## Portal Design

### Homepage

**Layout:**

1. **Hero Section**
   - Large hero image
   - Title and subtitle
   - Brief intro text
   - "Browse Catalog" button

2. **Statistics Bar**
   - Total artworks
   - Categories
   - Date range

3. **Featured Artworks**
   - Grid of 6-8 highlighted works
   - "View All" link

4. **About Section**
   - Artist biography excerpt
   - Photo
   - "Learn More" link

5. **Footer**
   - Contact info
   - Copyright
   - Admin link

### Gallery Page

**Layout:**

1. **Filter Sidebar**
   - Search input
   - Category checkboxes
   - Year range slider
   - Medium dropdown
   - Clear filters

2. **Results Grid**
   - Image cards
   - Title, Year, Catalog #
   - Hover effect

3. **Pagination**
   - Page numbers
   - Items per page

### Artwork Detail Page

**Layout:**

1. **Breadcrumb**
   - Home > Gallery > Title

2. **Main Image**
   - Large primary image
   - Lightbox on click
   - Additional images gallery

3. **Info Panel**
   - Catalog number
   - Title
   - Year
   - Medium
   - Dimensions
   - Signature

4. **Scholarly Sections**
   - Provenance
   - Exhibition History
   - Literature

5. **Authentication Badge**
   - Status indicator

6. **Navigation**
   - Previous/Next artwork

### About Page

- Artist biography
- Timeline
- Photo gallery

### Contact Page

- Contact form (links to tip submission)
- Email
- Info about submitting works

## Implementation Steps

### Step 1: Database Migration

```python
# scripts/migrations/014_public_portal.py
"""
Migration: Online Catalog Portal
Date: YYYY-MM-DD
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add columns to artworks
    cursor.execute("PRAGMA table_info(artworks)")
    existing = [col[1] for col in cursor.fetchall()]

    if 'is_public' not in existing:
        cursor.execute("ALTER TABLE artworks ADD COLUMN is_public INTEGER DEFAULT 0")
    if 'public_provenance' not in existing:
        cursor.execute("ALTER TABLE artworks ADD COLUMN public_provenance TEXT")
    if 'public_notes' not in existing:
        cursor.execute("ALTER TABLE artworks ADD COLUMN public_notes TEXT")

    # Create portal_settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portal_settings (
            id INTEGER PRIMARY KEY,
            setting_key TEXT NOT NULL UNIQUE,
            setting_value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed settings
    settings = [
        ('site_title', 'Artist Catalogue Raisonné'),
        ('site_subtitle', 'The Complete Works'),
        ('about_text', ''),
        ('contact_email', ''),
        ('require_password', 'false'),
        ('password_hash', ''),
        ('google_analytics_id', ''),
        ('meta_description', ''),
        ('hero_image_path', ''),
    ]

    for key, value in settings:
        cursor.execute("""
            INSERT OR IGNORE INTO portal_settings (setting_key, setting_value)
            VALUES (?, ?)
        """, (key, value))

    conn.commit()
    conn.close()
    print("Migration completed successfully")

if __name__ == "__main__":
    migrate()
```

### Step 2: Create Portal Service

```python
# src/services/portal_service.py

class PortalService:
    """Manage public catalog portal."""

    async def get_settings(self) -> dict:
        """Get all portal settings."""
        pass

    async def update_settings(self, settings: dict) -> None:
        """Update portal settings."""
        pass

    async def get_public_artworks(
        self,
        search: str = None,
        year_from: int = None,
        year_to: int = None,
        medium: str = None,
        category: str = None,
        sort: str = 'catalog_number',
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """Get public artworks with filters."""
        pass

    async def get_public_artwork(self, artwork_id: int) -> dict:
        """Get single artwork for public view."""
        pass

    async def publish_artwork(self, artwork_id: int) -> None:
        """Make artwork public."""
        pass

    async def unpublish_artwork(self, artwork_id: int) -> None:
        """Remove artwork from public."""
        pass

    async def verify_portal_password(self, password: str) -> bool:
        """Verify portal access password."""
        pass

    def sanitize_for_public(self, artwork: dict) -> dict:
        """Remove private data from artwork."""
        private_fields = [
            'source_url', 'source_platform', 'confidence_score',
            'acquisition_status', 'last_sale_price', 'current_owner',
            'contact_info', 'internal_notes'
        ]
        return {k: v for k, v in artwork.items() if k not in private_fields}
```

### Step 3: Create Public Routes

```python
# src/api/routes/public.py

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/public", tags=["public"])

@router.get("/artworks")
async def get_public_artworks(
    search: str = None,
    year_from: int = None,
    year_to: int = None,
    medium: str = None,
    category: str = None,
    sort: str = 'catalog_number',
    limit: int = 50,
    offset: int = 0
):
    pass

@router.get("/artworks/{id}")
async def get_public_artwork(id: int):
    pass

@router.get("/stats")
async def get_public_stats():
    pass

@router.get("/about")
async def get_about():
    pass

@router.get("/settings")
async def get_public_settings():
    pass

@router.post("/verify-password")
async def verify_password(password: str):
    pass
```

### Step 4: Create Public Templates

Create separate template folder:
- `src/api/templates/public/index.html`
- `src/api/templates/public/gallery.html`
- `src/api/templates/public/artwork.html`
- `src/api/templates/public/about.html`
- `src/api/templates/public/contact.html`
- `src/api/templates/public/base.html`

### Step 5: Add Public Routes to FastAPI

```python
# Public routes (no authentication)
@app.get("/")
async def public_home():
    return templates.TemplateResponse("public/index.html", {...})

@app.get("/gallery")
async def public_gallery():
    pass

@app.get("/catalog/{id}")
async def public_artwork(id: int):
    pass

@app.get("/about")
async def public_about():
    pass
```

### Step 6: Admin Portal Settings UI

Create settings page for managing portal.

## SEO Considerations

### Meta Tags

```html
<title>{{ artwork.title }} | Dan Brown Catalogue Raisonné</title>
<meta name="description" content="{{ artwork.description[:160] }}">
<meta property="og:title" content="{{ artwork.title }}">
<meta property="og:image" content="{{ artwork.primary_image_url }}">
<meta property="og:type" content="article">
```

### Structured Data

```json
{
  "@context": "https://schema.org",
  "@type": "VisualArtwork",
  "name": "{{ artwork.title }}",
  "creator": {
    "@type": "Person",
    "name": "Dan Brown"
  },
  "dateCreated": "{{ artwork.year_created }}",
  "artMedium": "{{ artwork.medium }}",
  "image": "{{ artwork.primary_image_url }}"
}
```

### Sitemap

Generate sitemap.xml with all public artwork URLs.

## Testing Requirements

### Unit Tests

```python
def test_sanitize_removes_private():
    """Private data removed from public view."""

def test_public_artwork_requires_public():
    """Non-public artwork returns 404."""

def test_password_verification():
    """Password verification works."""
```

### Manual Testing Checklist

- [ ] View public homepage
- [ ] Browse gallery
- [ ] Filter by category
- [ ] Search artworks
- [ ] View artwork detail
- [ ] Test responsive design
- [ ] Test password protection
- [ ] Verify private data hidden
- [ ] Admin publish/unpublish
- [ ] Update portal settings

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/014_public_portal.py` | Create | Migration |
| `src/database/models.py` | Modify | Add columns |
| `src/services/portal_service.py` | Create | Business logic |
| `src/api/routes/public.py` | Create | Public API |
| `src/api/routes/portal.py` | Create | Admin portal API |
| `src/api/templates/public/*.html` | Create | Public templates |
| `src/api/static/css/public.css` | Create | Public styles |
| `src/api/static/js/public.js` | Create | Public JS |

---

*Last updated: December 5, 2025*
