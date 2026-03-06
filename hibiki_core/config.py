"""
Configuration for the logging package.

Set these in your environment or pass them to configure_logging().
"""

import os
from typing import Optional


class LoggingConfig:
    """Configuration class for logging settings"""

    ENVIRONMENT: str = os.getenv("ENV", "development")

    LOG_DB_MIN_LEVEL: str = os.getenv("LOG_DB_MIN_LEVEL", "WARNING")

    LOG_DISCORD_MIN_LEVEL: str = os.getenv("LOG_DISCORD_MIN_LEVEL", "ERROR")

    ENCRYPTION_KEY: Optional[str] = os.getenv("ENCRYPTION_KEY")

    @classmethod
    def validate(cls, require_encryption: bool = True):
        """
        Validate configuration.

        Args:
            require_encryption: Whether to require ENCRYPTION_KEY.
                Set to True if using Discord webhook encryption.
        """
        if require_encryption and not cls.ENCRYPTION_KEY:
            raise ValueError(
                "ENCRYPTION_KEY environment variable must be set for Discord webhook encryption"
            )

    @classmethod
    def from_dict(cls, config: dict):
        """Create config from dictionary"""
        for key, value in config.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
        return cls


config = LoggingConfig()
