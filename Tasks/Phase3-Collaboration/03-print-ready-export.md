# Print-Ready Export

> Phase 3, Task 3 | Priority: Medium | Dependencies: None

## Overview

Create comprehensive export functionality for generating publication-quality catalogue raisonné documents. Supports multiple formats (PDF, Word, HTML) with customizable templates, scholarly formatting, and print-ready output suitable for academic publication.

## Success Criteria

- [ ] Export individual artwork entries with full metadata
- [ ] Export complete catalogue with all artworks
- [ ] Multiple format support: PDF, DOCX, HTML
- [ ] Customizable entry templates
- [ ] High-resolution image export
- [ ] Scholarly formatting (bibliography, citations)
- [ ] Print-ready specifications (bleed, margins, resolution)
- [ ] Batch export capabilities
- [ ] Customizable cover page and introduction
- [ ] Table of contents generation

## Export Templates

### Entry Template Structure

Each artwork entry includes:

1. **Header**: Catalog number, Title
2. **Image**: Primary image with caption
3. **Basic Info**: Year, Medium, Dimensions
4. **Signature/Inscription**: Signature details
5. **Provenance**: Ownership history
6. **Exhibition History**: Chronological list
7. **Literature**: Bibliography citations
8. **Notes**: Additional scholarly notes

### Template Example (Markdown/HTML)

```html
<article class="catalog-entry">
  <header>
    <span class="catalog-number">DB-0042</span>
    <h2 class="title">The Harbor</h2>
  </header>

  <figure class="primary-image">
    <img src="images/42.jpg" alt="The Harbor">
    <figcaption>Oil on canvas, 24 × 36 inches. Private collection.</figcaption>
  </figure>

  <dl class="metadata">
    <dt>Date</dt><dd>1985</dd>
    <dt>Medium</dt><dd>Oil on canvas</dd>
    <dt>Dimensions</dt><dd>24 × 36 inches (60.9 × 91.4 cm)</dd>
    <dt>Signed</dt><dd>Lower right: "D. Brown"</dd>
  </dl>

  <section class="provenance">
    <h3>Provenance</h3>
    <p>The artist, Connecticut (until 1985); Susan Powell Fine Art, Madison, CT (1985-1986); Private collection, New York (1986-present).</p>
  </section>

  <section class="exhibitions">
    <h3>Exhibitions</h3>
    <ul>
      <li>1985. Susan Powell Fine Art, Madison, CT. <em>Dan Brown: Recent Paintings</em>, cat. no. 12.</li>
      <li>1990. New Britain Museum of American Art, New Britain, CT. <em>Connecticut Realists</em>.</li>
    </ul>
  </section>

  <section class="literature">
    <h3>Literature</h3>
    <ul>
      <li>Doe 1995, pp. 156-157, pl. 45 (illustrated).</li>
    </ul>
  </section>
</article>
```

## API Endpoints

### Single Artwork Export

#### GET /api/artworks/{id}/export
Export single artwork entry.

**Query Parameters:**
- `format`: pdf, docx, html, json (default: pdf)
- `template`: entry_standard, entry_brief, entry_full (default: entry_standard)
- `include_images`: true/false (default: true)
- `image_quality`: web (72dpi), print (300dpi)

**Response:** File download

### Batch Export

#### POST /api/export/batch
Export multiple artworks.

**Request:**
```json
{
  "artwork_ids": [1, 2, 3, 4, 5],
  "format": "pdf",
  "template": "entry_standard",
  "include_images": true,
  "image_quality": "print",
  "one_per_page": true
}
```

**Response:** File download (combined PDF or ZIP)

### Full Catalogue Export

#### POST /api/export/catalogue
Export complete catalogue.

**Request:**
```json
{
  "format": "pdf",
  "include_cover": true,
  "cover_title": "Dan Brown: A Catalogue Raisonné",
  "cover_subtitle": "The Complete Paintings",
  "include_introduction": true,
  "introduction_text": "...",
  "include_toc": true,
  "include_index": true,
  "sort_by": "catalog_number",
  "filter": {
    "art_type": "Painting",
    "authentication_status": "authenticated"
  },
  "image_quality": "print",
  "page_size": "letter",
  "margins": {
    "top": 1,
    "bottom": 1,
    "left": 1.25,
    "right": 1
  }
}
```

**Response:** File download

### Export Templates

#### GET /api/export/templates
List available templates.

