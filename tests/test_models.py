import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import declarative_base

from hibiki_core.models import (
    create_log_model,
    create_discord_config_model,
    LOG_TABLE_SQL,
    DISCORD_CONFIG_TABLE_SQL,
)


class TestCreateLogModel:
    def test_creates_model_class(self):
        Base = declarative_base()
        Log = create_log_model(Base)
        assert Log.__tablename__ == "logs"

    def test_model_has_expected_columns(self):
        Base = declarative_base()
        Log = create_log_model(Base)
        mapper = inspect(Log)
        column_names = {col.key for col in mapper.columns}
        expected = {"id", "level", "message", "logger_name", "user_id", "path", "method", "trace", "created_at"}
        assert expected == column_names

    def test_model_instantiation(self):
        Base = declarative_base()
        Log = create_log_model(Base)
        entry = Log(level="ERROR", message="test", logger_name="app.test")
        assert entry.level == "ERROR"
        assert entry.message == "test"
        assert entry.logger_name == "app.test"


class TestCreateDiscordConfigModel:
    def test_creates_model_class(self):
        Base = declarative_base()
        Config = create_discord_config_model(Base)
        assert Config.__tablename__ == "discord_notification_config"

    def test_model_has_expected_columns(self):
        Base = declarative_base()
        Config = create_discord_config_model(Base)
        mapper = inspect(Config)
        column_names = {col.key for col in mapper.columns}
        expected = {
            "id", "notification_type", "webhook_url_encrypted",
            "username", "message_template", "is_enabled",
            "created_at", "updated_at",
        }
        assert expected == column_names

    def test_model_instantiation(self):
        Base = declarative_base()
        Config = create_discord_config_model(Base)
        entry = Config(
            notification_type="log",
            webhook_url_encrypted="encrypted_url",
            is_enabled=True,
        )
        assert entry.notification_type == "log"
        assert entry.is_enabled is True


class TestRawSQL:
    def test_log_table_sql_is_nonempty(self):
        assert "CREATE TABLE logs" in LOG_TABLE_SQL

    def test_discord_config_table_sql_is_nonempty(self):
        assert "CREATE TABLE discord_notification_config" in DISCORD_CONFIG_TABLE_SQL
