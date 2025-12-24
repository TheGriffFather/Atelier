"""Image download, caching, and thumbnail generation service."""

import asyncio
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import aiohttp
from PIL import Image
from sqlalchemy import select

from config.settings import settings
from src.database import ArtworkImage, get_session_context

logger = logging.getLogger(__name__)

# Thumbnail sizes
THUMBNAIL_SIZES = {
    "small": (150, 150),
    "medium": (300, 300),
    "large": (600, 600),
}


def get_image_hash(url: str) -> str:
    """Generate a unique hash for an image URL."""
    return hashlib.md5(url.encode()).hexdigest()


def get_image_path(url: str, artwork_id: int) -> Path:
    """Get the local path for storing an image."""
    image_hash = get_image_hash(url)
    ext = Path(url.split("?")[0]).suffix or ".jpg"
    return settings.image_dir / str(artwork_id) / f"{image_hash}{ext}"


def get_thumbnail_path(image_path: Path, size: str) -> Path:
    """Get the path for a thumbnail."""
    thumb_dir = image_path.parent / "thumbs"
    return thumb_dir / f"{image_path.stem}_{size}{image_path.suffix}"


async def download_image(url: str, dest_path: Path, timeout: int = 30) -> bool:
    """Download an image from URL to local path."""
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                if response.status != 200:
                    logger.warning(f"Failed to download {url}: HTTP {response.status}")
                    return False

                content = await response.read()
                dest_path.write_bytes(content)
                logger.info(f"Downloaded image to {dest_path}")
                return True

    except asyncio.TimeoutError:
        logger.warning(f"Timeout downloading {url}")
        return False
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return False


def generate_thumbnail(image_path: Path, size: str = "medium") -> Optional[Path]:
    """Generate a thumbnail for an image."""
    if size not in THUMBNAIL_SIZES:
        logger.warning(f"Unknown thumbnail size: {size}")
        return None

    try:
        thumb_path = get_thumbnail_path(image_path, size)
        thumb_path.parent.mkdir(parents=True, exist_ok=True)

        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Create thumbnail maintaining aspect ratio
            img.thumbnail(THUMBNAIL_SIZES[size], Image.Resampling.LANCZOS)

            # Save with good quality
            img.save(thumb_path, "JPEG", quality=85, optimize=True)
            logger.info(f"Generated {size} thumbnail: {thumb_path}")
            return thumb_path

    except Exception as e:
        logger.error(f"Error generating thumbnail for {image_path}: {e}")
        return None


def generate_all_thumbnails(image_path: Path) -> dict[str, Optional[Path]]:
    """Generate all thumbnail sizes for an image."""
    return {size: generate_thumbnail(image_path, size) for size in THUMBNAIL_SIZES}


def get_image_dimensions(image_path: Path) -> Optional[Tuple[int, int]]:
    """Get the dimensions of an image."""
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        logger.error(f"Error getting dimensions for {image_path}: {e}")
        return None


async def download_artwork_image(image: ArtworkImage) -> bool:
    """Download an artwork image and update the database."""
    if not image.url:
        return False

    # Skip if already downloaded
    if image.local_path:
        local_path = Path(image.local_path)
        if local_path.exists():
            logger.debug(f"Image already exists: {local_path}")
            return True

    # Download the image
    dest_path = get_image_path(image.url, image.artwork_id)
    success = await download_image(image.url, dest_path)

    if success:
        # Get dimensions
        dimensions = get_image_dimensions(dest_path)

        # Generate thumbnails
        generate_all_thumbnails(dest_path)

        # Update database with RELATIVE path for cross-platform compatibility
        async with get_session_context() as session:
            result = await session.execute(
                select(ArtworkImage).where(ArtworkImage.id == image.id)
            )
            db_image = result.scalar_one_or_none()

            if db_image:
                # Store relative path (e.g., 'images/artworks/1/original.jpg')
                # This ensures portability between Windows dev and Docker
                db_image.local_path = settings.get_relative_image_path(dest_path)
                db_image.date_downloaded = datetime.utcnow()
                if dimensions:
                    db_image.width, db_image.height = dimensions
                await session.commit()

        return True

    return False


async def download_all_artwork_images(artwork_id: Optional[int] = None, limit: int = 100) -> dict:
    """Download all images for artworks, optionally filtered by artwork_id."""
    stats = {"downloaded": 0, "skipped": 0, "failed": 0}

    async with get_session_context() as session:
        query = select(ArtworkImage)

        if artwork_id:
            query = query.where(ArtworkImage.artwork_id == artwork_id)

        # Only download images without local paths
        query = query.where(
            (ArtworkImage.local_path == None) | (ArtworkImage.local_path == "")
        ).limit(limit)

        result = await session.execute(query)
        images = result.scalars().all()

    for image in images:
        success = await download_artwork_image(image)
        if success:
            stats["downloaded"] += 1
        else:
            stats["failed"] += 1

        # Small delay between downloads
        await asyncio.sleep(0.5)

    logger.info(f"Image download complete: {stats}")
    return stats


async def regenerate_thumbnails(artwork_id: Optional[int] = None) -> dict:
    """Regenerate thumbnails for all downloaded images."""
    stats = {"generated": 0, "failed": 0}

    async with get_session_context() as session:
        query = select(ArtworkImage).where(ArtworkImage.local_path != None)

        if artwork_id:
            query = query.where(ArtworkImage.artwork_id == artwork_id)

        result = await session.execute(query)
        images = result.scalars().all()

    for image in images:
        local_path = Path(image.local_path)
        if local_path.exists():
            thumbs = generate_all_thumbnails(local_path)
            if any(thumbs.values()):
                stats["generated"] += 1
            else:
                stats["failed"] += 1

    logger.info(f"Thumbnail regeneration complete: {stats}")
    return stats


def get_local_image_url(image: ArtworkImage, size: Optional[str] = None) -> str:
    """Get the URL for a local image or its thumbnail."""
    if not image.local_path:
        return image.url

    # Resolve relative path to absolute for file existence checks
    local_path = settings.resolve_image_path(image.local_path)
    if not local_path:
        return image.url

    if size and size in THUMBNAIL_SIZES:
        thumb_path = get_thumbnail_path(local_path, size)
        if thumb_path.exists():
            # Use helper to generate API URL
            thumb_relative = settings.get_relative_image_path(thumb_path)
            return settings.get_image_api_url(thumb_relative) or image.url

    if local_path.exists():
        # Use stored relative path directly for URL generation
        return settings.get_image_api_url(image.local_path) or image.url

    # Fallback to original URL
    return image.url