**Response:**
```json
{
  "templates": [
    {
      "id": "entry_standard",
      "name": "Standard Entry",
      "description": "Full scholarly entry with all sections",
      "format_support": ["pdf", "docx", "html"]
    },
    {
      "id": "entry_brief",
      "name": "Brief Entry",
      "description": "Condensed entry for checklist format",
      "format_support": ["pdf", "docx", "html"]
    },
    {
      "id": "checklist",
      "name": "Exhibition Checklist",
      "description": "Simple list format for exhibitions",
      "format_support": ["pdf", "docx"]
    }
  ]
}
```

#### POST /api/export/templates
Create custom template (admin).

**Request:**
```json
{
  "id": "custom_entry",
  "name": "Custom Entry Format",
  "description": "Our house style",
  "html_template": "...",
  "css_styles": "..."
}
```

### Export Preview

#### POST /api/export/preview
Preview export without downloading.

**Request:**
```json
{
  "artwork_ids": [42],
  "template": "entry_standard"
}
```

**Response:**
```json
{
  "preview_html": "<article class='catalog-entry'>..."
}
```

### Export Jobs (for large exports)

#### POST /api/export/jobs
Start large export job.

**Request:** Same as catalogue export

**Response:**
```json
{
  "job_id": "abc123",
  "status": "processing",
  "estimated_time": 120
}
```

#### GET /api/export/jobs/{id}
Check export job status.

**Response:**
```json
{
  "job_id": "abc123",
  "status": "completed",
  "download_url": "/api/export/jobs/abc123/download",
  "expires_at": "2025-12-06T10:00:00"
}
```

#### GET /api/export/jobs/{id}/download
Download completed export.

## UI Requirements

### Export Page

Location: `/export` (new page)

**Layout:**

1. **Export Type Selection**
   - Single artwork (dropdown selector)
   - Selected artworks (from gallery selection)
   - Full catalogue
   - Custom filter

2. **Format Options**
   - PDF (recommended for print)
   - Word Document (for editing)
   - HTML (for web)

3. **Template Selection**
   - Visual preview of each template
   - Radio buttons

4. **Image Options**
   - Include images checkbox
   - Quality: Web (72dpi) / Print (300dpi)
   - Size limits

5. **Page Options** (PDF only)
   - Page size: Letter, A4, Custom
   - Orientation: Portrait, Landscape
   - Margins
   - Include page numbers

6. **Catalogue Options** (full catalogue)
   - Include cover page
   - Cover title/subtitle
   - Include table of contents
   - Include introduction
   - Include index
   - Sort order

7. **Preview Panel**
   - Live preview of first entry
   - Refresh button

8. **Export Button**
   - Shows progress for large exports
   - Downloads when complete

### Gallery Integration

On `/` (gallery view):
- Multi-select artworks
- "Export Selected" button in toolbar
- Opens export page with selection

### Artwork Detail Integration

On `/artwork/{id}`:
- "Export" button
- Dropdown with format options
- Quick export to PDF

## Implementation Steps

### Step 1: Create Export Service

Create `src/services/export_service.py`:

```python
from typing import Optional
from pathlib import Path
import json

class ExportService:
    """Handle catalogue exports."""

    TEMPLATES_DIR = Path("src/api/templates/export")

    async def export_artwork(
        self,
        artwork_id: int,
        format: str = 'pdf',
        template: str = 'entry_standard',
        include_images: bool = True,
        image_quality: str = 'web'
    ) -> bytes:
        """Export single artwork."""
        artwork = await self._get_artwork_data(artwork_id)
        html = self._render_template(template, artwork)

        if format == 'html':
            return html.encode()
        elif format == 'pdf':
            return self._html_to_pdf(html)
        elif format == 'docx':
            return self._html_to_docx(html)

        raise ValueError(f"Unsupported format: {format}")

    async def export_batch(
        self,
        artwork_ids: list[int],
        format: str = 'pdf',
        template: str = 'entry_standard',
        **options
    ) -> bytes:
        """Export multiple artworks."""
        pass

    async def export_catalogue(
        self,
        options: dict
    ) -> bytes:
        """Export complete catalogue."""
        pass

    async def _get_artwork_data(self, artwork_id: int) -> dict:
        """Get all artwork data for export."""
        # Include: basic info, images, provenance, exhibitions, literature
        pass

    def _render_template(
        self,
        template_name: str,
        artwork: dict
    ) -> str:
        """Render artwork to HTML."""
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader(self.TEMPLATES_DIR))
        template = env.get_template(f"{template_name}.html")
        return template.render(artwork=artwork)

    def _html_to_pdf(self, html: str) -> bytes:
        """Convert HTML to PDF."""
        from weasyprint import HTML, CSS
        return HTML(string=html).write_pdf()

    def _html_to_docx(self, html: str) -> bytes:
        """Convert HTML to DOCX."""
        from htmldocx import HtmlToDocx
        pass

    def _prepare_images(
        self,
        artwork: dict,
        quality: str
    ) -> dict:
        """Prepare images for export."""
        pass

    def _generate_toc(self, artworks: list) -> str:
        """Generate table of contents."""
        pass

    def _generate_index(self, artworks: list) -> str:
        """Generate alphabetical index."""
        pass

    def format_provenance(self, entries: list) -> str:
        """Format provenance chain as text."""
        pass

    def format_exhibitions(self, exhibitions: list) -> str:
        """Format exhibition history."""
        pass

    def format_literature(self, citations: list) -> str:
        """Format bibliography."""
        pass
```

