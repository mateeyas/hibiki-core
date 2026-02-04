# Hibiki Core

A complete, production-ready logging system with console, database, and Discord notification support.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- ✅ **Console Logging** - Standard output with configurable formatting
- ✅ **Database Logging** - Store logs in PostgreSQL with configurable minimum level
- ✅ **Discord Notifications** - Automatic notifications via webhooks for errors
- ✅ **Non-blocking** - All DB and Discord operations are async
- ✅ **Encrypted Storage** - Discord webhook URLs encrypted in database
- ✅ **Context Support** - Add user_id, request path, HTTP method to logs
- ✅ **Configurable Levels** - Separate control for DB and Discord

## Quick Start

### 1. Installation

```bash
# From PyPI (when published)
pip install hibiki-core

# From source
git clone https://github.com/yourusername/hibiki-core.git
cd hibiki-core
pip install -e .

# Or copy directly into your project
cp -r hibiki_core /path/to/your/project/
pip install aiohttp cryptography sqlalchemy asyncpg
```

### 2. Environment Variables

```bash
# Required
ENCRYPTION_KEY=your_encryption_key_here  # Generate with: python -c "from hibiki_core.encryption import generate_key; print(generate_key())"

# Optional (defaults shown)
LOG_DB_MIN_LEVEL=WARNING    # What gets saved to database
LOG_DISCORD_MIN_LEVEL=ERROR # What gets sent to Discord

# Optional - Console Format (only affects console output, not DB or Discord)
# ENV=production  # Uncomment for JSON-formatted console logs (for log aggregation tools like ELK, Datadog)
                  # Leave commented/unset for human-readable console logs (default)
```

### 3. Database Setup

**Option A: Use the factory functions (recommended)**

```python
from sqlalchemy.orm import declarative_base
from hibiki_core.models import create_log_model, create_discord_config_model

Base = declarative_base()

# Create models
Log = create_log_model(Base)
DiscordNotificationConfig = create_discord_config_model(Base)

# Create tables
Base.metadata.create_all(engine)
```

**Option B: Use the SQL directly**

```python
from logging_package.models import LOG_TABLE_SQL, DISCORD_CONFIG_TABLE_SQL

# Execute the SQL against your database
```

### 4. Initialize Logging

```python
from hibiki_core import configure_logging, setup_db_logging, get_logger

# Configure console logging (call once at app startup)
configure_logging()

# Setup database and Discord logging (after DB is initialized)
setup_db_logging(
    session_maker=your_async_session_maker,
    log_model=Log,
    discord_config_model=DiscordNotificationConfig  # Optional, for Discord notifications
)

# Use in your code
logger = get_logger(__name__)
logger.error("Something went wrong", exc_info=True)
```

## Usage

### Basic Logging

```python
from logging_package import get_logger

logger = get_logger("app.payments")

# Standard logging
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")

# With exception info
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {str(e)}", exc_info=True)
```

### Logging with Context

```python
from logging_package import get_logger, add_context_to_logger

logger = get_logger("app.users")

# Add request context
context_logger = add_context_to_logger(
    logger,
    user_id=user.id,
    path="/api/users",
    method="POST"
)

context_logger.error("User creation failed")
# Discord notification will include user_id, path, and method
```

### Discord Setup

1. Create a Discord webhook in your server
2. Configure via your application's API or database directly:

```sql
INSERT INTO discord_notification_config (
    notification_type,
    webhook_url_encrypted,
    username,
    is_enabled
) VALUES (
    'log',
    'ENCRYPTED_WEBHOOK_URL',  -- Use encryption.encrypt() function
    'Bot Name',
    true
);
```

Or use the API routes (copy `app/routes/discord_notifications.py` to your project).

## Configuration

### Environment Variables

```bash
# Required
ENCRYPTION_KEY=your_key  # For encrypting Discord webhook URLs

# Database and Discord logging levels
LOG_DB_MIN_LEVEL=WARNING    # Database: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DISCORD_MIN_LEVEL=ERROR # Discord: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Console logging format (optional)
ENV=production  # Set to "production" for JSON logs (for ELK, Datadog, etc.)
                # Leave unset for human-readable logs (default)
                # NOTE: Only affects console format, not DB or Discord
```

### Log Levels

Control what gets logged to each destination:

