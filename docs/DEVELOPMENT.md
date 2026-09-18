# Configuration and development

Start with the [README](../README.md). The regular server initializes the schema
but does not start scheduled discovery. Collection data is local to your host.

## Settings

Copy `.env.example` to `.env`. Settings are loaded by `config/settings.py`;
environment variables override the file. Keep the file out of Git.

| Setting | Purpose |
| --- | --- |
| `APP_NAME` | API title; the current artist-specific page labels are still in the templates. |
| `API_HOST` / `API_PORT` | Native server listener; defaults to `127.0.0.1:8000`. |
| `DATABASE_URL` | Defaults to `sqlite+aiosqlite:///data/artworks.db`. Create `data/images` before first use. |
| `EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET` | Optional eBay Browse API credentials. Current standard discovery uses production endpoints. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `NOTIFICATION_EMAIL` | Optional email notifications. |
| `SCRAPE_INTERVAL_MINUTES`, `REQUEST_DELAY_SECONDS`, `MAX_CONCURRENT_REQUESTS` | Discovery timing and concurrency. |
| `ENABLE_SCHEDULER` | Docker entrypoint option; default off. |

For Docker, `API_PORT` selects the host port. Compose fixes the internal server
at port 8000 and binds it to the container interface; the host mapping remains
localhost-only. Its `./data` mount contains the database, downloaded images, and
any mail authorization files. Back up and protect that directory as private data.

Gmail uses local `data/gmail_credentials.json` and `data/gmail_token.json`.
Connect only in a trusted private installation. Authorizing Gmail does not add
an application login; see [Security](../SECURITY.md).

## CLI

Run these with the Python interpreter from your virtual environment:

```bash
python -m src.cli init
python -m src.cli server
python -m src.cli scrape
python -m src.cli scheduler
```

The last two commands contact configured external services and can send
notifications. Run them deliberately after reviewing the artist-specific search
and notification settings. The normal server command does not enable reload.
For development reload, use:

```bash
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

## CSS

The compiled `src/api/static/css/output.css` is committed for a simple first run.
To change the theme, use Node.js 20 or newer:

```bash
npm ci
npm run css:build
```

`npm run css:watch` rebuilds while editing. Review the generated stylesheet with
its input changes. Browser-based scrapers additionally require an explicit
`python -m playwright install chromium`; the default API/HTTP path does not.

## Tests

```bash
python -m pytest -q
python scripts/check_publication.py
```

Tests use synthetic fixtures. The suite covers confidence scoring and page rendering;
it does not establish complete route, Gmail, scraper, or physical-display coverage.
Do not use real email accounts, private catalogues, or credentials in tests.

## Source map

| Path | Responsibility |
| --- | --- |
| `src/api/routes`, `src/api/templates` | API endpoints and browser pages |
| `src/database` | Models, sessions, and schema initialization |
| `src/scrapers`, `src/filters` | Discovery and artist disambiguation |
| `src/services`, `src/notifications` | Images, records, mail, and notifications |
| `config/settings.py` | Runtime configuration |
| `display/hardware` | Optional display setup |
| `Tasks` | Proposed development work, not a completed-feature inventory |

CSV/JSON exports contain selected fields. They are useful for interchange, but
are not a complete backup of images, contacts, mail state, and the database.
