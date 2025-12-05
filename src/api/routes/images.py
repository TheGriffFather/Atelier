"""Image management endpoints."""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from config.settings import settings
from src.services.image_service import (
    download_all_artwork_images,
    regenerate_thumbnails,
)

router = APIRouter()


class ImageDownloadResponse(BaseModel):
    """Response for image download operations."""
    message: str
    downloaded: int
    skipped: int
    failed: int


class ImageDownloadStatus(BaseModel):
    """Status of image download task."""
    status: str
    message: str


# Track background task status
_download_status = {"running": False, "last_result": None}


async def _run_download_task(artwork_id: Optional[int] = None, limit: int = 100):
    """Background task for downloading images."""
    global _download_status
    _download_status["running"] = True
    _download_status["last_result"] = None

    try:
        result = await download_all_artwork_images(artwork_id=artwork_id, limit=limit)
        _download_status["last_result"] = result
    finally:
        _download_status["running"] = False


@router.post("/download", response_model=ImageDownloadStatus)
async def trigger_image_download(
    background_tasks: BackgroundTasks,
    artwork_id: Optional[int] = Query(None, description="Download images for specific artwork"),
    limit: int = Query(100, le=500, description="Maximum images to download"),
):
    """
    Trigger background download of artwork images.

    Downloads images that don't have local copies and generates thumbnails.
    """
    if _download_status["running"]:
        return ImageDownloadStatus(
            status="already_running",
            message="Image download is already in progress"
        )

    background_tasks.add_task(_run_download_task, artwork_id, limit)

    return ImageDownloadStatus(
        status="started",
        message=f"Started downloading images (limit: {limit})"
    )


@router.get("/download/status")
async def get_download_status():
    """Get the status of the image download task."""
    return {
        "running": _download_status["running"],
        "last_result": _download_status["last_result"]
    }


@router.post("/thumbnails/regenerate")
async def trigger_thumbnail_regeneration(
    background_tasks: BackgroundTasks,
    artwork_id: Optional[int] = Query(None, description="Regenerate for specific artwork"),
):
    """Regenerate thumbnails for all downloaded images."""
    background_tasks.add_task(regenerate_thumbnails, artwork_id)
    return {"status": "started", "message": "Thumbnail regeneration started"}


@router.get("/serve/{filename:path}")
async def serve_flat_image(filename: str):
    """Serve an image file from the flat images directory."""
    # Build the full path - images are stored directly in image_dir
    image_path = settings.image_dir / filename

    if not image_path.exists():
        # Try artworks subdirectory
        image_path = settings.image_dir / "artworks" / filename
        if not image_path.exists():
            # Try external subdirectory
            image_path = settings.image_dir / "external" / filename
            if not image_path.exists():
                raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

    # Security check - ensure path is within image directory
    try:
        image_path.resolve().relative_to(settings.image_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    # Determine media type
    suffix = image_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(image_path, media_type=media_type)


@router.get("/{artwork_id}/{filename:path}")
async def serve_image(artwork_id: int, filename: str):
    """Serve a local image file from artwork subdirectory."""
    # Build the full path
    image_path = settings.image_dir / str(artwork_id) / filename

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    # Security check - ensure path is within image directory
    try:
        image_path.resolve().relative_to(settings.image_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    # Determine media type
    suffix = image_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(image_path, media_type=media_type)