### Step 2: Create Export Templates

Create `src/api/templates/export/entry_standard.html`:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    {% include 'export_styles.css' %}
  </style>
</head>
<body>
  <article class="catalog-entry">
    <header>
      {% if artwork.catalog_number %}
      <span class="catalog-number">{{ artwork.catalog_number }}</span>
      {% endif %}
      <h2 class="title">{{ artwork.title }}</h2>
    </header>

    {% if artwork.primary_image and include_images %}
    <figure class="primary-image">
      <img src="{{ artwork.primary_image.path }}" alt="{{ artwork.title }}">
      <figcaption>
        {{ artwork.medium }}{% if artwork.dimensions %}, {{ artwork.dimensions }}{% endif %}.
        {% if artwork.current_location %}{{ artwork.current_location }}.{% endif %}
      </figcaption>
    </figure>
    {% endif %}

    <dl class="metadata">
      <dt>Date</dt>
      <dd>{{ artwork.year_display }}</dd>

      <dt>Medium</dt>
      <dd>{{ artwork.medium or 'Unknown' }}</dd>

      <dt>Dimensions</dt>
      <dd>{{ artwork.dimensions or 'Unknown' }}{% if artwork.dimensions_cm %} ({{ artwork.dimensions_cm }}){% endif %}</dd>

      {% if artwork.signed %}
      <dt>Signed</dt>
      <dd>{{ artwork.signed }}</dd>
      {% endif %}

      {% if artwork.inscription %}
      <dt>Inscription</dt>
      <dd>{{ artwork.inscription }}</dd>
      {% endif %}
    </dl>

    {% if artwork.provenance_text %}
    <section class="provenance">
      <h3>Provenance</h3>
      <p>{{ artwork.provenance_text }}</p>
    </section>
    {% endif %}

    {% if artwork.exhibitions %}
    <section class="exhibitions">
      <h3>Exhibitions</h3>
      <ul>
        {% for ex in artwork.exhibitions %}
        <li>{{ ex.year }}. {{ ex.venue_name }}{% if ex.venue_city %}, {{ ex.venue_city }}{% endif %}. <em>{{ ex.exhibition_name or 'Exhibition' }}</em>{% if ex.catalog_number %}, cat. no. {{ ex.catalog_number }}{% endif %}.</li>
        {% endfor %}
      </ul>
    </section>
    {% endif %}

    {% if artwork.citations %}
    <section class="literature">
      <h3>Literature</h3>
      <ul>
        {% for citation in artwork.citations %}
        <li>{{ citation.formatted }}</li>
        {% endfor %}
      </ul>
    </section>
    {% endif %}

    {% if artwork.notes %}
    <section class="notes">
      <h3>Notes</h3>
      <p>{{ artwork.notes }}</p>
    </section>
    {% endif %}
  </article>
</body>
</html>
```

Create `src/api/templates/export/export_styles.css`:

```css
@page {
  size: letter;
  margin: 1in;
}

body {
  font-family: 'Times New Roman', serif;
  font-size: 11pt;
  line-height: 1.5;
  color: #000;
}

.catalog-entry {
  page-break-after: always;
}

.catalog-number {
  font-weight: bold;
  font-size: 14pt;
}

.title {
  font-size: 18pt;
  font-style: italic;
  margin: 0.25em 0;
}

.primary-image {
  max-width: 100%;
  margin: 1em 0;
}

.primary-image img {
  max-width: 100%;
  max-height: 6in;
}

figcaption {
  font-size: 10pt;
  font-style: italic;
  margin-top: 0.5em;
}

.metadata {
  margin: 1em 0;
}

.metadata dt {
  font-weight: bold;
  float: left;
  width: 100px;
}

.metadata dd {
  margin-left: 110px;
  margin-bottom: 0.25em;
}

