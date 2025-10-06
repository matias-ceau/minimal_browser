"""Secure password/API key storage using system keychains."""

from __future__ import annotations

import logging
from typing import Optional

try:
    import keyring
    from keyring.errors import KeyringError
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    KeyringError = Exception  # type: ignore

logger = logging.getLogger(__name__)

SERVICE_NAME = "minimal_browser"


class KeyStore:
    """Cross-platform keychain integration for secure credential storage.
    
    Supports:
    - GNOME Keyring (Linux)
    - macOS Keychain
    - Windows Credential Manager
    """
    
    def __init__(self):
        """Initialize keystore with availability check."""
        self._available = KEYRING_AVAILABLE
        if not self._available:
            logger.warning(
                "Keyring library not available. Install with: pip install keyring"
            )
    
    @property
    def available(self) -> bool:
        """Check if keyring backend is available."""
        return self._available
    
    def store_key(self, provider: str, api_key: str) -> bool:
        """Store API key in system keychain.
        
        Args:
            provider: Provider name (e.g., 'openrouter', 'openai', 'anthropic')
            api_key: The API key to store securely
            
        Returns:
            True if successful, False otherwise
        """
        if not self._available:
            logger.debug("Keyring not available, cannot store key")
            return False
        
        try:
            keyring.set_password(SERVICE_NAME, provider, api_key)
            logger.info(f"Successfully stored {provider} key in system keychain")
            return True
        except KeyringError as e:
            logger.error(f"Failed to store {provider} key: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error storing {provider} key: {e}")
            return False
    
    def get_key(self, provider: str) -> Optional[str]:
        """Retrieve API key from system keychain.
        
        Args:
            provider: Provider name (e.g., 'openrouter', 'openai', 'anthropic')
            
        Returns:
            API key if found, None otherwise
        """
        if not self._available:
            logger.debug("Keyring not available, cannot retrieve key")
            return None
        
        try:
            key = keyring.get_password(SERVICE_NAME, provider)
            if key:
                logger.debug(f"Retrieved {provider} key from system keychain")
            return key
        except KeyringError as e:
            logger.error(f"Failed to retrieve {provider} key: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving {provider} key: {e}")
            return None
    
    def delete_key(self, provider: str) -> bool:
        """Delete API key from system keychain.
        
        Args:
            provider: Provider name (e.g., 'openrouter', 'openai', 'anthropic')
            
        Returns:
            True if successful, False otherwise
        """
        if not self._available:
            logger.debug("Keyring not available, cannot delete key")
            return False
        
        try:
            keyring.delete_password(SERVICE_NAME, provider)
            logger.info(f"Successfully deleted {provider} key from system keychain")
            return True
        except KeyringError as e:
            logger.warning(f"Failed to delete {provider} key: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting {provider} key: {e}")
            return False
    
    def list_stored_providers(self) -> list[str]:
        """List providers with keys stored in keychain.
        
        Note: This is a best-effort approach as keyring doesn't provide
        a native list function. We check known providers.
        
        Returns:
            List of provider names that have stored keys
        """
        if not self._available:
            return []
        
        known_providers = ['openrouter', 'openai', 'anthropic']
        stored = []
        
        for provider in known_providers:
            if self.get_key(provider):
                stored.append(provider)
        
        return stored


# Global keystore instance
keystore = KeyStore()
