import pytest
from hibiki_core.encryption import encrypt, decrypt, generate_key
from hibiki_core.config import LoggingConfig


class TestGenerateKey:
    def test_returns_string(self):
        key = generate_key()
        assert isinstance(key, str)

    def test_key_is_valid_fernet_key(self):
        from cryptography.fernet import Fernet
        key = generate_key()
        Fernet(key.encode())

    def test_generates_unique_keys(self):
        key1 = generate_key()
        key2 = generate_key()
        assert key1 != key2


class TestEncryptDecrypt:
    @pytest.fixture(autouse=True)
    def setup_key(self, monkeypatch):
        key = generate_key()
        monkeypatch.setattr(LoggingConfig, "ENCRYPTION_KEY", key)

    def test_round_trip(self):
        original = "https://discord.com/api/webhooks/123/abc"
        encrypted = encrypt(original)
        assert encrypted != original
        assert decrypt(encrypted) == original

    def test_encrypt_returns_string(self):
        result = encrypt("test")
        assert isinstance(result, str)

    def test_different_encryptions_differ(self):
        text = "same text"
        enc1 = encrypt(text)
        enc2 = encrypt(text)
        # Fernet uses random IV, so encryptions of the same text should differ
        assert enc1 != enc2


class TestEncryptWithoutKey:
    def test_encrypt_raises_without_key(self, monkeypatch):
        monkeypatch.setattr(LoggingConfig, "ENCRYPTION_KEY", None)
        with pytest.raises(ValueError, match="ENCRYPTION_KEY"):
            encrypt("test")

    def test_decrypt_raises_without_key(self, monkeypatch):
        monkeypatch.setattr(LoggingConfig, "ENCRYPTION_KEY", None)
        with pytest.raises(ValueError, match="ENCRYPTION_KEY"):
            decrypt("test")
