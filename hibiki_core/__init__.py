"""
Hibiki Core - Complete Logging Solution

A comprehensive logging package with console, database, and Discord notification support.

Features:
- Console logging (standard output)
- Database logging (PostgreSQL via SQLAlchemy)
- Discord notifications (via webhooks)
- Configurable log levels for each destination
- Non-blocking async operations
- Encrypted webhook storage

Installation:
    pip install hibiki-core

Usage:
    from hibiki_core import configure_logging, setup_db_logging, get_logger
    
    # Setup (call once at app startup)
    configure_logging()
    setup_db_logging(
        session_maker=your_session_maker,
        log_model=YourLogModel,
        discord_config_model=YourDiscordConfigModel  # Optional, for Discord notifications
    )
    
    # Use in your code
    logger = get_logger(__name__)
    logger.error("Something went wrong", exc_info=True)
"""

__version__ = "2.0.0"

from .logger import (
    configure_logging,
    setup_db_logging,
    get_logger,
    add_context_to_logger,
    log_to_db,
    log_to_discord,
    log_error,
)

__all__ = [
    "configure_logging",
    "setup_db_logging",
    "get_logger",
    "add_context_to_logger",
    "log_to_db",
    "log_to_discord",
    "log_error",
]
