# Atelier

### Give an artist's work a place to live.

Atelier is an open-source workspace for building a **catalogue raisonné**: a documented record of an artist's known works. Bring images, provenance, exhibitions, research leads, and acquisition notes together, then browse the collection in a gallery or on a dedicated display.

![Status](https://img.shields.io/badge/status-early_development-c5a065) ![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab) ![Stack](https://img.shields.io/badge/FastAPI-SQLAlchemy-009688) [![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**[Tour the interface](#a-workspace-for-the-whole-collection)** · **[Get started](#run-atelier-locally)** · **[Display frame](#from-catalogue-to-display)** · **[Make it your own](#adapt-it-for-another-artist)** · **[Roadmap](#where-the-project-is-heading)**

![Atelier gallery with artwork thumbnails in a masonry layout](docs/images/gallery.jpg)

*The existing web interface, captured from the original Dan Brown catalogue. These historical screenshots illustrate the UI; a fresh installation starts with an empty database. Artwork images retain their respective rights.*

## A workspace for the whole collection

Atelier is built for researchers, estate managers, galleries, and collectors who need more than a folder of images. A record can connect a work's physical description with where it was shown, how it changed hands, and what still needs to be verified.

| Workflow | Available in the source |
| --- | --- |
| **Catalogue** | Artwork records, multiple images, dimensions, medium, dating, condition, provenance notes, and verification status. |
| **Browse and compare** | Gallery layouts, filtering, artwork details, acquisition tracking, and a chronological timeline. |
| **Document exhibitions** | Show records, dates and venues, with links to the works exhibited. |
| **Follow research leads** | Contacts, outreach records, follow-ups, and optional Gmail integration. |
| **Discover works** | Saved searches, result review, and artist-specific confidence scoring. eBay API and web-scraper integrations require separate setup. |
| **Share a view** | CSV/JSON exports of selected record fields, a REST API, and a browser-based display mode. |

### The collection in context

<table>
<tr>
<td width="50%" valign="top"><a href="docs/images/timeline.jpg"><img src="docs/images/timeline.jpg" alt="Atelier timeline of artwork and exhibition records" width="460"></a><br><strong>Follow the timeline</strong><br>See works and exhibitions in chronological context.</td>
<td width="50%" valign="top"><a href="docs/images/exhibitions.jpg"><img src="docs/images/exhibitions.jpg" alt="Atelier exhibition cards with dates and linked artworks" width="460"></a><br><strong>Connect works to shows</strong><br>Keep exhibition history beside the collection.</td>
</tr>
</table>

### Research without losing the thread

The tracker keeps a candidate work's source and acquisition status together. Discovery adds saved searches and results to review. Confidence scores help prioritize candidates; they are research aids, **not authentication of artwork**. Outreach records keep contacts and follow-ups alongside the research.

![Atelier Discovery page with saved search cards and review controls](docs/images/discovery.jpg)

External services need your own credentials where applicable. API quotas, availability, and site terms vary; scraper code in the repository does not mean every provider has been recently tested.

## From catalogue to display

The `/frame` page presents the collection as a slideshow, with touch navigation and display settings. Run it in a normal browser or open it in Chromium kiosk mode on a Raspberry Pi connected to a suitable screen.

![Atelier display preview with artwork, slideshow controls and frame settings](docs/images/display-frame.jpg)

The application can run on the same computer as the display. A separate display client needs a deliberately configured, protected connection to the host. See the [display hardware guide](display/hardware/README.md) for parts, layout, and kiosk setup. A Pi and touchscreen are optional; start on a computer first.

## Run Atelier locally

Use **Python 3.11 or newer** and Git. A compiled stylesheet is included, so Node.js is only needed when editing the Tailwind theme. No API keys are needed to open an empty catalogue.

### Windows PowerShell

```powershell
git clone https://github.com/TheGriffFather/Atelier.git
cd Atelier
py -3 -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
New-Item -ItemType Directory -Force data/images | Out-Null
./.venv/Scripts/python.exe -m src.cli init
./.venv/Scripts/python.exe -m src.cli server
```

### macOS / Linux

```bash
git clone https://github.com/TheGriffFather/Atelier.git
cd Atelier
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
cp .env.example .env
mkdir -p data/images
.venv/bin/python -m src.cli init
.venv/bin/python -m src.cli server
```

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** and use **Add Artwork** to create your first record. API documentation is at `/docs`. Stop the server with **Ctrl+C**.

**Keep this installation private.** Atelier does not yet have application login or role-based access. Its catalogue, outreach, and connected Gmail operations share the host's authority. The default setup binds to localhost; do not expose the port to the internet. See [security and private data](SECURITY.md) before configuring remote access or connecting mail.

### Docker

Docker Compose is included. Copy `.env.example` to `.env`, then run:

```bash
docker compose up --build -d
```

Open the same local URL. Data persists in `./data`; `docker compose down` stops the service. Host access is bound to localhost by default. Automated scraping is off unless you explicitly set `ENABLE_SCHEDULER=true`.

The image includes the Playwright Python package, but no browser binaries. Browser-driven scrapers need additional setup. Review [configuration and development](docs/DEVELOPMENT.md) before enabling discovery integrations.

## Adapt it for another artist

Atelier began as a catalogue of the painter **Dan Brown (1949–2022)**. The current UI labels, biography, search terms, notification text, and confidence rules still reflect that artist. Changing `APP_NAME` alone does not retarget the whole app.

For another collection, update these together:

| Area | Starting point |
| --- | --- |
| Name and runtime settings | [Configuration](config/settings.py) and your ignored `.env` |
| Branding, biography and timeline | [Templates](src/api/templates) and [biography data](src/api/routes/biography.py) |
| Search terms and provider behavior | [Scrapers](src/scrapers) and [saved-search routes](src/api/routes/alerts.py) |
| Artist disambiguation | [Confidence rules](src/filters/confidence.py) and [their tests](tests/filters/test_confidence.py) |
| Email wording | [Notification templates](src/notifications/email.py) |

Keep collection records, private research, images, credentials, and backups in local storage. Use a fresh database for a new collection. A reusable artist profile is a natural next step for the project.

## Where the project is heading

**Early development.** The repository contains the workflows shown above, but it is not a finished multi-user or public collection-hosting service. The test suite covers confidence scoring and page rendering, not every workflow or external integration.

| Planned work | Direction |
| --- | --- |
| Collection foundations | Guided imports, duplicate detection, image annotations, and completeness checks. |
| Scholarly records | Structured provenance chains, bibliographies, and catalogue numbering. |
| Collaboration | Login, roles, activity history, and review workflows. |
| Publishing | Print-ready catalogues and a separate public collection portal. |
| Discovery | More provider integrations and better review tools. |

The [task specifications](Tasks/README.md) describe the longer-term plan. They are design proposals, not proof that a feature is implemented.

## Built with

FastAPI and Jinja2 serve the web workspace; SQLAlchemy and SQLite store records. The frontend uses Tailwind CSS and vanilla JavaScript. Discovery uses HTTP/API clients and optional browser automation. Gmail and SMTP are optional integrations.

| Guide | Contents |
| --- | --- |
| [Interface walkthrough](docs/WALKTHROUGH.md) | Pages, screenshots, and how the workflows connect |
| [Configuration and development](docs/DEVELOPMENT.md) | Environment settings, CSS, tests, CLI commands, and source layout |
| [Display hardware](display/hardware/README.md) | Computer/Pi setup and browser kiosk mode |
| [Security](SECURITY.md) | Deployment boundaries and private-data handling |
| [Contributing](CONTRIBUTING.md) | Development and publication checks |

## License and image credits

The software is released under the **[MIT License](LICENSE)**. Artwork and third-party imagery shown in UI screenshots are not relicensed by the software license. See [image notes](docs/images/README.md). Atelier is an independent project, unaffiliated with the artists' estates or external services it can use.
