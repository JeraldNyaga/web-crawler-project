"""
Configuration management using Pydantic Settings.
All settings are loaded from environment variables.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    
    mongodb_uri: str
    mongodb_db_name: str = "books_crawler"    
    
    api_secret_key: str
    api_title: str = "Books Crawler API"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_keys: str  
    

    target_url: str = "https://books.toscrape.com"
    crawler_max_retries: int = 3
    crawler_retry_delay: int = 2
    crawler_timeout: int = 30
    crawler_concurrent_requests: int = 10
    crawler_user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    
    # Scheduler Settings
    scheduler_enabled: bool = True
    scheduler_run_time: str = "02:00"
    scheduler_timezone: str = "UTC"
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 3600  # seconds
    
    # Logging
    log_level: str = "INFO"
    log_file_enabled: bool = True
    log_dir: str = "logs"
    
    # Environment
    environment: str = "development"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def api_keys_list(self) -> List[str]:
        """Parse comma-separated API keys into a list."""
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        
        return self.environment.lower() == "development"



settings = Settings()