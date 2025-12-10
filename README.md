# Atelier

**A Digital Catalogue Raisonné Platform**

Atelier is an open-source platform for building and managing a comprehensive catalogue raisonné - a scholarly catalog of all known works by an artist. Built for art historians, estate managers, galleries, collectors, and families preserving an artist's legacy.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)
![Status](https://img.shields.io/badge/status-work%20in%20progress-orange.svg)

> **Note:** This project is under active development. Core functionality is working, but many planned features are still being implemented. See the [Roadmap](#roadmap) section for details on upcoming enhancements.

**[View Application Walkthrough](docs/WALKTHROUGH.md)** | **[Changelog](CHANGELOG.md)**

---

## What is a Catalogue Raisonné?

A **catalogue raisonné** (French for "reasoned catalog") is the definitive scholarly record of all known works by an artist. It serves as the authoritative reference for:

- **Authentication** - Establishing which works are genuine
- **Provenance** - Tracking ownership history
- **Documentation** - Recording physical characteristics, exhibitions, literature
- **Discovery** - Finding previously unknown works

Atelier digitizes this traditionally paper-based process, adding automated discovery tools and modern web interfaces.

---

## Current Features

### Comprehensive Artwork Database
- Full scholarly metadata (medium, dimensions, provenance, exhibitions, literature)
- Multiple images per artwork with primary image designation
- Condition reports and conservation notes
- Signature and inscription documentation

### Automated Discovery
- **eBay API Integration** - Monitor listings with 5,000 free daily API calls
- **Confidence Scoring** - Filter results to distinguish your artist from others with similar names
- **Extensible Scrapers** - Add custom scrapers for auction houses and galleries
- **Email Alerts** - Get notified when potential works are found

### Modern Web Dashboard
- **Gallery View** - Browse artworks with cards, masonry, compact, or table layouts
- **Timeline** - Interactive chronological view of the artist's life and works
- **Tracker** - Monitor acquisition status and verification progress
- **Outreach** - Contact management for galleries, collectors, researchers
- **Discovery Hub** - Search and monitor external platforms

### Physical Display Frame
- Touch-optimized interface for Raspberry Pi kiosk displays
- Swipe navigation through artwork collection
- Configurable rotation intervals (30 seconds to 1 week)
- Perfect for galleries, memorial displays, or home collections

### Export & Integration
- CSV and JSON export with full metadata
- RESTful API for integration with other systems

---

## Roadmap

Atelier is being developed in four phases. Each phase builds upon the previous to create a complete professional-grade catalogue raisonné platform.

### Phase 1: Foundation (In Progress)

| Feature | Description | Status |
|---------|-------------|--------|
| **Enhanced Image Management** | Multiple image types (recto, verso, detail, UV), image annotations, perceptual hashing | Planned |
| **Import/Migration Tools** | CSV, JSON, Excel import with field mapping wizard | Planned |
| **Duplicate Detection** | Perceptual hash matching, title/dimension similarity, merge workflow | Planned |
| **Data Completeness Dashboard** | Track research progress, identify gaps, prioritize work | Planned |

### Phase 2: Professional Catalog Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Provenance Chain Builder** | Visual ownership history timeline with gap detection | Planned |
| **Exhibition History Module** | Comprehensive exhibition tracking with venue database | Planned |
| **Literature & Bibliography** | Citation management, publication linking, bibliography export | Planned |
| **Catalog Numbering System** | Customizable scholarly numbering schemes | Planned |

### Phase 3: Collaboration

| Feature | Description | Status |
|---------|-------------|--------|
| **Multi-User Support** | User roles (Admin, Editor, Viewer), activity logging | Planned |
| **Authentication Workflow** | Expert opinions, verification status tracking | Planned |
| **Print-Ready Export** | PDF catalog generation with professional layouts | Planned |
| **Public Tip Submission** | Allow collectors to submit potential works | Planned |

### Phase 4: Discovery & Integration

| Feature | Description | Status |
|---------|-------------|--------|
| **Auction House Integrations** | Christie's, Sotheby's, Heritage, Bonhams scrapers | Planned |
| **Price History Tracking** | Market intelligence, price trends, comparable sales | Planned |
| **Museum Collection Search** | Search Met, Smithsonian, and other institutional APIs | Planned |
| **Online Catalog Portal** | Public-facing searchable catalog website | Planned |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for Tailwind CSS)

### Installation

```bash
# Clone the repository
git clone https://github.com/TheGriffFather/Atelier.git
cd Atelier

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install Playwright browsers (for web scraping)
playwright install chromium

# Build Tailwind CSS
npm install
npm run css:build

# Copy environment config
cp .env.example .env
# Edit .env with your settings

# Initialize database
python -m src.cli init

# Start the server
python -m src.cli server
```

Access the dashboard at **http://localhost:8000**

---

## Configuration

Create a `.env` file:

```env
# Application
APP_NAME="Your Artist Catalogue"
DEBUG=false

# Database
DATABASE_URL=sqlite+aiosqlite:///data/artworks.db

# eBay API (optional - for automated discovery)
EBAY_CLIENT_ID=your-client-id
EBAY_CLIENT_SECRET=your-client-secret
EBAY_ENVIRONMENT=production

# Email Notifications (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_EMAIL=alerts@example.com

# Scraping Settings
SCRAPE_INTERVAL_MINUTES=60
REQUEST_DELAY_SECONDS=2.0
```

---

## Customizing for Your Artist

Atelier is designed to be customized for any artist. Key areas to modify:

### 1. Confidence Scoring (`src/filters/confidence.py`)

Update the positive and negative signals to match your artist:

```python
# Positive signals - terms that indicate this IS your artist
POSITIVE_SIGNALS = [
    "your artist name",
    "their art school",
    "their primary gallery",
    "their signature style",
    "their birth city",
]

# Negative signals - terms that indicate this is NOT your artist
NEGATIVE_SIGNALS = [
    "different artist with same name",
    "unrelated medium",
    "wrong time period",
]
```

### 2. Templates

Update the About page (`src/api/templates/about.html`) with your artist's:
- Biography
- Gallery affiliations
- Permanent collections
- Notable exhibitions

### 3. Seed Data

Create a seed script to populate initial known artworks:

```python
# scripts/seed_artworks.py
artworks = [
    {
        "title": "Artwork Title",
        "medium": "Oil on canvas",
        "dimensions": "24 x 36 inches",
        "year_created": 1985,
        # ... additional fields
    },
]
```

---

## Web Interface

| URL | Description |
|-----|-------------|
| `/` | Main dashboard (Gallery, Tracker, Shows, Biography) |
| `/about` | About the catalogue raisonné |
| `/timeline` | Interactive timeline |
| `/artwork/{id}` | Artwork detail page |
| `/outreach` | Contact management |
| `/discovery` | External platform monitoring |
| `/display` | Display frame settings |
| `/frame` | Touch-optimized display |

---

## API Reference

### Artworks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/artworks` | GET | List artworks (supports filtering) |
| `/api/artworks/{id}` | GET | Get artwork details |
| `/api/artworks` | POST | Create artwork |
| `/api/artworks/{id}` | PATCH | Update artwork |
| `/api/artworks/bulk` | POST | Bulk actions |
| `/api/artworks/export/csv` | GET | Export as CSV |
| `/api/artworks/export/json` | GET | Export as JSON |

### Query Parameters

```
GET /api/artworks?verified_only=true&art_type=Painting&search=landscape
```

- `verified_only` - Only verified artworks
- `art_type` - Filter by type (Painting, Drawing, Print, etc.)
- `status` - Acquisition status (new, watching, acquired, passed)
- `search` - Full-text search
- `limit` / `offset` - Pagination

---

## Database Schema

### Artwork Fields

**Identification:**
- `title`, `description`, `catalog_number`
- `source_platform`, `source_url`
- `confidence_score` (0.0-1.0)

**Physical:**
- `medium`, `dimensions`, `dimensions_cm`
- `art_type` (Painting, Drawing, Print, Sculpture, etc.)

**Dating:**
- `year_created`, `year_created_circa`

**Signature:**
- `signed` (location), `inscription`

**Provenance:**
- `provenance`, `exhibition_history`, `literature`
- `last_known_owner`, `current_location`

**Condition:**
- `condition`, `framed`, `frame_description`

**Acquisition:**
- `acquisition_status`, `acquisition_priority`, `acquisition_notes`
- `last_sale_price`, `last_sale_date`, `last_sale_venue`
- `estimated_value`

---

## Project Structure

```
atelier/
├── src/
│   ├── api/                    # FastAPI application
│   │   ├── main.py
│   │   ├── routes/             # API endpoints
│   │   ├── templates/          # Jinja2 templates
│   │   └── static/             # CSS, JS
│   ├── scrapers/               # Platform scrapers
│   │   ├── base.py             # Base scraper class
│   │   ├── ebay_api.py         # eBay Browse API
│   │   └── orchestrator.py     # Scraper coordination
│   ├── filters/                # Confidence scoring
│   ├── database/               # SQLAlchemy models
│   └── cli.py                  # CLI commands
├── scripts/                    # Utility scripts
├── tests/                      # Test suite
├── Tasks/                      # Development specifications
├── config/                     # Configuration
└── data/                       # Database and images
```

---

## Development

```bash
# Run development server with hot reload
python -m src.cli server

# Run scrapers once
python -m src.cli scrape

# Run scheduled scraping (every hour)
python -m src.cli scheduler

# Build CSS
npm run css:build
npm run css:watch  # Watch mode

# Run tests
pytest
pytest --cov=src
```

### Adding a New Scraper

```python
from src.scrapers.base import BaseScraper, ScrapedListing

class NewSiteScraper(BaseScraper):
    platform = SourcePlatform.OTHER

    def build_search_queries(self) -> list[str]:
        return ["artist name", "artist name painting"]

    async def search(self, query: str) -> list[ScrapedListing]:
        # Your scraping logic
        pass
```

---

## Deployment

### Raspberry Pi Display Frame

Atelier includes a touch-optimized display mode perfect for Raspberry Pi kiosks:

1. Install Raspberry Pi OS
2. Clone and configure Atelier on your main server
3. Configure the Pi to open Chromium in kiosk mode pointing to `http://your-server:8000/frame`

### Docker (Coming Soon)

Docker support is planned for easier deployment.

---

## Contributing

Contributions are welcome! This project is under active development and there are many ways to help:

### Priority Areas
- **Phase 1 Features** - Help implement the foundation features listed in the roadmap
- **Additional Scrapers** - Christie's, Sotheby's, Heritage, LiveAuctioneers
- **Image Processing** - Perceptual hashing and similarity matching
- **Testing** - Expand test coverage
- **Documentation** - Improve guides and examples

### Getting Started
1. Check the `Tasks/` folder for detailed feature specifications
2. Review `Tasks/SCHEMA.md` for database conventions
3. Pick a feature or bug and open an issue to discuss
4. Submit a pull request

See the [Contributing Guide](CONTRIBUTING.md) for more details.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

This project was originally built to catalog the works of Dan Brown (1949-2022), a Connecticut trompe l'oeil painter, as a gift for his daughter. It has been generalized to help anyone building a catalogue raisonné.

---

*Built with love for preserving artistic legacies.*
