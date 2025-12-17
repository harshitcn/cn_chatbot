"""
Configuration management for the FAQ Chatbot application.
Supports multiple environments: stage and production.
"""
import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""
    
    # Application settings
    app_name: str = "FAQ Chatbot"
    app_env: Literal["stage", "production"] = "stage"
    debug: bool = True
    
    # Database settings (dummy for now)
    database_url: str = "sqlite:///stage.db"
    
    # Vector store settings
    vector_store_path: str = "data/vector_stage.faiss"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Location API settings
    location_slug_api_url: str = ""  # URL for the first API that returns slug
    location_data_api_url: str = ""  # URL for the second API that returns location data (use {slug} placeholder)
    location_api_key: str = ""  # API key for location APIs (optional)
    
    # Web scraping settings
    scrape_base_url: str = ""  # Base URL for web scraping (e.g., "https://example.com")
    scrape_url_pattern: str = "{base_url}/{location-slug}"  # URL pattern for scraping (use {base_url}, {location}, {location_name}, {location-slug})
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get the active settings instance.
    Loads the appropriate .env file based on APP_ENV environment variable.
    
    Returns:
        Settings: The active settings instance
    """
    global _settings
    
    if _settings is None:
        # Get environment from environment variable or default to stage
        app_env = os.getenv("APP_ENV", "stage").lower()
        
        # Determine which .env file to load
        env_file = f".env.{app_env}"
        env_path = Path(env_file)
        
        # Check if environment-specific .env file exists
        if env_path.exists():
            # Load settings from environment-specific file
            _settings = Settings(
                _env_file=env_file,
                _env_file_encoding="utf-8"
            )
        else:
            # Fall back to default .env or use defaults
            default_env_file = Path(".env")
            if default_env_file.exists():
                _settings = Settings(_env_file=".env", _env_file_encoding="utf-8")
            else:
                # Use defaults
                _settings = Settings()
        
        # Ensure app_env is set correctly (override from env var if present)
        env_app_env = os.getenv("APP_ENV", app_env).lower()
        _settings.app_env = env_app_env
        
        # Override with environment variables if set (highest priority)
        # These override the .env file values
        if os.getenv("DEBUG"):
            _settings.debug = os.getenv("DEBUG").lower() in ("true", "1", "yes")
        if os.getenv("DATABASE_URL"):
            _settings.database_url = os.getenv("DATABASE_URL")
        if os.getenv("VECTOR_STORE_PATH"):
            _settings.vector_store_path = os.getenv("VECTOR_STORE_PATH")
        if os.getenv("PORT"):
            _settings.port = int(os.getenv("PORT"))
        if os.getenv("APP_NAME"):
            _settings.app_name = os.getenv("APP_NAME")
        if os.getenv("LOCATION_SLUG_API_URL"):
            _settings.location_slug_api_url = os.getenv("LOCATION_SLUG_API_URL")
        if os.getenv("LOCATION_DATA_API_URL"):
            _settings.location_data_api_url = os.getenv("LOCATION_DATA_API_URL")
        if os.getenv("LOCATION_API_KEY"):
            _settings.location_api_key = os.getenv("LOCATION_API_KEY")
        if os.getenv("SCRAPE_BASE_URL"):
            _settings.scrape_base_url = os.getenv("SCRAPE_BASE_URL")
        if os.getenv("SCRAPE_URL_PATTERN"):
            _settings.scrape_url_pattern = os.getenv("SCRAPE_URL_PATTERN")
    
    return _settings

