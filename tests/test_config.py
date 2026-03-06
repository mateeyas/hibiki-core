import os
import pytest
from hibiki_core.config import LoggingConfig, config


class TestLoggingConfigDefaults:
    def test_default_environment(self):
        assert config.ENVIRONMENT == os.getenv("ENV", "development")

    def test_default_db_min_level(self):
        assert config.LOG_DB_MIN_LEVEL == os.getenv("LOG_DB_MIN_LEVEL", "WARNING")

    def test_default_discord_min_level(self):
        assert config.LOG_DISCORD_MIN_LEVEL == os.getenv("LOG_DISCORD_MIN_LEVEL", "ERROR")

    def test_encryption_key_optional_by_default(self):
        # ENCRYPTION_KEY should be None if not set in environment
        if "ENCRYPTION_KEY" not in os.environ:
            assert config.ENCRYPTION_KEY is None


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
