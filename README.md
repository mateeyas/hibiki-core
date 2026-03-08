# Hibiki Core

A production-ready logging system with console, database, and Discord notification support.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## AI Coding Assistant Support

If you use an AI coding assistant (Cursor, GitHub Copilot, ChatGPT, Claude, etc.), provide [`LLMGUIDE.md`](LLMGUIDE.md) as context. It contains a complete reference for the package's API, initialization sequence, async behavior, and common pitfalls -- everything the model needs to generate correct integration code.

## Features

- **Console Logging** - Human-readable or JSON-formatted output
- **Database Logging** - Store logs in PostgreSQL (or any SQLAlchemy-supported DB)
- **Discord Notifications** - Automatic webhook notifications for errors
- **Non-blocking** - All DB and Discord operations are async
- **Encrypted Storage** - Discord webhook URLs encrypted at rest
- **Context Support** - Attach user_id, request path, HTTP method to logs
- **Configurable Levels** - Separate thresholds for console, DB, and Discord

## Installation

```bash
pip install hibiki-core

# With PostgreSQL support
pip install hibiki-core[postgres]
```

## Quick Start

### Console-only (no database)

```python
from hibiki_core import configure_logging, get_logger

configure_logging(namespace="myapp")

logger = get_logger("myapp.service")
logger.info("Ready")
logger.error("Something broke", exc_info=True)
```

### With database and Discord

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from hibiki_core import configure_logging, setup_db_logging, get_logger
from hibiki_core.models import create_log_model, create_discord_config_model

# Define models
Base = declarative_base()
Log = create_log_model(Base)
DiscordNotificationConfig = create_discord_config_model(Base)

# Create async engine and session
engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Initialize logging (call once at startup)
configure_logging(namespace="myapp")
setup_db_logging(
    session_maker=session_maker,
    log_model=Log,
    namespace="myapp",
    discord_config_model=DiscordNotificationConfig,  # optional
)

logger = get_logger("myapp.module")
logger.error("Something went wrong", exc_info=True)
```

Alternatively, create tables directly with raw SQL:

```python
from hibiki_core.models import LOG_TABLE_SQL, DISCORD_CONFIG_TABLE_SQL
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ENCRYPTION_KEY` | *(none)* | Required if using Discord webhook encryption. Generate with: `python -c "from hibiki_core.encryption import generate_key; print(generate_key())"` |
| `LOG_DB_MIN_LEVEL` | `WARNING` | Minimum level saved to database. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_DISCORD_MIN_LEVEL` | `ERROR` | Minimum level sent to Discord. Same options as above. |
| `ENV` | `development` | Set to `production` for JSON console output **and** ERROR-only console log level. Leave unset for human-readable output at INFO level. |

### Namespace

The `namespace` parameter controls which loggers receive DB and Discord handlers. Only loggers whose names start with the namespace will log to the database and Discord.

```python
configure_logging(namespace="myapp")
setup_db_logging(session_maker=..., log_model=..., namespace="myapp")

logger = get_logger("myapp.api")     # Gets DB + Discord handlers
logger = get_logger("other.module")  # Console only
```

Use `extra_loggers` to include third-party loggers:

```python
configure_logging(namespace="myapp", extra_loggers=["uvicorn", "fastapi"])
```

### Logging with Context

```python
from hibiki_core import get_logger, add_context_to_logger

logger = get_logger("myapp.users")
context_logger = add_context_to_logger(logger, user_id="123", path="/api/users", method="POST")
context_logger.error("User creation failed")
```

### Discord Setup

1. Create a webhook in your Discord server.
2. Encrypt the URL and store it in the `discord_notification_config` table with `notification_type = 'log'` and `is_enabled = true`.

```python
from hibiki_core.encryption import encrypt
encrypted_url = encrypt("https://discord.com/api/webhooks/...")
```

Discord error messages include the logger name, message, traceback, and any attached context (user_id, path, method).

## API Reference

### Core Functions

#### `configure_logging(namespace="app", extra_loggers=None)`

Configure console logging. Call once at app startup.

#### `setup_db_logging(session_maker, log_model, discord_config_model=None, namespace="app")`

Initialize database and optional Discord logging. Call after your database is ready.

#### `get_logger(name) -> logging.Logger`

Get a logger. If `name` matches the configured namespace, DB/Discord handlers are attached automatically.

#### `add_context_to_logger(logger, user_id=None, path=None, method=None) -> logging.LoggerAdapter`

Wrap a logger with request context that is included in DB and Discord log entries.

#### `async log_to_db(level, message, logger_name, user_id=None, path=None, method=None, trace=None)`

Manually log a message to the database (respects `LOG_DB_MIN_LEVEL`).

#### `async log_to_discord(level, message, logger_name, trace=None, user_id=None, path=None, method=None)`

Manually send a notification to Discord (respects `LOG_DISCORD_MIN_LEVEL`).

#### `async log_error(error, logger_name, message=None, user_id=None, path=None, method=None)`

Log an exception to the database with its traceback automatically extracted.

### Encryption Utilities

```python
from hibiki_core.encryption import encrypt, decrypt, generate_key

key = generate_key()
encrypted = encrypt("https://discord.com/api/webhooks/...")
original = decrypt(encrypted)
```

### Models

```python
from hibiki_core.models import (
    create_log_model,              # Factory: Log model bound to your Base
    create_discord_config_model,   # Factory: DiscordNotificationConfig model
    LOG_TABLE_SQL,                 # Raw SQL for logs table (PostgreSQL)
    DISCORD_CONFIG_TABLE_SQL,      # Raw SQL for discord_notification_config table
)
```

## Framework Integration

### FastAPI

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from hibiki_core import configure_logging, setup_db_logging, get_logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(namespace="app", extra_loggers=["uvicorn", "fastapi"])
    setup_db_logging(
        session_maker=async_session_maker,
        log_model=Log,
        namespace="app",
        discord_config_model=DiscordNotificationConfig,
    )
    yield

app = FastAPI(lifespan=lifespan)
logger = get_logger("app.routes")
```

### Django

```python
# settings.py
from hibiki_core import configure_logging
configure_logging(namespace="myproject")

# views.py
from hibiki_core import get_logger
logger = get_logger("myproject.views")
```

### Flask

```python
from hibiki_core import configure_logging, get_logger

configure_logging(namespace="myapp")
logger = get_logger("myapp.routes")
```

## Troubleshooting

**Logs not appearing in database** - Verify `setup_db_logging()` was called, your logger name matches the namespace, and `LOG_DB_MIN_LEVEL` allows the level.

**Discord notifications not sending** - Check that a row exists in `discord_notification_config` with `notification_type = 'log'` and `is_enabled = true`, and that `LOG_DISCORD_MIN_LEVEL` allows the level.

**Encryption errors** - Ensure `ENCRYPTION_KEY` is set. If you rotate the key, re-encrypt all stored webhook URLs.

## License

MIT
