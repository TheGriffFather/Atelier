# CLAUDE.md - Atelier Project Guide

This document provides essential context for AI agents working on Atelier, a Digital Catalogue Raisonné Platform.

## Project Overview

**Atelier** is an open-source platform for building and managing comprehensive catalogue raisonnés - the definitive scholarly record of all known works by an artist. The platform combines automated artwork discovery, professional metadata management, and collaborative research tools.

### Target Audience
- **Estate managers** - Families preserving a deceased artist's legacy
- **Art historians** - Academic researchers doing scholarly documentation
- **Galleries** - Dealers tracking artists they represent
- **Collectors** - People documenting provenance for their holdings
- **Independent researchers** - Anyone doing serious cataloging work

## Technology Stack

### Backend
- **Python 3.11+** with async/await throughout
- **FastAPI** - Web framework with automatic OpenAPI docs
- **SQLAlchemy 2.0** - Async ORM with `Mapped` type hints
- **SQLite** (default) via `aiosqlite` - Supports PostgreSQL via `DATABASE_URL`
- **Pydantic 2.x** - Request/response validation
- **APScheduler** - Periodic task scheduling

### Frontend
- **Jinja2** - Server-side HTML templating
- **Tailwind CSS** - Utility-first styling (build with `npm run css:build`)
- **Vanilla JavaScript** - No framework, just DOM manipulation

### Scraping & Discovery
- **httpx** - Async HTTP client
- **BeautifulSoup4** - HTML parsing
- **Playwright** - Browser automation for JavaScript-heavy sites
- **imagehash** - Perceptual hashing for duplicate detection

## Project Structure

```
Atelier/
├── config/
│   └── settings.py          # Pydantic Settings configuration
├── src/
│   ├── api/
│   │   ├── main.py           # FastAPI app, route registration
│   │   ├── routes/           # API endpoints (artworks.py, images.py, etc.)
│   │   ├── templates/        # Jinja2 HTML templates
│   │   └── static/           # CSS, JS, images
│   ├── database/
│   │   ├── models.py         # SQLAlchemy models and Enums
│   │   └── session.py        # Async session management
│   ├── scrapers/
│   │   ├── base.py           # Abstract BaseScraper class
│   │   ├── orchestrator.py   # Coordinates multiple scrapers
│   │   ├── ebay_api.py       # eBay Browse API integration
│   │   └── *.py              # Platform-specific scrapers
│   ├── services/             # Business logic layer
│   ├── filters/
│   │   └── confidence.py     # Confidence scoring for artist disambiguation
│   ├── notifications/        # Email alerts
│   └── cli.py                # Command-line interface
├── scripts/
│   └── migrations/           # Database migration scripts
├── tests/                    # Pytest test suite
├── data/
│   ├── artworks.db           # SQLite database
│   └── images/               # Downloaded artwork images
├── Tasks/                    # Development task specifications
│   ├── README.md             # Task overview and guidelines
│   ├── SCHEMA.md             # Master schema reference
│   ├── Phase1-Foundation/    # Foundational features
│   ├── Phase2-Professional/  # Core catalog features
│   ├── Phase3-Collaboration/ # Team features
│   └── Phase4-Discovery/     # External integrations
└── CLAUDE.md                 # This file
```

## Common Commands

```bash
# Development server
python -m src.cli server

# Run scrapers once
python -m src.cli scrape

# Run scheduled scraping (hourly)
python -m src.cli scheduler

# Initialize database
python -m src.cli init

# Build Tailwind CSS
npm run css:build
npm run css:watch  # Watch mode

# Run tests
pytest
pytest --cov=src
```

## Database Conventions

### Model Style
```python
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional

class Artwork(Base):
    __tablename__ = "artworks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    images: Mapped[list["ArtworkImage"]] = relationship(back_populates="artwork")
```

### Key Tables (14 total)
| Table | Purpose |
|-------|---------|
| `artworks` | Core artwork records with full metadata |
| `artwork_images` | Multiple images per artwork |
| `artists` | Artist biographical data |
| `exhibitions` | Exhibition records |
| `artwork_exhibitions` | Artwork-Exhibition junction |
| `contacts` | Outreach contacts |
| `outreach` | Communication records |
| `research_leads` | Research lead tracking |
| `saved_searches` | Alert search configurations |
| `alert_results` | Search alert results |
| `notifications` | Notification history |
| `search_filters` | Confidence scoring rules |

### Migrations
Create migration scripts in `scripts/migrations/`:
```python
# scripts/migrations/XXX_feature_name.py
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column exists before adding
    cursor.execute("PRAGMA table_info(table_name)")
    columns = [col[1] for col in cursor.fetchall()]

    if "new_column" not in columns:
        cursor.execute("ALTER TABLE table_name ADD COLUMN new_column TEXT")
        print("Added new_column")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
```

## API Conventions

### Route Organization
Routes are organized in `src/api/routes/` with each file handling a domain:
- `artworks.py` - Artwork CRUD and export
- `images.py` - Image serving and download
- `scraper.py` - Scraper control
- `alerts.py` - Saved searches and results
- `exhibitions.py` - Exhibition management
- `outreach.py` - Contact and outreach tracking
- `gmail.py` - Gmail integration
- `display.py` - Frame display settings

### Endpoint Patterns
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/feature", tags=["feature"])

class FeatureCreate(BaseModel):
    name: str
    description: Optional[str] = None

