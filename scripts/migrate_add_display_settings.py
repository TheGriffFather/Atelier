"""Migration script to add display_settings table."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.database.session import engine as async_engine


async def migrate():
    """Add display_settings table to database."""
    async with async_engine.begin() as conn:
        # Check if table already exists
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='display_settings'")
        )
        if result.fetchone():
            print("Table 'display_settings' already exists, skipping creation.")
            return

        # Create the table with all columns including image_fit and excluded_art_types
        await conn.execute(text("""
            CREATE TABLE display_settings (
                id INTEGER PRIMARY KEY,
                frame_style VARCHAR DEFAULT 'wood',
                interval INTEGER DEFAULT 3600,
                shuffle BOOLEAN DEFAULT 1,
                show_title BOOLEAN DEFAULT 1,
                show_progress BOOLEAN DEFAULT 0,
                verified_only BOOLEAN DEFAULT 1,
                image_fit VARCHAR DEFAULT 'auto',
                selected_artwork_ids JSON,
                excluded_art_types JSON,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("Created 'display_settings' table.")

        # Insert default row
        await conn.execute(text("""
            INSERT INTO display_settings (id, frame_style, interval, shuffle, show_title, show_progress, verified_only, image_fit)
            VALUES (1, 'wood', 3600, 1, 1, 0, 1, 'auto')
        """))
        print("Inserted default settings row.")


if __name__ == "__main__":
    asyncio.run(migrate())
    print("Migration complete!")
