import logging
import logging.config
import os
import traceback
import sys
from typing import Optional
import asyncio

# Use relative imports for package
try:
    from .config import config as logging_config
except ImportError:
    # Fallback for direct usage
    from app.core.config import settings as logging_config

# Database imports will be initialized later to avoid circular imports
async_session_maker = None
Log = None
DiscordNotificationConfig = None

# Will be set during setup_db_logging
DB_LOG_MIN_LEVEL = logging.WARNING
DISCORD_LOG_MIN_LEVEL = logging.ERROR

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "format": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "json_console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "app": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "fastapi": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


def configure_logging():
    if os.getenv("ENV", "development") == "production":
        LOGGING_CONFIG["root"]["level"] = "ERROR"
        LOGGING_CONFIG["loggers"]["uvicorn"]["level"] = "ERROR"
        LOGGING_CONFIG["loggers"]["app"]["level"] = "ERROR"
        LOGGING_CONFIG["loggers"]["fastapi"]["level"] = "ERROR"
        LOGGING_CONFIG["root"]["handlers"] = ["json_console"]
    logging.config.dictConfig(LOGGING_CONFIG)


def setup_db_logging(session_maker, log_model, discord_config_model=None):
    """
    Initialize database logging with session maker and Log model
    Call this after app startup to avoid circular imports

    Args:
        session_maker: The async session maker for database operations
        log_model: The Log model class
        discord_config_model: Optional DiscordNotificationConfig model for Discord logging
    """
    global async_session_maker, Log, DB_LOG_MIN_LEVEL, DISCORD_LOG_MIN_LEVEL, DiscordNotificationConfig
    async_session_maker = session_maker
    Log = log_model
    DiscordNotificationConfig = discord_config_model

    # Set the minimum log levels from settings
    try:
        from .config import config as settings
    except ImportError:
        from app.core.config import settings
    
    DB_LOG_MIN_LEVEL = getattr(logging, settings.LOG_DB_MIN_LEVEL.upper(), logging.WARNING)
    DISCORD_LOG_MIN_LEVEL = getattr(logging, settings.LOG_DISCORD_MIN_LEVEL.upper(), logging.ERROR)

    # Register our custom handler with all existing loggers
    register_db_handler_with_loggers()


async def log_to_db(
    level: str,
    message: str,
    logger_name: str,
    user_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
    trace: Optional[str] = None,
):
    """
    Log an event to the database
    Only logs messages at or above the configured minimum level (default: WARNING)

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        logger_name: Name of the logger
        user_id: Optional user ID
        path: Optional request path
        method: Optional request method (GET, POST, etc.)
        trace: Optional stack trace for errors
    """
    # Only log important events to the database
    if not async_session_maker or not Log:
        # Database logging not initialized yet
        return

    numeric_level = getattr(logging, level.upper(), None)
    if not numeric_level or numeric_level < DB_LOG_MIN_LEVEL:
        return

    # Create a log entry
    try:
        async with async_session_maker() as session:
            log_entry = Log(
                level=level.upper(),
                message=message,
                logger_name=logger_name,
                user_id=user_id,
                path=path,
                method=method,
                trace=trace,
            )
            session.add(log_entry)
            await session.commit()
    except Exception as e:
        # If we can't log to the database, log to the console instead
        print(f"Error logging to database: {str(e)}")


async def log_error(
    error: Exception,
    logger_name: str,
    message: Optional[str] = None,
    user_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
):
    """
    Log an exception to the database

    Args:
        error: The exception to log
        logger_name: Name of the logger
        message: Optional custom message (defaults to str(error))
        user_id: Optional user ID
        path: Optional request path
        method: Optional request method
    """
    error_message = message or str(error)
    trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))

    await log_to_db(
        level="ERROR",
        message=error_message,
        logger_name=logger_name,
        user_id=user_id,
        path=path,
        method=method,
        trace=trace,
    )


async def log_to_discord(
    level: str,
    message: str,
    logger_name: str,
    trace: Optional[str] = None,
    user_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
):
    """
    Send error notification to Discord if configured (non-blocking).
    Only sends logs at or above the configured minimum level (default: ERROR).
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Error message
        logger_name: Name of the logger
        trace: Optional stack trace
        user_id: Optional user ID
        path: Optional request path
        method: Optional HTTP method
    """
    # Only send for logs at or above the minimum level
    numeric_level = getattr(logging, level.upper(), None)
    if not numeric_level or numeric_level < DISCORD_LOG_MIN_LEVEL:
        return
    
    if not async_session_maker or not DiscordNotificationConfig:
        return
    
    try:
        # Import here to avoid circular imports
        try:
            from .discord_service import send_error_notification
            from .encryption import decrypt
        except ImportError:
            from app.services.discord_service import send_error_notification
            from app.core.encryption import decrypt
            
        from sqlalchemy import select
        
        # Get Discord log notification config from database
        async with async_session_maker() as session:
            result = await session.execute(
                select(DiscordNotificationConfig).where(
                    DiscordNotificationConfig.notification_type == "log",
                    DiscordNotificationConfig.is_enabled == True
                )
            )
            config = result.scalar_one_or_none()
            
            if not config:
                # No error notification configured
                return
            
            # Decrypt webhook URL
            webhook_url = decrypt(config.webhook_url_encrypted)
            username = config.username
            
            # Send notification (non-blocking)
            await send_error_notification(
                level=level,
                message=message,
                logger_name=logger_name,
                webhook_url=webhook_url,
                username=username,
                trace=trace,
                user_id=user_id,
                path=path,
                method=method
            )
            
    except Exception as e:
        # Never let Discord errors break the application
        # Use print to avoid recursive logging
        print(f"Error sending Discord error notification: {str(e)}")