@router.get("")
async def list_features():
    """List all features."""
    pass

@router.post("")
async def create_feature(data: FeatureCreate):
    """Create a new feature."""
    pass

@router.get("/{id}")
async def get_feature(id: int):
    """Get feature by ID."""
    pass

@router.patch("/{id}")
async def update_feature(id: int, data: dict):
    """Update feature."""
    pass

@router.delete("/{id}")
async def delete_feature(id: int):
    """Delete feature."""
    pass
```

### Response Format
```json
{
  "items": [...],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

## Frontend Conventions

### Template Structure
Templates use Jinja2 with a base template:
```html
{% extends "base.html" %}
{% block title %}Page Title{% endblock %}
{% block content %}
    <!-- Page content -->
{% endblock %}
{% block scripts %}
    <script src="/static/js/page-specific.js"></script>
{% endblock %}
```

### Tailwind Theme
Dark charcoal theme with gold accents:
```css
/* Primary colors */
gray-900: #1a1b1e  /* Background */
gray-800: #25262b  /* Cards */
gold-500: #C5A065  /* Accent */
gold-600: #d4af37  /* Hover */

/* Typography */
font-serif: 'Playfair Display'  /* Headers */
font-sans: 'Inter'              /* Body/UI */
```

### JavaScript Patterns
- Use vanilla JS with async/await
- Fetch API for AJAX calls
- Event delegation for dynamic content
- Template literals for HTML generation

## Development Workflow

### Before Starting a Feature
1. Read the task specification in `Tasks/PhaseX-Category/XX-feature.md`
2. Review `Tasks/SCHEMA.md` for database conventions
3. Check existing code for similar patterns
4. Create migration script if modifying schema

### Implementation Order
1. **Database** - Migration script, update models.py
2. **Service** - Business logic in `src/services/`
3. **API Routes** - Endpoints in `src/api/routes/`
4. **Templates** - UI in `src/api/templates/`
5. **JavaScript** - Client logic in `src/api/static/js/`
6. **Tests** - Unit and integration tests

### After Completing a Feature
- [ ] All success criteria from spec are met
- [ ] Migration works on fresh database
- [ ] API endpoints return correct responses
- [ ] UI matches design specifications
- [ ] Tests pass
- [ ] No regressions in existing features
- [ ] CLAUDE.md updated if needed

## Development Phases

See `Tasks/README.md` for full details. Summary:

### Phase 1: Foundation
- Enhanced Image Management (multiple views, annotations, hashing)
- Import/Migration Tools (CSV, JSON, Excel import)
- Duplicate Detection (perceptual hashing, merge workflow)
- Data Completeness Dashboard (progress tracking)

### Phase 2: Professional
- Provenance Chain Builder (ownership history)
- Exhibition History Module (enhanced exhibitions)
- Literature & Bibliography (citation management)
- Catalog Numbering System (scholarly numbering)

### Phase 3: Collaboration
- Multi-User Support (roles, activity logging)
- Authentication Workflow (expert opinions)
- Print-Ready Export (PDF generation)
- Public Tip Submission (collector outreach)

### Phase 4: Discovery
- Auction House Integrations (Christie's, Sotheby's, etc.)
- Price History Tracking (market intelligence)
- Museum Collection Search (institutional holdings)
- Online Catalog Portal (public-facing site)

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/database/models.py` | All SQLAlchemy models and Enums |
| `src/database/session.py` | `get_db_session()` context manager |
| `src/api/main.py` | FastAPI app, middleware, route registration |
| `config/settings.py` | Environment configuration via Pydantic |
| `src/filters/confidence.py` | Confidence scoring for artist disambiguation |
| `Tasks/SCHEMA.md` | Master schema reference for all phases |

## Environment Variables

```env
# Required
DATABASE_URL=sqlite+aiosqlite:///data/artworks.db
API_HOST=0.0.0.0
API_PORT=8000

# Optional - eBay API
EBAY_CLIENT_ID=your-client-id
EBAY_CLIENT_SECRET=your-client-secret

# Optional - Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_EMAIL=alerts@example.com

# Scraping
SCRAPE_INTERVAL_MINUTES=60
REQUEST_DELAY_SECONDS=2.0
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_artworks.py

# Run with verbose output
pytest -v
```

### Test Structure
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_artwork():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/artworks", json={
            "title": "Test Artwork"
        })
        assert response.status_code == 201
```

## Common Patterns

### Database Session Usage
```python
from src.database.session import get_db_session

async def my_function():
    async with get_db_session() as session:
        result = await session.execute(select(Artwork))
        artworks = result.scalars().all()
```

### Error Handling
```python
from fastapi import HTTPException

if not artwork:
    raise HTTPException(status_code=404, detail="Artwork not found")
```

### Image Handling
Images are stored in `data/images/{artwork_id}/`:
- Original: `{hash}.jpg`
- Thumbnails: `thumbs/{hash}_small.jpg`, `{hash}_medium.jpg`, `{hash}_large.jpg`

### Confidence Scoring
The confidence scorer in `src/filters/confidence.py` uses positive/negative signals to distinguish the target artist from others with similar names. Update patterns when customizing for a new artist.

## Troubleshooting

### Database Issues
```bash
# Reset database
rm data/artworks.db
python -m src.cli init
```

### CSS Not Updating
```bash
npm run css:build
# Or watch mode
npm run css:watch
```

### Playwright Issues
```bash
playwright install chromium
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)

---

*Last updated: December 2025*
