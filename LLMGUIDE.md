# Hibiki Core -- AI Reference Guide

> This document is designed to be provided to AI coding assistants as context when working with or integrating the `hibiki-core` package. It covers architecture, API surface, initialization requirements, and common pitfalls.

## What is hibiki-core?

Hibiki Core (v2.0.0) is a Python 3.10+ logging library that routes log messages to three destinations: **console**, **PostgreSQL** (or any SQLAlchemy-supported database), and **Discord** (via webhooks). All DB and Discord I/O is async and non-blocking. Discord webhook URLs are encrypted at rest with Fernet.

## Module Map

```
hibiki_core/
├── __init__.py          # Public API -- 7 exported functions
├── logger.py            # Core: configure_logging, setup_db_logging, get_logger, AsyncDBHandler
├── config.py            # LoggingConfig -- reads env vars
├── models.py            # SQLAlchemy model factories + raw SQL constants
├── encryption.py        # Fernet encrypt/decrypt/generate_key
└── discord_service.py   # Discord webhook helpers
```

**Dependency flow:** `config` feeds into `logger`. `logger` imports `encryption` and `discord_service` lazily at send time. `models` is independent and consumed by the host application.

## Initialization Sequence (REQUIRED)

Initialization is a **two-step process** that must happen in order:

```python
from hibiki_core import configure_logging, setup_db_logging, get_logger
from hibiki_core.models import create_log_model, create_discord_config_model
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

Base = declarative_base()
Log = create_log_model(Base)
DiscordNotificationConfig = create_discord_config_model(Base)

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Step 1: Console logging + set namespace
configure_logging(namespace="myapp")

# Step 2: DB + optional Discord logging (call AFTER engine/session are ready)
setup_db_logging(
    session_maker=session_maker,
    log_model=Log,
    namespace="myapp",
    discord_config_model=DiscordNotificationConfig,  # omit to disable Discord
)
```

**Rules:**
- `configure_logging` must be called before `setup_db_logging`.
- `setup_db_logging` must be called after the database engine and session maker are created.
- The `namespace` argument must be the same in both calls.
- Omit `discord_config_model` to disable Discord integration entirely.

## Namespace Convention

The namespace controls which loggers receive DB and Discord handlers. Only loggers whose name equals or starts with `namespace + "."` get those handlers.

```python
configure_logging(namespace="myapp")
setup_db_logging(session_maker=..., log_model=..., namespace="myapp")

get_logger("myapp")          # DB + Discord + console
get_logger("myapp.api")      # DB + Discord + console
get_logger("myapp.api.auth") # DB + Discord + console
get_logger("other.module")   # console ONLY
```

To include third-party loggers in console configuration (not DB/Discord):

```python
configure_logging(namespace="myapp", extra_loggers=["uvicorn", "fastapi"])
```

## Public API Reference

### Top-level exports (`from hibiki_core import ...`)

| Function | Signature | Description |
|----------|-----------|-------------|
| `configure_logging` | `(namespace="app", extra_loggers=None)` | Configure console logging and set the logger namespace. Call once at startup. |
| `setup_db_logging` | `(session_maker, log_model, discord_config_model=None, namespace="app")` | Initialize DB and optional Discord logging. Call after DB is ready. |
| `get_logger` | `(name: str) -> logging.Logger` | Get a logger. Attaches DB/Discord handlers if name matches namespace. |
| `add_context_to_logger` | `(logger, user_id=None, path=None, method=None) -> LoggerAdapter` | Wrap a logger with request context (stored in DB and Discord entries). |
| `log_to_db` | `async (level, message, logger_name, user_id?, path?, method?, trace?)` | Manually write a log entry to the database. Respects `LOG_DB_MIN_LEVEL`. |
| `log_to_discord` | `async (level, message, logger_name, trace?, user_id?, path?, method?)` | Manually send a Discord notification. Respects `LOG_DISCORD_MIN_LEVEL`. |
| `log_error` | `async (error, logger_name, message?, user_id?, path?, method?)` | Log an exception to DB with auto-extracted traceback. |

### Models (`from hibiki_core.models import ...`)

| Export | Type | Description |
|--------|------|-------------|
| `create_log_model(Base)` | Factory function | Returns a `Log` SQLAlchemy model bound to the given `Base`. Table: `logs`. |
| `create_discord_config_model(Base)` | Factory function | Returns a `DiscordNotificationConfig` model. Table: `discord_notification_config`. |
| `LOG_TABLE_SQL` | `str` | Raw PostgreSQL DDL for the `logs` table (alternative to the model factory). |
| `DISCORD_CONFIG_TABLE_SQL` | `str` | Raw PostgreSQL DDL for the `discord_notification_config` table. |

### Encryption (`from hibiki_core.encryption import ...`)

| Function | Signature | Description |
|----------|-----------|-------------|
| `encrypt` | `(text: str) -> str` | Encrypt plaintext with Fernet. Requires `ENCRYPTION_KEY` env var. |
| `decrypt` | `(encrypted_text: str) -> str` | Decrypt ciphertext. Requires `ENCRYPTION_KEY`. |
| `generate_key` | `() -> str` | Generate a new Fernet key (base64-encoded string). |

### Discord Service (`from hibiki_core.discord_service import ...`)

