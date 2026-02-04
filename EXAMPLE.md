# Integration Examples

Examples of integrating the logging package into different frameworks.

## FastAPI Integration

```python
# main.py
from fastapi import FastAPI
from hibiki_core import configure_logging, setup_db_logging, get_logger
from hibiki_core.models import create_log_model, create_discord_config_model
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Create Base and models
Base = declarative_base()
Log = create_log_model(Base)
DiscordNotificationConfig = create_discord_config_model(Base)

# Create database engine and session
engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
async_session_maker = async_sessionmaker(engine, class_=AsyncSession)

app = FastAPI()

@app.on_event("startup")
async def startup():
    # 1. Configure console logging
    configure_logging()

    # 2. Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 3. Setup DB and Discord logging
    setup_db_logging(
        session_maker=async_session_maker,
        log_model=Log,
        discord_config_model=DiscordNotificationConfig  # Include for Discord support
    )

    logger = get_logger(__name__)
    logger.info("Application started successfully")

# Use in your routes
@app.get("/")
async def root():
    logger = get_logger(__name__)
    logger.info("Root endpoint accessed")
    return {"message": "Hello"}

@app.get("/error")
async def trigger_error():
    logger = get_logger(__name__)
    try:
        1 / 0
    except Exception as e:
        logger.error("Division by zero", exc_info=True)
        # This logs to: console, database, and Discord (if configured)
        raise
```

## Without Discord Notifications

If you only want console and database logging (no Discord):

```python
# Setup without discord_config_model
setup_db_logging(
    session_maker=async_session_maker,
    log_model=Log
    # discord_config_model omitted - Discord notifications disabled
)
```

## With Request Context

```python
from fastapi import Request
from hibiki_core import get_logger, add_context_to_logger

@app.post("/users")
async def create_user(request: Request, user_data: dict):
    logger = get_logger(__name__)

    # Add request context
    context_logger = add_context_to_logger(
        logger,
        user_id=user_data.get("id"),
        path=str(request.url.path),
        method=request.method
    )

    try:
        # ... create user logic ...
        context_logger.info("User created successfully")
    except Exception as e:
        context_logger.error(f"User creation failed: {str(e)}", exc_info=True)
        # Discord notification will include user_id, path, and method
        raise
```

## Minimal Setup (Database Only)

```python
from hibiki_core import configure_logging, setup_db_logging, get_logger
from logging_package.models import create_log_model

Base = declarative_base()
Log = create_log_model(Base)

configure_logging()
setup_db_logging(
    session_maker=async_session_maker,
    log_model=Log
    # No discord_config_model = no Discord notifications
)

logger = get_logger(__name__)
logger.error("This goes to console and database only")
```

## Full Setup (All Features)

```python
from hibiki_core import configure_logging, setup_db_logging, get_logger
from hibiki_core.models import create_log_model, create_discord_config_model

Base = declarative_base()
Log = create_log_model(Base)
DiscordNotificationConfig = create_discord_config_model(Base)

# Create tables
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

# Initialize logging
configure_logging()
setup_db_logging(
    session_maker=async_session_maker,
    log_model=Log,
    discord_config_model=DiscordNotificationConfig
)

# Then configure Discord webhook via API or database
# See README.md for Discord setup instructions

logger = get_logger(__name__)
logger.error("This goes to console, database, and Discord!")
```
