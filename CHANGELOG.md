# Changelog

All notable changes to Hibiki Core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.0.0]: https://github.com/yourusername/hibiki-core/releases/tag/v1.0.0
