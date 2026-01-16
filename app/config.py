"""
Configuration management for the FAQ Chatbot application.
Supports multiple environments: stage and production.
"""
import os
from pathlib import Path
from typing import Literal, Optional
from pydantic import field_validator
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
    
    # Location API settings (loaded from environment file)
    location_slug_api_url: str = ""  # URL for the first API that returns slug from location name
    location_data_api_url: str = ""  # URL for the second API that returns location data using slug
    location_api_key: str = ""  # API key for location APIs (optional)
    
    # Data API settings (Tier 3) - loaded from environment file
    data_api_base_url: str = "https://code-ninjas-public-api-uat.azurewebsites.net/api/v1"  # Base URL for data APIs (camps, programs, events, etc.)
    data_api_key: str = ""  # Optional API key for data APIs
    
    # LLM API settings for event discovery
    llm_api_key: str = ""  # API key for LLM (Grok, OpenAI, etc.)
    llm_api_url: str = "https://api.openai.com/v1/chat/completions"  # API endpoint URL (default: OpenAI)
    llm_provider: str = "openai"  # LLM provider: 'grok', 'openai', etc.
    # Cost-effective models that support function calling (web search):
    # - gpt-4o-mini: $0.15/$0.60 per 1M tokens (RECOMMENDED - cheapest with good quality, supports web search)
    # - gpt-3.5-turbo: $0.50/$1.50 per 1M tokens (cheaper but older, less capable, also supports web search)
    # - gpt-4o: $2.50/$10.00 per 1M tokens (more expensive but better quality)
    # Note: All OpenAI models support function calling for web search when WEB_SEARCH_ENABLED=true
    llm_model: str = "gpt-4.1-mini"  # Model name to use (gpt-4o-mini is the cheapest option with web search support)
    llm_timeout: float = 180.0  # LLM API timeout in seconds (default: 180s / 3 minutes)
    llm_max_tokens: int = 8000  # Maximum tokens for LLM response (default: 8000 for comprehensive results)
    llm_temperature: float = 0.8  # Temperature for LLM (default: 0.8 for more comprehensive searching)
    
    # Web search settings (for OpenAI models that need web search)
    # Web search uses DuckDuckGo (free, no API key required) via function calling
    web_search_enabled: bool = False  # Enable web search tool for OpenAI (uses DuckDuckGo, free, no API key required)
    
    # Events discovery settings
    events_storage_path: str = "data/events"  # Path to store CSV files
    default_search_radius: int = 5  # Default search radius in miles
    prompt_template_path: str = "app/prompts/events_discovery_prompt.txt"  # Path to prompt template
    
    # Email settings (optional, for distribution)
    email_smtp_host: str = ""  # SMTP server host
    email_smtp_port: int = 587  # SMTP server port
    email_smtp_user: str = ""  # SMTP username
    email_smtp_password: str = ""  # SMTP password
    email_from: str = ""  # From email address
    email_use_tls: bool = True  # Use TLS for SMTP
    email_send_to_owners: bool = False  # If False, send to test email instead of center owners
    email_test_recipient: str = ""  # Test email address (used when email_send_to_owners=False)
    test_mode_limit_centers: int = 0 # Limit number of centers to process in stage environment (0 = no limit)
    
    @field_validator('test_mode_limit_centers', mode='before')
    @classmethod
    def parse_test_mode_limit_centers(cls, v):
        """Convert empty string to 0 for test_mode_limit_centers."""
        if v == '' or v is None:
            return 0
        return int(v) if isinstance(v, str) else v
    sync_to_database: bool = False  # If True, sync centers to database and use database. If False, fetch directly from APIs
    
    # Cron job settings
    cron_enabled: bool = False  # Enable/disable cron jobs
    cron_schedule: str = ""  # Cron expression (default: every 5 minutes)
    # Format: minute hour day month day_of_week
    # Examples:
    # - "*/5 * * * *" = Every 5 minutes
    # - "0 2 * * *" = Daily at 2 AM
    # - "0 */6 * * *" = Every 6 hours
    # - "0 0 * * 0" = Weekly on Sunday at midnight
    
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
        
        # Pydantic BaseSettings automatically loads from .env files and environment variables
        # Environment variables take precedence over .env file values
        # No need for manual overrides - Pydantic handles this automatically
    
    return _settings

