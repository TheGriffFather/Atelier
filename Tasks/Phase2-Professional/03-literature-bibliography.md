# Literature & Bibliography

> Phase 2, Task 3 | Priority: High | Dependencies: None

## Overview

Create a comprehensive bibliography system for tracking publications that reference artworks. Includes books, articles, exhibition catalogs, auction catalogs, and online resources. Allows linking artworks to citations with page/plate numbers, forming the scholarly documentation essential for a catalogue raisonné.

## Success Criteria

- [ ] Track publications with full bibliographic data
- [ ] Link artworks to publications with citation details
- [ ] Support various publication types (book, article, catalog, etc.)
- [ ] Record page numbers, plate numbers, figure numbers
- [ ] Indicate how artwork is cited (illustrated, mentioned, discussed)
- [ ] Generate bibliographic entries in standard formats
- [ ] Search and filter publications
- [ ] Exhibition catalog links to exhibitions
- [ ] Import from BibTeX/RIS

## Database Changes

### New `publications` Table

```sql
CREATE TABLE publications (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    publication_type TEXT NOT NULL,
    authors TEXT,
    editors TEXT,
    publisher TEXT,
    publication_year INTEGER,
    publication_location TEXT,
    isbn TEXT,
    issn TEXT,
    doi TEXT,
    journal_name TEXT,
    volume TEXT,
    issue TEXT,
    pages TEXT,
    exhibition_id INTEGER REFERENCES exhibitions(id),
    notes TEXT,
    url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_publications_type ON publications(publication_type);
CREATE INDEX idx_publications_year ON publications(publication_year);
CREATE INDEX idx_publications_title ON publications(title);
```

### New `artwork_citations` Table

```sql
CREATE TABLE artwork_citations (
    id INTEGER PRIMARY KEY,
    artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    publication_id INTEGER NOT NULL REFERENCES publications(id) ON DELETE CASCADE,
    page_numbers TEXT,
    plate_number TEXT,
    figure_number TEXT,
    catalog_number TEXT,
    citation_type TEXT DEFAULT 'mentioned',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(artwork_id, publication_id)
);

CREATE INDEX idx_citations_artwork ON artwork_citations(artwork_id);
CREATE INDEX idx_citations_publication ON artwork_citations(publication_id);
```

### Enums

```python
class PublicationType(str, Enum):
    BOOK = "book"
    ARTICLE = "article"
    EXHIBITION_CATALOG = "exhibition_catalog"
    AUCTION_CATALOG = "auction_catalog"
    MONOGRAPH = "monograph"
    MAGAZINE = "magazine"
    NEWSPAPER = "newspaper"
    WEBSITE = "website"
    THESIS = "thesis"
    OTHER = "other"

class CitationType(str, Enum):
    ILLUSTRATED = "illustrated"    # Image reproduced
    MENTIONED = "mentioned"        # Text reference only
    DISCUSSED = "discussed"        # Extended discussion
    CATALOGED = "cataloged"        # In catalog listing
    COVER = "cover"                # On publication cover
```

## API Endpoints

### Publications

#### GET /api/publications
List publications.

**Query Parameters:**
- `search`: Search title/authors
- `type`: Publication type filter
- `year_from`, `year_to`: Year range
- `artwork_id`: Filter by cited artwork
- `has_isbn`: Boolean - has ISBN
- `limit`, `offset`: Pagination

**Response:**
```json
{
  "publications": [
    {
      "id": 1,
      "title": "American Trompe l'Oeil: Masters of Deception",
      "publication_type": "book",
      "authors": "John Doe, Jane Smith",
      "publisher": "Yale University Press",
      "publication_year": 1995,
      "isbn": "978-0-123456-78-9",
      "artworks_count": 5,
      "created_at": "2025-12-05T10:00:00"
    }
  ],
  "total": 25
}
```

#### POST /api/publications
Create publication.

