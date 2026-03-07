import os
import importlib
import pytest
from hibiki_core.config import LoggingConfig, config
import hibiki_core.config as config_module


@pytest.fixture(autouse=True)
def restore_config(monkeypatch):
    """Reset environment variables and reload config_module after each test."""
    yield
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("LOG_DB_MIN_LEVEL", raising=False)
    monkeypatch.delenv("LOG_DISCORD_MIN_LEVEL", raising=False)
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    importlib.reload(config_module)


class TestLoggingConfigDefaults:
    def test_default_environment(self, monkeypatch):
        monkeypatch.delenv("ENV", raising=False)
        importlib.reload(config_module)
        assert config_module.config.ENVIRONMENT == "development"

    def test_custom_environment(self, monkeypatch):
        monkeypatch.setenv("ENV", "production")
        importlib.reload(config_module)
        assert config_module.config.ENVIRONMENT == "production"

    def test_default_db_min_level(self, monkeypatch):
        monkeypatch.delenv("LOG_DB_MIN_LEVEL", raising=False)
        importlib.reload(config_module)
        assert config_module.config.LOG_DB_MIN_LEVEL == "WARNING"

    def test_custom_db_min_level(self, monkeypatch):
        monkeypatch.setenv("LOG_DB_MIN_LEVEL", "DEBUG")
        importlib.reload(config_module)
        assert config_module.config.LOG_DB_MIN_LEVEL == "DEBUG"

    def test_default_discord_min_level(self, monkeypatch):
        monkeypatch.delenv("LOG_DISCORD_MIN_LEVEL", raising=False)
        importlib.reload(config_module)
        assert config_module.config.LOG_DISCORD_MIN_LEVEL == "ERROR"

    def test_custom_discord_min_level(self, monkeypatch):
        monkeypatch.setenv("LOG_DISCORD_MIN_LEVEL", "WARNING")
        importlib.reload(config_module)
        assert config_module.config.LOG_DISCORD_MIN_LEVEL == "WARNING"

    def test_encryption_key_optional_by_default(self, monkeypatch):
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        importlib.reload(config_module)
        assert config_module.config.ENCRYPTION_KEY is None

    def test_encryption_key_when_set(self, monkeypatch):
        monkeypatch.setenv("ENCRYPTION_KEY", "my-secret-key")
        importlib.reload(config_module)
        assert config_module.config.ENCRYPTION_KEY == "my-secret-key"


class TestLoggingConfigValidate:
    def test_validate_raises_when_key_missing(self, monkeypatch):
        monkeypatch.setattr(LoggingConfig, "ENCRYPTION_KEY", None)
        with pytest.raises(ValueError, match="ENCRYPTION_KEY"):
            LoggingConfig.validate(require_encryption=True)

    def test_validate_skips_when_not_required(self, monkeypatch):
        monkeypatch.setattr(LoggingConfig, "ENCRYPTION_KEY", None)
        LoggingConfig.validate(require_encryption=False)

    def test_validate_passes_when_key_set(self, monkeypatch):
        monkeypatch.setattr(LoggingConfig, "ENCRYPTION_KEY", "test-key")
        LoggingConfig.validate(require_encryption=True)


class TestLoggingConfigFromDict:
    def test_from_dict_sets_attributes(self):
        LoggingConfig.from_dict({
            "LOG_DB_MIN_LEVEL": "DEBUG",
            "LOG_DISCORD_MIN_LEVEL": "WARNING",
        })
        assert LoggingConfig.LOG_DB_MIN_LEVEL == "DEBUG"
        assert LoggingConfig.LOG_DISCORD_MIN_LEVEL == "WARNING"
        # Reset
        LoggingConfig.LOG_DB_MIN_LEVEL = "WARNING"
        LoggingConfig.LOG_DISCORD_MIN_LEVEL = "ERROR"

    def test_from_dict_ignores_unknown_keys(self):
        LoggingConfig.from_dict({"UNKNOWN_KEY": "value"})
