# Changelog

All notable changes to Hibiki Core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-03-06

### Breaking Changes

- `configure_logging()` no longer hardcodes `uvicorn`, `app`, and `fastapi` loggers. Pass them via `extra_loggers=["uvicorn", "fastapi"]` if needed.
- `asyncpg` is no longer a required dependency. Install with `pip install hibiki-core[postgres]` if you need it.
- Removed fallback imports to `app.core.*` / `app.services.*`. The package must be installed as a standalone package.

### Added

- `namespace` parameter on `configure_logging()` and `setup_db_logging()` to control which loggers receive DB/Discord handlers (default: `"app"`).
- `extra_loggers` parameter on `configure_logging()` to configure additional third-party loggers.
- `postgres` optional dependency group (`pip install hibiki-core[postgres]`).
- `username` parameter on `send_notification_by_type()` for configurable Discord bot name.
- `require_encryption` parameter on `LoggingConfig.validate()` to make `ENCRYPTION_KEY` optional when Discord is not used.
- Basic test suite covering config, encryption, models, logger, and discord service.

### Changed

- Default Discord bot username changed from "SoundLocal Bot" to "Hibiki Bot".
- Default Discord error bot username changed from "SoundLocal Error Bot" to "Hibiki Error Bot".
- Replaced deprecated `asyncio.get_event_loop()` with `asyncio.get_running_loop()`.

### Removed

- Hardcoded `uvicorn`/`fastapi` logger configuration from `configure_logging()`.
- Fallback imports to `app.core.config`, `app.core.logger`, `app.core.encryption`, `app.services.discord_service`.
- Broken emoji avatar URL from `send_user_signup_notification()`.
- `asyncpg` from required dependencies (moved to optional `postgres` extra).
- Unused `import re` and `import json` from `discord_service.py`.
- Reference to nonexistent `REVIEW.md` from `MANIFEST.in`.
- SoundLocal-specific references from README and documentation.

### Fixed

- Stale `logging_package` references in docstrings (now `hibiki_core`).
- `LoggingConfig.validate()` no longer unconditionally requires `ENCRYPTION_KEY`.

## [1.0.0] - 2026-02-04

### Added

- Console logging with human-readable and JSON formats
- Database logging with configurable minimum level
- Discord webhook notifications for logs
- Async, non-blocking operations for DB and Discord
- Encrypted webhook URL storage
- Context support (user_id, path, method)
- Separate log level control for console, DB, and Discord
- Model factories for easy SQLAlchemy integration
- Complete documentation and examples

### Features

- **Console Logging**: Standard output with environment-based formatting
- **Database Logging**: PostgreSQL storage via SQLAlchemy with async support
- **Discord Notifications**: Webhook-based notifications with rich formatting
- **Security**: Fernet encryption for webhook URLs
- **Flexibility**: Optional Discord support, configurable log levels
- **Production Ready**: Battle-tested in production environments

[2.0.0]: https://github.com/mateeyas/hibiki-core/releases/tag/v2.0.0
[1.0.0]: https://github.com/mateeyas/hibiki-core/releases/tag/v1.0.0
