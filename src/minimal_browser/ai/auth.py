"""AI authentication and API key management"""

import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages API keys and authentication for AI providers.
    
    Priority order for loading keys:
    1. Environment variables (highest priority)
    2. System keychain (GNOME Keyring/macOS Keychain/Windows Credential Manager)
    3. Runtime set keys (lowest priority)
    """
    
    def __init__(self):
        self._api_keys: Dict[str, str] = {}
        self._keystore = None
        self._init_keystore()
        self._load_keys()
    
    def _init_keystore(self):
        """Initialize keystore integration."""
        try:
            from ..storage.keystore import keystore
            self._keystore = keystore
            if self._keystore.available:
                logger.info("System keychain integration available")
            else:
                logger.info("System keychain not available, using environment variables only")
        except ImportError as e:
            logger.warning(f"Failed to import keystore: {e}")
            self._keystore = None
    
    def _load_keys(self):
        """Load API keys from environment variables and system keychain.
        
        Environment variables take precedence over keychain storage.
        """
        providers = ['openrouter', 'openai', 'anthropic']
        env_var_map = {
            'openrouter': 'OPENROUTER_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
        }
        
        for provider in providers:
            # Try environment variable first
            env_var = env_var_map.get(provider)
            if env_var:
                env_key = os.getenv(env_var)
                if env_key:
                    self._api_keys[provider] = env_key
                    logger.debug(f"Loaded {provider} key from environment")
                    continue
            
            # Fall back to keychain if available
            if self._keystore and self._keystore.available:
                keychain_key = self._keystore.get_key(provider)
                if keychain_key:
                    self._api_keys[provider] = keychain_key
                    logger.debug(f"Loaded {provider} key from system keychain")
    
    def get_key(self, provider: str) -> Optional[str]:
        """Get API key for provider"""
        return self._api_keys.get(provider)
    
    def has_key(self, provider: str) -> bool:
        """Check if API key exists for provider"""
        return provider in self._api_keys
    
    def set_key(self, provider: str, key: str, store_in_keychain: bool = False):
        """Set API key for provider.
        
        Args:
            provider: Provider name (e.g., 'openrouter', 'openai', 'anthropic')
            key: The API key
            store_in_keychain: If True, also store in system keychain for persistence
        """
        self._api_keys[provider] = key
        
        if store_in_keychain and self._keystore and self._keystore.available:
            success = self._keystore.store_key(provider, key)
            if success:
                logger.info(f"Stored {provider} key in system keychain")
            else:
                logger.warning(f"Failed to store {provider} key in system keychain")
    
    def delete_key(self, provider: str, delete_from_keychain: bool = False) -> bool:
        """Delete API key for provider.
        
        Args:
            provider: Provider name
            delete_from_keychain: If True, also delete from system keychain
            
        Returns:
            True if key was deleted, False if not found
        """
        removed = False
        if provider in self._api_keys:
            del self._api_keys[provider]
            removed = True
        
        if delete_from_keychain and self._keystore and self._keystore.available:
            self._keystore.delete_key(provider)
        
        return removed
    
    def list_providers(self) -> list[str]:
        """List providers with available keys"""
        return list(self._api_keys.keys())
    
    def list_keychain_providers(self) -> list[str]:
        """List providers with keys stored in system keychain.
        
        Returns:
            List of provider names with keys in keychain, or empty list if unavailable
        """
        if self._keystore and self._keystore.available:
            return self._keystore.list_stored_providers()
        return []
    
    def validate_key(self, provider: str) -> bool:
        """Validate API key format (basic check)"""
        key = self.get_key(provider)
        if not key:
            return False
        
        # Basic validation
        if provider == 'openrouter':
            return key.startswith('sk-or-') and len(key) > 20
        elif provider == 'openai':
            return key.startswith('sk-') and len(key) > 20
        elif provider == 'anthropic':
            return key.startswith('sk-ant-') and len(key) > 20
        
        return len(key) > 10  # Generic fallback


# Global auth manager instance
auth_manager = AuthManager()