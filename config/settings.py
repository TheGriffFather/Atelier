"""Application settings and configuration."""

from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Atelier"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Database
    database_url: str = "sqlite+aiosqlite:///data/artworks.db"

    # Scraping
    scrape_interval_minutes: int = 60
    request_delay_seconds: float = 2.0
    max_concurrent_requests: int = 3

    # eBay API (get credentials at https://developer.ebay.com/my/keys)
    ebay_client_id: str = ""
    ebay_client_secret: str = ""

    # Perplexity API (for research automation)
    perplexity_api_key: str = ""

    # Notifications
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    notification_email: str = ""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Paths
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    image_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data" / "images")

    def get_relative_image_path(self, absolute_path: Path) -> str:
        """
        Convert an absolute image path to a relative path for database storage.

        Stores paths relative to data_dir, e.g., 'images/artworks/1/original.jpg'
        This ensures portability between Windows dev and Docker environments.
        """
        try:
            relative = absolute_path.relative_to(self.data_dir)
            # Always use forward slashes for cross-platform compatibility
            return str(relative).replace("\\", "/")
        except ValueError:
            # Path is not under data_dir, try to extract artworks portion
            path_str = str(absolute_path).replace("\\", "/")
            if "images/artworks/" in path_str:
                idx = path_str.index("images/artworks/")
                return path_str[idx:]
            # Fallback: return just the filename with images prefix
            return f"images/{absolute_path.name}"

    def resolve_image_path(self, relative_path: Optional[str]) -> Optional[Path]:
        """
        Resolve a relative image path from database to absolute filesystem path.

        Takes paths like 'images/artworks/1/original.jpg' and resolves to
        the correct absolute path for the current environment.
        """
        if not relative_path:
            return None

        # Handle legacy absolute paths (Windows or Linux)
        if relative_path.startswith("/") or (len(relative_path) > 1 and relative_path[1] == ":"):
            # Already absolute - extract relative portion
            path_str = relative_path.replace("\\", "/")
            if "images/artworks/" in path_str:
                idx = path_str.index("images/artworks/")
                relative_path = path_str[idx:]
            elif "/data/images/" in path_str:
                idx = path_str.index("/data/images/") + len("/data/")
                relative_path = path_str[idx:]
            else:
                # Can't determine relative path, return None
                return None

        # Resolve relative to data_dir
        return self.data_dir / relative_path

    def get_image_api_url(self, relative_path: Optional[str]) -> Optional[str]:
        """
        Convert a relative image path to an API URL for serving.

        Takes paths like 'images/artworks/1/original.jpg' and returns
        '/api/images/1/original.jpg'
        """
        if not relative_path:
            return None

        # Normalize path
        path_str = relative_path.replace("\\", "/")

        # Handle legacy absolute paths
        if path_str.startswith("/") or (len(path_str) > 1 and path_str[1] == ":"):
            if "images/artworks/" in path_str:
                idx = path_str.index("images/artworks/")
                path_str = path_str[idx:]
            else:
                return None

        # Extract artwork ID and filename from 'images/artworks/{id}/{filename}'
        if path_str.startswith("images/artworks/"):
            remaining = path_str[len("images/artworks/"):]
            parts = remaining.split("/", 1)
            if len(parts) == 2:
                artwork_id, filename = parts
                return f"/api/images/{artwork_id}/{filename}"

        # Fallback to serve endpoint
        return f"/api/images/serve/{Path(path_str).name}"


settings = Settings()
