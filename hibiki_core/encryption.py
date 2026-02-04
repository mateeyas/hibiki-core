"""
Encryption utilities for securing Discord webhook URLs.
"""

from cryptography.fernet import Fernet
from .config import config


def encrypt(text: str) -> str:
    """
    Encrypt text using Fernet symmetric encryption.
    
    Args:
        text: Plain text to encrypt
        
    Returns:
        Encrypted text as string
        
    Raises:
        ValueError: If ENCRYPTION_KEY is not set
    """
    if not config.ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY must be set in environment or config")
    
    f = Fernet(config.ENCRYPTION_KEY.encode())
    encrypted = f.encrypt(text.encode())
    return encrypted.decode()


def decrypt(encrypted_text: str) -> str:
    """
    Decrypt text using Fernet symmetric encryption.
    
    Args:
        encrypted_text: Encrypted text to decrypt
        
    Returns:
        Decrypted plain text
        
    Raises:
        ValueError: If ENCRYPTION_KEY is not set or decryption fails
    """
    if not config.ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY must be set in environment or config")
    
    try:
        f = Fernet(config.ENCRYPTION_KEY.encode())
        decrypted = f.decrypt(encrypted_text.encode())
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt: {str(e)}")


def generate_key() -> str:
    """
    Generate a new Fernet encryption key.
    
    Returns:
        Base64-encoded encryption key
        
    Usage:
        from logging_package.encryption import generate_key
        
        key = generate_key()
        print(f"Add to .env: ENCRYPTION_KEY={key}")
    """
    return Fernet.generate_key().decode()