section h3 {
  font-size: 12pt;
  margin-top: 1em;
  margin-bottom: 0.5em;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.provenance p,
.notes p {
  text-align: justify;
}

.exhibitions ul,
.literature ul {
  list-style: none;
  padding: 0;
}

.exhibitions li,
.literature li {
  margin-bottom: 0.5em;
  text-indent: -1em;
  padding-left: 1em;
}
```

### Step 3: Create API Routes

Create `src/api/routes/export.py`:

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import io

router = APIRouter(prefix="/api/export", tags=["export"])

class BatchExportRequest(BaseModel):
    artwork_ids: list[int]
    format: str = "pdf"
    template: str = "entry_standard"
    include_images: bool = True
    image_quality: str = "web"
    one_per_page: bool = True

class CatalogueExportRequest(BaseModel):
    format: str = "pdf"
    include_cover: bool = True
    cover_title: Optional[str] = None
    cover_subtitle: Optional[str] = None
    include_introduction: bool = False
    introduction_text: Optional[str] = None
    include_toc: bool = True
    include_index: bool = False
    sort_by: str = "catalog_number"
    filter: Optional[dict] = None
    image_quality: str = "print"
    page_size: str = "letter"
    margins: Optional[dict] = None

@router.get("/templates")
async def list_templates():
    pass

@router.post("/templates")
async def create_template(template_data: dict, user = Depends(require_admin)):
    pass

@router.post("/preview")
async def preview_export(artwork_ids: list[int], template: str = "entry_standard"):
    pass

@router.post("/batch")
async def batch_export(request: BatchExportRequest):
    pass

@router.post("/catalogue")
async def catalogue_export(request: CatalogueExportRequest, background_tasks: BackgroundTasks):
    pass

@router.post("/jobs")
async def start_export_job(request: CatalogueExportRequest):
    pass

@router.get("/jobs/{id}")
async def get_job_status(id: str):
    pass

@router.get("/jobs/{id}/download")
async def download_job(id: str):
    pass
```

Add to artworks routes:
```python
@router.get("/{id}/export")
async def export_artwork(
    id: int,
    format: str = "pdf",
    template: str = "entry_standard",
    include_images: bool = True,
    image_quality: str = "web"
):
    pass
```

### Step 4: Create Export Page

Create `src/api/templates/export-page.html`:
- Export type selection
- Format options
- Template preview
- Options forms
- Progress indicator

### Step 5: Add JavaScript

Create `src/api/static/js/export.js`:
- Form handling
- Preview loading
- Download triggering
- Job status polling

## Testing Requirements

### Unit Tests

```python
# tests/test_export_service.py

def test_export_artwork_pdf():
    """PDF export works."""

def test_export_artwork_html():
    """HTML export works."""

def test_format_provenance():
    """Provenance formats correctly."""

def test_format_exhibitions():
    """Exhibitions format correctly."""

def test_format_literature():
    """Literature formats correctly."""

def test_render_template():
    """Template renders with data."""
```

### Integration Tests

```python
# tests/test_export_api.py

def test_single_export():
    """Single artwork exports."""

def test_batch_export():
    """Batch export works."""

def test_preview():
    """Preview returns HTML."""

def test_catalogue_export():
    """Full catalogue exports."""
```

### Manual Testing Checklist

- [ ] Export single artwork as PDF
- [ ] Export single artwork as DOCX
- [ ] Export single artwork as HTML
- [ ] Batch export multiple artworks
- [ ] Export full catalogue
- [ ] Include cover page
- [ ] Include table of contents
- [ ] Preview before export
- [ ] Print exported PDF

## Dependencies

- `weasyprint` - HTML to PDF conversion
- `python-docx` or `htmldocx` - DOCX generation
- `Jinja2` - Template rendering (already in FastAPI)

```bash
pip install weasyprint python-docx
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/services/export_service.py` | Create | Export logic |
| `src/api/routes/export.py` | Create | API endpoints |
| `src/api/routes/artworks.py` | Modify | Add export endpoint |
| `src/api/main.py` | Modify | Register routes |
| `src/api/templates/export/entry_standard.html` | Create | Standard template |
| `src/api/templates/export/entry_brief.html` | Create | Brief template |
| `src/api/templates/export/checklist.html` | Create | Checklist template |
| `src/api/templates/export/catalogue_cover.html` | Create | Cover page |
| `src/api/templates/export/export_styles.css` | Create | Print styles |
| `src/api/templates/export-page.html` | Create | Export UI |
| `src/api/static/js/export.js` | Create | Client logic |
| `tests/test_export_service.py` | Create | Unit tests |
| `tests/test_export_api.py` | Create | API tests |

---

*Last updated: December 5, 2025*