| Function | Signature | Description |
|----------|-----------|-------------|
| `send_discord_notification` | `async (message, webhook_url, username?, avatar_url?) -> bool` | Send a plain message to a Discord webhook. |
| `send_error_notification` | `async (level, message, logger_name, webhook_url, username?, trace?, user_id?, path?, method?) -> bool` | Send a formatted error notification. |
| `send_user_signup_notification` | `async (email, webhook_url, message_template?, username?) -> bool` | Send a signup notification (email is auto-anonymized). |
| `send_notification_by_type` | `async (notification_type, webhook_url, message_template, username?, **template_vars) -> bool` | Send a templated notification. Emails in `template_vars` are auto-anonymized. |
| `anonymize_email` | `(email: str) -> str` | Anonymize an email: `john.doe@example.com` -> `j***.d***@example.com`. |

## Model Factory Pattern

Models are created via factory functions so they bind to the host application's SQLAlchemy `Base`:

```python
from sqlalchemy.orm import declarative_base
from hibiki_core.models import create_log_model, create_discord_config_model

Base = declarative_base()
Log = create_log_model(Base)
DiscordNotificationConfig = create_discord_config_model(Base)
```

The `Log` model has columns: `id` (UUID string), `level`, `message`, `logger_name`, `user_id`, `path`, `method`, `trace`, `created_at`.

The `DiscordNotificationConfig` model has columns: `id`, `notification_type`, `webhook_url_encrypted`, `username`, `message_template`, `is_enabled`, `created_at`, `updated_at`.

If you don't use SQLAlchemy, use the raw SQL constants `LOG_TABLE_SQL` and `DISCORD_CONFIG_TABLE_SQL` instead.

## Async Behavior

`AsyncDBHandler` is a `logging.Handler` subclass. When its `emit()` method fires:

1. It checks for a running asyncio event loop via `asyncio.get_running_loop()`.
2. It creates background `asyncio.Task`s for `log_to_db()` and (if level is high enough) `log_to_discord()`.
3. Tasks are fire-and-forget -- the logging call returns immediately.
4. If no event loop is running, it falls back to printing the log to stdout.

**When calling `log_to_db`, `log_to_discord`, or `log_error` directly**, they are `async` functions and must be awaited:

```python
await log_to_db(level="ERROR", message="something broke", logger_name="myapp.api")
await log_error(error=exc, logger_name="myapp.api", user_id="123")
```

Using `logger.error(...)` via `get_logger` does NOT require await -- the handler manages async internally.

## Configuration via Environment Variables

| Variable | Default | Effect |
|----------|---------|--------|
| `ENV` | `development` | `production` switches console to JSON format and ERROR-only level. |
| `LOG_DB_MIN_LEVEL` | `WARNING` | Minimum level for database logging. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `LOG_DISCORD_MIN_LEVEL` | `ERROR` | Minimum level for Discord notifications. Same options. |
| `ENCRYPTION_KEY` | *(none)* | Fernet key for encrypting/decrypting Discord webhook URLs. Required if using Discord. Generate with `generate_key()`. |

Config is read at import time by `hibiki_core.config.LoggingConfig` and re-read when `setup_db_logging` is called.

## Discord Integration

Discord logging is optional. To enable it:

1. Pass `discord_config_model` to `setup_db_logging`.
2. Insert a row into `discord_notification_config` with `notification_type='log'`, `is_enabled=True`, and an encrypted webhook URL.
3. Set the `ENCRYPTION_KEY` env var.

```python
from hibiki_core.encryption import encrypt, generate_key

key = generate_key()  # set this as ENCRYPTION_KEY in your environment
encrypted_url = encrypt("https://discord.com/api/webhooks/...")
# Store encrypted_url in discord_notification_config.webhook_url_encrypted
```

At send time, the handler queries `discord_notification_config` for enabled configs with `notification_type='log'`, decrypts the URL, and sends the notification.

## Framework Integration Patterns

### FastAPI

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from hibiki_core import configure_logging, setup_db_logging, get_logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(namespace="myapp", extra_loggers=["uvicorn", "fastapi"])
    setup_db_logging(
        session_maker=async_session_maker,
        log_model=Log,
        namespace="myapp",
        discord_config_model=DiscordNotificationConfig,
    )
    yield

app = FastAPI(lifespan=lifespan)
logger = get_logger("myapp.routes")
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

## Common Mistakes to Avoid

| Mistake | Why it fails | Fix |
|---------|-------------|-----|
| Namespace mismatch between `configure_logging` and `get_logger` | Logger won't get DB/Discord handlers | Use the same namespace prefix everywhere |
| Calling `setup_db_logging` before engine is created | Session maker doesn't work | Call in FastAPI lifespan, Django `AppConfig.ready()`, etc. |
| Skipping `configure_logging` entirely | No console handlers, namespace defaults to `"app"` | Always call it first |
| Using `__name__` as logger name when module path doesn't start with namespace | Logger gets console only | Use `get_logger("myapp.modulename")` explicitly |
| Calling `log_to_db(...)` without `await` | Coroutine is created but never executed | Use `await log_to_db(...)` or just use `logger.error(...)` which handles async internally |
| Forgetting `ENCRYPTION_KEY` when using Discord | `ValueError` at decrypt time | Set the env var; generate with `generate_key()` |

## Testing Conventions

- Call `reset_db_handler()` (from `hibiki_core.logger`) between tests to clear the global DB handler singleton.
- Use `monkeypatch.setenv` for environment variables and `importlib.reload(config_module)` to pick up changes.
- Mock `aiohttp.ClientSession` for Discord tests to avoid real HTTP calls.
- Tests use `pytest` with `asyncio_mode = "strict"`.

```python
from hibiki_core.logger import reset_db_handler

@pytest.fixture(autouse=True)
def clean_handler():
    reset_db_handler()
    yield
    reset_db_handler()
```
