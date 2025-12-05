"""FastAPI application for the art tracker."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config.settings import settings
from src.database import init_db
from src.api.routes import artworks, biography, display, health, scraper, images, outreach, exhibitions, gmail, alerts

# Paths for static files and templates
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Initialize Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title=settings.app_name,
    description="Track and monitor artwork by Dan Brown (1949-2022)",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for dashboard and display frame
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if STATIC_DIR.exists():
    app.mount("/api/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(artworks.router, prefix="/api/artworks", tags=["Artworks"])
app.include_router(biography.router, prefix="/api", tags=["Biography"])
app.include_router(display.router, prefix="/api/display", tags=["Display Frame"])
app.include_router(scraper.router, prefix="/api", tags=["Scraper"])
app.include_router(images.router, prefix="/api/images", tags=["Images"])
app.include_router(outreach.router, tags=["Outreach"])
app.include_router(exhibitions.router, prefix="/api/exhibitions", tags=["Exhibitions"])
app.include_router(gmail.router, tags=["Gmail"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])

# Mount image directory for serving local images
if settings.image_dir.exists():
    app.mount("/api/images", StaticFiles(directory=settings.image_dir), name="images")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/artwork/{artwork_id}", response_class=HTMLResponse)
async def artwork_detail(request: Request, artwork_id: int):
    """Serve the artwork detail page."""
    return templates.TemplateResponse("artwork.html", {"request": request, "artwork_id": artwork_id})


@app.get("/display", response_class=HTMLResponse)
async def display_settings(request: Request):
    """Serve the display frame settings and preview page."""
    return templates.TemplateResponse("display-settings.html", {"request": request})


@app.get("/frame", response_class=HTMLResponse)
async def frame_display(request: Request):
    """Serve the touch-optimized frame display for physical art frames."""
    return templates.TemplateResponse("frame.html", {"request": request})


@app.get("/outreach", response_class=HTMLResponse)
async def outreach_page(request: Request):
    """Serve the outreach tracking page."""
    return templates.TemplateResponse("outreach.html", {"request": request})


@app.get("/timeline", response_class=HTMLResponse)
async def timeline_page(request: Request):
    """Serve the timeline page showing Dan Brown's life and works."""
    return templates.TemplateResponse("timeline.html", {"request": request})


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """Serve the About page explaining what a catalogue raisonné is."""
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/discovery", response_class=HTMLResponse)
async def discovery_page(request: Request):
    """Serve the Discovery Hub for searching and finding Dan Brown artwork."""
    return templates.TemplateResponse("discovery.html", {"request": request})