**Request:**
```json
{
  "title": "American Trompe l'Oeil: Masters of Deception",
  "publication_type": "book",
  "authors": "John Doe, Jane Smith",
  "editors": null,
  "publisher": "Yale University Press",
  "publication_year": 1995,
  "publication_location": "New Haven",
  "isbn": "978-0-123456-78-9",
  "notes": "Major survey of American trompe l'oeil painting"
}
```

#### GET /api/publications/{id}
Get publication with cited artworks.

**Response:**
```json
{
  "id": 1,
  "title": "American Trompe l'Oeil: Masters of Deception",
  "publication_type": "book",
  "authors": "John Doe, Jane Smith",
  "publisher": "Yale University Press",
  "publication_year": 1995,
  "isbn": "978-0-123456-78-9",
  "cited_artworks": [
    {
      "artwork_id": 42,
      "title": "The Harbor",
      "year_created": 1985,
      "citation": {
        "page_numbers": "156-157",
        "plate_number": "Plate 45",
        "citation_type": "illustrated"
      }
    }
  ],
  "formatted_citation": "Doe, John and Jane Smith. American Trompe l'Oeil: Masters of Deception. New Haven: Yale University Press, 1995."
}
```

#### PATCH /api/publications/{id}
Update publication.

#### DELETE /api/publications/{id}
Delete publication (removes citation links).

### Citations

#### POST /api/publications/{id}/citations
Add artwork citation.

**Request:**
```json
{
  "artwork_id": 42,
  "page_numbers": "156-157",
  "plate_number": "Plate 45",
  "figure_number": null,
  "catalog_number": null,
  "citation_type": "illustrated",
  "notes": "Full-page color reproduction"
}
```

#### PATCH /api/citations/{id}
Update citation.

#### DELETE /api/citations/{id}
Delete citation.

### Artwork Literature

#### GET /api/artworks/{id}/literature
Get literature for an artwork.

**Response:**
```json
{
  "artwork_id": 42,
  "citations": [
    {
      "citation_id": 1,
      "publication": {
        "id": 1,
        "title": "American Trompe l'Oeil",
        "publication_type": "book",
        "authors": "John Doe",
        "publication_year": 1995
      },
      "page_numbers": "156-157",
      "plate_number": "Plate 45",
      "citation_type": "illustrated",
      "formatted": "Doe 1995, pp. 156-157, pl. 45 (illustrated)"
    }
  ],
  "total": 3
}
```

### Export/Format

#### GET /api/publications/{id}/format
Get formatted citation.

**Query Parameters:**
- `style`: chicago, mla, apa (default: chicago)

**Response:**
```json
{
  "chicago": "Doe, John. American Trompe l'Oeil: Masters of Deception. New Haven: Yale University Press, 1995.",
  "mla": "Doe, John. American Trompe l'Oeil: Masters of Deception. Yale University Press, 1995.",
  "apa": "Doe, J. (1995). American Trompe l'Oeil: Masters of Deception. Yale University Press."
}
```

#### GET /api/artworks/{id}/literature/export
Export artwork's literature in formatted style.

**Response:**
```
LITERATURE

Doe, John. American Trompe l'Oeil: Masters of Deception. New Haven: Yale University Press, 1995, pp. 156-157, pl. 45 (illustrated).

Smith, Jane. "Connecticut Painters." Art Magazine 45, no. 2 (Spring 1990): 34-42 (mentioned p. 36).
```

### Import

#### POST /api/publications/import
Import publications from BibTeX or RIS.

**Request (multipart/form-data):**
- `file`: .bib or .ris file

## UI Requirements

### Publications List Page

Location: `/publications` (new page)

**Layout:**

1. **Header**
   - "Literature & Bibliography" title
   - "Add Publication" button
   - "Import BibTeX" button

2. **Filters Bar**
   - Search input
   - Type dropdown
   - Year range
   - Has ISBN checkbox

3. **Publication List**
   - Cards or table view
   - Each shows:
     - Title
     - Authors
     - Year
     - Type badge
     - Artworks cited count
   - Click to view/edit

### Publication Detail Page

Location: `/publications/{id}`