class AsyncDBHandler(logging.Handler):
    """
    Custom logging handler that asynchronously logs to the database.
    Only logs messages at or above the configured minimum level.
    """

    def __init__(self, level=None):
        """Initialize with the configured minimum level"""
        if level is None:
            level = DB_LOG_MIN_LEVEL
        super().__init__(level)

    def emit(self, record):
        """
        Log the specified logging record to the database asynchronously.
        """
        # Skip if below the minimum level
        if record.levelno < DB_LOG_MIN_LEVEL:
            return

        # Extract useful information from the record
        try:
            # Get user_id, path, and method from extra parameters if available
            user_id = getattr(record, "user_id", None)
            path = getattr(record, "path", None)
            method = getattr(record, "method", None)

            # Format the log message
            message = self.format(record)

            # Get trace from exception info if available
            trace = None
            if record.exc_info:
                trace = "".join(traceback.format_exception(*record.exc_info))

            # Create a future for the log_to_db call
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create a task to run log_to_db in the background
                    asyncio.create_task(
                        log_to_db(
                            level=record.levelname,
                            message=message,
                            logger_name=record.name,
                            user_id=user_id,
                            path=path,
                            method=method,
                            trace=trace,
                        )
                    )
                    
                    # Also send to Discord if at or above minimum level (non-blocking)
                    if record.levelno >= DISCORD_LOG_MIN_LEVEL:
                        asyncio.create_task(
                            log_to_discord(
                                level=record.levelname,
                                message=message,
                                logger_name=record.name,
                                trace=trace,
                                user_id=user_id,
                                path=path,
                                method=method,
                            )
                        )
                else:
                    # If we're not in an event loop, just log to console
                    print(f"DB Log: {record.levelname} - {message}")
            except RuntimeError:
                # No event loop available
                print(f"DB Log: {record.levelname} - {message}")
        except Exception as e:
            # If there's an error, just log to stdout as a fallback
            print(f"Error in AsyncDBHandler: {str(e)}")
            print(f"Original log: {record.levelname} - {self.format(record)}")


# Keep a global reference to our handler to avoid duplicate handlers
_db_handler = None


def register_db_handler_with_loggers():
    """
    Register our database handler with all loggers in the app namespace
    """
    global _db_handler

    if not _db_handler:
        _db_handler = AsyncDBHandler()

    # Get all existing loggers
    for logger_name, logger in logging.Logger.manager.loggerDict.items():
        # Only add to actual loggers (not PlaceHolders) in the app namespace
        if isinstance(logger, logging.Logger) and (
            logger_name.startswith("app.") or logger_name == "app"
        ):
            # Check if handler already exists to avoid duplicates
            has_db_handler = any(
                isinstance(handler, AsyncDBHandler) for handler in logger.handlers
            )
            if not has_db_handler:
                logger.addHandler(_db_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    If the name is in the app namespace, adds a database handler.

    Args:
        name: The name of the logger.

    Returns:
        A logger instance with database logging enabled for app loggers.
    """
    logger = logging.getLogger(name)

    # For app loggers, ensure a database handler is attached
    if name.startswith("app.") or name == "app":
        global _db_handler

        # Check if the DB handler already exists to avoid duplicates
        has_db_handler = any(
            isinstance(handler, AsyncDBHandler) for handler in logger.handlers
        )

        if not has_db_handler:
            # Create handler if it doesn't exist globally yet
            if not _db_handler:
                _db_handler = AsyncDBHandler()
            logger.addHandler(_db_handler)

    return logger


# Helper function to add context (like user_id, path, method) to a logger
def add_context_to_logger(logger, user_id=None, path=None, method=None):
    """
    Add contextual information to a logger for database logging.

    Args:
        logger: The logger to add context to
        user_id: The ID of the user making the request
        path: The path of the request
        method: The HTTP method of the request

    Returns:
        A logger with added context
    """

    # Create a logger adapter with the extra context
    class ContextAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            kwargs.setdefault("extra", {})
            if user_id is not None:
                kwargs["extra"]["user_id"] = user_id
            if path is not None:
                kwargs["extra"]["path"] = path
            if method is not None:
                kwargs["extra"]["method"] = method
            return msg, kwargs

    return ContextAdapter(logger, {})