```bash
# Database: WARNING and above (saves disk space)
LOG_DB_MIN_LEVEL=WARNING

# Discord: ERROR and above (reduces noise)
LOG_DISCORD_MIN_LEVEL=ERROR
```

Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

### Common Configurations

**Production (minimal):**

```bash
ENV=production              # JSON-formatted console logs
LOG_DB_MIN_LEVEL=WARNING
LOG_DISCORD_MIN_LEVEL=CRITICAL
```

**Production (readable console logs):**

```bash
# ENV not set                # Human-readable console logs
LOG_DB_MIN_LEVEL=WARNING
LOG_DISCORD_MIN_LEVEL=ERROR
```

**Development (verbose):**

```bash
# ENV not set or ENV=development
LOG_DB_MIN_LEVEL=DEBUG
LOG_DISCORD_MIN_LEVEL=WARNING
```

**Troubleshooting:**

```bash
# ENV not set
LOG_DB_MIN_LEVEL=DEBUG
LOG_DISCORD_MIN_LEVEL=ERROR
```

## API

### Main Functions

```python
from logging_package import (
    configure_logging,      # Setup console logging
    setup_db_logging,       # Setup DB + Discord logging
    get_logger,             # Get a logger instance
    add_context_to_logger,  # Add context to logs
    log_to_db,              # Manually log to DB
    log_to_discord,         # Manually send to Discord
    log_error,              # Log an exception
)
```

### Encryption Utilities

```python
from logging_package.encryption import encrypt, decrypt, generate_key

# Generate a new encryption key
key = generate_key()

# Encrypt/decrypt webhook URLs
encrypted = encrypt("https://discord.com/api/webhooks/...")
original = decrypt(encrypted)
```

### Models

```python
from logging_package.models import (
    create_log_model,
    create_discord_config_model,
    LOG_TABLE_SQL,
    DISCORD_CONFIG_TABLE_SQL,
)
```

## File Structure

```
logging_package/
├── __init__.py              # Package exports
├── logger.py                # Core logging functionality
├── discord_service.py       # Discord webhook integration
├── config.py                # Configuration management
├── encryption.py            # Webhook URL encryption
├── models.py                # Database model factories
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Integration with Existing Projects

### FastAPI

```python
from fastapi import FastAPI
from logging_package import configure_logging, setup_db_logging, get_logger

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    configure_logging()
    setup_db_logging(
        session_maker=async_session_maker,
        log_model=Log,
        discord_config_model=DiscordNotificationConfig  # Optional
    )

logger = get_logger(__name__)

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello"}
```

### Django

```python
# In settings.py
import logging
from logging_package import configure_logging

configure_logging()

# In your views
from logging_package import get_logger

logger = get_logger(__name__)

def my_view(request):
    logger.info("View accessed")
    return HttpResponse("Hello")
```

### Flask

```python
from flask import Flask
from logging_package import configure_logging, get_logger

app = Flask(__name__)
configure_logging()

logger = get_logger(__name__)

@app.route("/")
def hello():
    logger.info("Hello endpoint")
    return "Hello"
```

## Discord Message Format

When errors are sent to Discord, they include:

```
**ERROR** in `app.routes.payment`
```

Payment processing failed: Connection timeout

```

**Path:** `/api/v1/payments` **Method:** `POST`
**User ID:** `user-12345`
**Trace:**
```

Traceback (most recent call last):
File "/app/routes/payment.py", line 45
...

```

```

## Troubleshooting

### Logs not appearing in database

1. Check `LOG_DB_MIN_LEVEL` is set correctly
2. Verify `setup_db_logging()` was called
3. Check database connection

### Discord notifications not sending

1. Verify webhook URL is configured in database
2. Check `LOG_DISCORD_MIN_LEVEL` allows the log level
3. Ensure `notification_type = 'log'` and `is_enabled = true`
4. Test webhook manually:
   ```bash
   curl -X POST "WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -d '{"content": "Test"}'
   ```

### Encryption errors

1. Ensure `ENCRYPTION_KEY` is set
2. If you change the key, re-encrypt all webhook URLs
3. Generate new key: `python -c "from hibiki_core.encryption import generate_key; print(generate_key())"`

## License

MIT License - Feel free to use in your projects!

## Support

For issues or questions, refer to the main SoundLocal API documentation.
