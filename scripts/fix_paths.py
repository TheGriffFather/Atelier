#!/usr/bin/env python3
"""
Convert absolute image paths in database to portable relative paths.

This script converts Windows/Linux absolute paths in the artwork_images table
to relative paths (e.g., 'images/artworks/1/original.jpg') for cross-platform
compatibility between Windows development and Docker deployment.

Usage:
    python fix_paths.py [database_path]

    If no path is provided, defaults to 'data/artworks.db'

Example:
    python fix_paths.py data/artworks.db
"""
import sqlite3
import re
import sys


def fix_image_paths(db_path: str) -> tuple[int, int, list]:
    """
    Update all local_path entries in artwork_images table to use relative paths.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        Tuple of (number of paths updated, number already relative, sample updated paths)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all local_path entries
    cursor.execute('SELECT id, local_path FROM artwork_images WHERE local_path IS NOT NULL')
    rows = cursor.fetchall()

    updated = 0
    already_relative = 0
    updated_paths = []

    for row in rows:
        img_id, old_path = row
        if not old_path:
            continue

        # Normalize path separators
        normalized = old_path.replace('\\', '/')

        # Skip if already in relative format (starts with 'images/')
        if normalized.startswith('images/'):
            already_relative += 1
            continue

        # Extract the relative portion from various absolute path formats
        new_path = None

        # Pattern: .../images/artworks/{id}/{filename}
        match = re.search(r'images/artworks/(\d+)/(.+)$', normalized)
        if match:
            artwork_id = match.group(1)
            filename = match.group(2)
            new_path = f'images/artworks/{artwork_id}/{filename}'
        else:
            # Pattern: .../artworks/{id}/{filename} (without images/ prefix)
            match = re.search(r'artworks/(\d+)/(.+)$', normalized)
            if match:
                artwork_id = match.group(1)
                filename = match.group(2)
                new_path = f'images/artworks/{artwork_id}/{filename}'

        if new_path:
            cursor.execute('UPDATE artwork_images SET local_path = ? WHERE id = ?', (new_path, img_id))
            updated += 1
            if len(updated_paths) < 5:
                updated_paths.append((old_path, new_path))

    conn.commit()

    # Verify the changes
    cursor.execute('SELECT local_path FROM artwork_images WHERE local_path IS NOT NULL LIMIT 5')
    sample_paths = [row[0] for row in cursor.fetchall()]

    conn.close()

    return updated, already_relative, sample_paths


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/artworks.db'

    print(f"Converting image paths to relative format")
    print(f"Database: {db_path}")
    print("-" * 50)

    try:
        updated, already_relative, sample_paths = fix_image_paths(db_path)

        print(f"Paths updated: {updated}")
        print(f"Already relative: {already_relative}")

        if sample_paths:
            print("\nSample paths after conversion:")
            for path in sample_paths:
                print(f"  {path}")

        print("\nDone!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
