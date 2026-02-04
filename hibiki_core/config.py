"""
Configuration for the logging package.

Set these in your environment or pass them to setup_logging().
"""

import os
from typing import Optional


class LoggingConfig:
    """Configuration class for logging settings"""
    
    # Console logging
    ENVIRONMENT: str = os.getenv("ENV", "development")
    
    # Database logging
    LOG_DB_MIN_LEVEL: str = os.getenv("LOG_DB_MIN_LEVEL", "WARNING")
    
    # Discord logging
    LOG_DISCORD_MIN_LEVEL: str = os.getenv("LOG_DISCORD_MIN_LEVEL", "ERROR")
    
    # Encryption for Discord webhooks
    ENCRYPTION_KEY: Optional[str] = os.getenv("ENCRYPTION_KEY")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY environment variable must be set")
    
    @classmethod
    def from_dict(cls, config: dict):
        """Create config from dictionary"""
        for key, value in config.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
        return cls


# Default config instance
config = LoggingConfig()