**Layout:**

1. **Header**
   - Publication title
   - Type badge
   - Edit/Delete buttons

2. **Bibliographic Info**
   - Authors/Editors
   - Publisher, Year, Location
   - ISBN/ISSN/DOI
   - URL link
   - Formatted citation (copyable)

3. **Cited Artworks**
   - Grid of artwork thumbnails
   - Each shows citation details
   - "Add Citation" button

### Artwork Detail - Literature Tab

Add to `/artwork/{id}`:

1. **Literature Section**
   - List of citations
   - Each shows:
     - Publication title
     - Author, Year
     - Page/plate numbers
     - Citation type badge
   - "Add Citation" button

### Add/Edit Publication Modal

**Fields:**
- Publication type dropdown (required)
- Title (required)
- Authors
- Editors
- Publisher
- Publication year
- Publication location (city)
- ISBN
- ISSN
- DOI
- URL

**For articles:**
- Journal name
- Volume
- Issue
- Pages

**For exhibition catalogs:**
- Exhibition link (dropdown)

### Add Citation Modal

**Fields:**
- Artwork selector (autocomplete)
- Page numbers
- Plate number
- Figure number
- Catalog number
- Citation type dropdown
- Notes

## Implementation Steps

### Step 1: Database Migration

```python
# scripts/migrations/006_literature.py
"""
Migration: Literature & Bibliography
Date: YYYY-MM-DD
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create publications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS publications (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            publication_type TEXT NOT NULL,
            authors TEXT,
            editors TEXT,
            publisher TEXT,
            publication_year INTEGER,
            publication_location TEXT,
            isbn TEXT,
            issn TEXT,
            doi TEXT,
            journal_name TEXT,
            volume TEXT,
            issue TEXT,
            pages TEXT,
            exhibition_id INTEGER REFERENCES exhibitions(id),
            notes TEXT,
            url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create artwork_citations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artwork_citations (
            id INTEGER PRIMARY KEY,
            artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
            publication_id INTEGER NOT NULL REFERENCES publications(id) ON DELETE CASCADE,
            page_numbers TEXT,
            plate_number TEXT,
            figure_number TEXT,
            catalog_number TEXT,
            citation_type TEXT DEFAULT 'mentioned',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(artwork_id, publication_id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_publications_type ON publications(publication_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_publications_year ON publications(publication_year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_publications_title ON publications(title)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_citations_artwork ON artwork_citations(artwork_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_citations_publication ON artwork_citations(publication_id)")

    conn.commit()
    conn.close()
    print("Migration completed successfully")

if __name__ == "__main__":
    migrate()
```

### Step 2: Update Models

Add to `src/database/models.py`:
- `PublicationType`, `CitationType` enums
- `Publication` model
- `ArtworkCitation` model
- Relationships

### Step 3: Create Literature Service

Create `src/services/literature_service.py`:

