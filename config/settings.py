"""Application settings and configuration."""

from pathlib import Path
from typing import Literal

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
    app_name: str = "Dan Brown Art Tracker"
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


settings = Settings()