```python
class LiteratureService:
    """Manage publications and citations."""

    async def list_publications(
        self,
        search: str = None,
        publication_type: str = None,
        year_from: int = None,
        year_to: int = None,
        artwork_id: int = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """List publications with filters."""
        pass

    async def get_publication(self, publication_id: int) -> dict:
        """Get publication with cited artworks."""
        pass

    async def create_publication(self, data: dict) -> Publication:
        """Create publication."""
        pass

    async def update_publication(self, publication_id: int, data: dict) -> Publication:
        """Update publication."""
        pass

    async def delete_publication(self, publication_id: int) -> None:
        """Delete publication and citations."""
        pass

    async def add_citation(
        self,
        publication_id: int,
        artwork_id: int,
        citation_data: dict
    ) -> ArtworkCitation:
        """Add artwork citation."""
        pass

    async def update_citation(
        self,
        citation_id: int,
        citation_data: dict
    ) -> ArtworkCitation:
        """Update citation."""
        pass

    async def delete_citation(self, citation_id: int) -> None:
        """Delete citation."""
        pass

    async def get_artwork_literature(self, artwork_id: int) -> list:
        """Get literature for artwork."""
        pass

    def format_citation(
        self,
        publication: dict,
        style: str = 'chicago'
    ) -> str:
        """Format publication in citation style."""
        if style == 'chicago':
            return self._format_chicago(publication)
        elif style == 'mla':
            return self._format_mla(publication)
        elif style == 'apa':
            return self._format_apa(publication)
        return ""

    def _format_chicago(self, pub: dict) -> str:
        """Format in Chicago style."""
        parts = []

        if pub.get('authors'):
            parts.append(f"{pub['authors']}.")

        parts.append(f'"{pub["title"]}."' if pub['publication_type'] == 'article' else f"{pub['title']}.")

        if pub.get('journal_name'):
            parts.append(f"{pub['journal_name']}")
            if pub.get('volume'):
                parts.append(f"{pub['volume']}")
            if pub.get('issue'):
                parts.append(f", no. {pub['issue']}")
            if pub.get('publication_year'):
                parts.append(f" ({pub['publication_year']})")
            if pub.get('pages'):
                parts.append(f": {pub['pages']}")
        else:
            if pub.get('publication_location'):
                parts.append(f"{pub['publication_location']}:")
            if pub.get('publisher'):
                parts.append(f" {pub['publisher']},")
            if pub.get('publication_year'):
                parts.append(f" {pub['publication_year']}")

        return " ".join(parts).replace("  ", " ").strip()

    async def import_bibtex(self, file_content: str) -> dict:
        """Import from BibTeX format."""
        pass

    async def import_ris(self, file_content: str) -> dict:
        """Import from RIS format."""
        pass

    def format_literature_entry(self, citation: dict) -> str:
        """Format single artwork citation."""
        pub = citation['publication']
        parts = [self.format_citation(pub, 'chicago')]

        location_parts = []
        if citation.get('page_numbers'):
            location_parts.append(f"pp. {citation['page_numbers']}")
        if citation.get('plate_number'):
            location_parts.append(f"pl. {citation['plate_number']}")
        if citation.get('figure_number'):
            location_parts.append(f"fig. {citation['figure_number']}")

        if location_parts:
            parts.append(", ".join(location_parts))

        if citation.get('citation_type') == 'illustrated':
            parts.append("(illustrated)")
        elif citation.get('citation_type') == 'discussed':
            parts.append("(discussed)")

        return " ".join(parts)
```

### Step 4: Create API Routes

Create `src/api/routes/literature.py`:

```python
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api", tags=["literature"])

class PublicationCreate(BaseModel):
    title: str
    publication_type: str
    authors: Optional[str] = None
    editors: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    publication_location: Optional[str] = None
    isbn: Optional[str] = None
    issn: Optional[str] = None
    doi: Optional[str] = None
    journal_name: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    exhibition_id: Optional[int] = None
    notes: Optional[str] = None
    url: Optional[str] = None

class CitationCreate(BaseModel):
    artwork_id: int
    page_numbers: Optional[str] = None
    plate_number: Optional[str] = None
    figure_number: Optional[str] = None
    catalog_number: Optional[str] = None
    citation_type: str = "mentioned"
    notes: Optional[str] = None

@router.get("/publications")
async def list_publications(
    search: Optional[str] = None,
    type: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    artwork_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0
):
    pass

@router.post("/publications")
async def create_publication(publication: PublicationCreate):
    pass

@router.get("/publications/{id}")
async def get_publication(id: int):
    pass

@router.patch("/publications/{id}")
async def update_publication(id: int, publication: PublicationCreate):
    pass

@router.delete("/publications/{id}")
async def delete_publication(id: int):
    pass

@router.get("/publications/{id}/format")
async def format_publication(id: int, style: str = "chicago"):
    pass

@router.post("/publications/{id}/citations")
async def add_citation(id: int, citation: CitationCreate):
    pass

@router.patch("/citations/{id}")
async def update_citation(id: int, citation: CitationCreate):
    pass

@router.delete("/citations/{id}")
async def delete_citation(id: int):
    pass

@router.post("/publications/import")
async def import_publications(file: UploadFile = File(...)):
    pass
```

Add to artworks routes:
```python
@router.get("/{id}/literature")
async def get_artwork_literature(id: int):
    pass

@router.get("/{id}/literature/export")
async def export_artwork_literature(id: int, style: str = "chicago"):
    pass
```

### Step 5: Create Templates

Create `src/api/templates/publications.html`:
- List page

Create `src/api/templates/publication.html`:
- Detail page

Update `src/api/templates/artwork.html`:
- Add Literature tab

### Step 6: Add JavaScript

Create `src/api/static/js/literature.js`:
- List filtering
- Modal handling
- Citation formatting preview
- BibTeX import

## Testing Requirements

### Unit Tests

```python
# tests/test_literature_service.py

def test_create_publication():
    """Creates publication with all fields."""

def test_add_citation():
    """Links artwork to publication."""

def test_format_chicago():
    """Chicago format is correct."""

def test_format_mla():
    """MLA format is correct."""

def test_format_apa():
    """APA format is correct."""

def test_format_literature_entry():
    """Full entry with citation details."""

def test_import_bibtex():
    """Parses BibTeX correctly."""
```

### Integration Tests

```python
# tests/test_literature_api.py

def test_list_publications():
    """GET returns list."""

def test_filter_by_type():
    """Type filter works."""

def test_create_publication():
    """POST creates publication."""

def test_add_citation():
    """POST adds citation."""

def test_get_artwork_literature():
    """Returns literature for artwork."""

def test_format_endpoint():
    """Returns formatted citation."""
```

### Manual Testing Checklist

- [ ] View publications list
- [ ] Filter by type
- [ ] Search publications
- [ ] Create book publication
- [ ] Create article publication
- [ ] Create exhibition catalog (linked)
- [ ] View publication detail
- [ ] Add artwork citation
- [ ] Edit citation details
- [ ] Remove citation
- [ ] View literature on artwork page
- [ ] Export artwork literature
- [ ] Import BibTeX file
- [ ] Copy formatted citation

## Edge Cases

1. **No Literature**: Show "No literature recorded"
2. **Multiple Citations Same Publication**: Prevent duplicates
3. **Delete Publication**: Cascade delete citations
4. **Long Titles**: Truncate in list
5. **Missing Year**: Handle in formatting
6. **Invalid BibTeX**: Clear error message
7. **Exhibition Catalog Link**: Validate exhibition exists
8. **Special Characters**: Handle quotes in titles

## Citation Formatting Examples

### Chicago Style

**Book:**
```
Doe, John. American Trompe l'Oeil: Masters of Deception. New Haven: Yale University Press, 1995.
```

**Article:**
```
Smith, Jane. "Connecticut Painters." Art Magazine 45, no. 2 (1990): 34-42.
```

**Exhibition Catalog:**
```
Brown, Dan. Dan Brown: Recent Paintings. Exh. cat. Madison: Susan Powell Fine Art, 1985.
```

### Full Literature Entry

```
Doe 1995
Doe, John. American Trompe l'Oeil. Yale University Press, 1995, pp. 156-157, pl. 45 (illustrated).
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/006_literature.py` | Create | Database migration |
| `src/database/models.py` | Modify | Add enums and models |
| `src/services/literature_service.py` | Create | Business logic |
| `src/api/routes/literature.py` | Create | API endpoints |
| `src/api/routes/artworks.py` | Modify | Add literature endpoint |
| `src/api/main.py` | Modify | Register routes |
| `src/api/templates/publications.html` | Create | List page |
| `src/api/templates/publication.html` | Create | Detail page |
| `src/api/templates/artwork.html` | Modify | Add Literature tab |
| `src/api/static/js/literature.js` | Create | Client logic |
| `tests/test_literature_service.py` | Create | Unit tests |
| `tests/test_literature_api.py` | Create | API tests |

---

*Last updated: December 5, 2025*
