"""AI authentication and API key management"""

import os
from typing import Optional, Dict


class AuthManager:
    """Manages API keys and authentication for AI providers"""
    
    def __init__(self):
        self._api_keys: Dict[str, str] = {}
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from environment variables"""
        # OpenRouter
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if openrouter_key:
            self._api_keys['openrouter'] = openrouter_key
        
        # OpenAI (direct)
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self._api_keys['openai'] = openai_key
        
        # Anthropic (direct)
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            self._api_keys['anthropic'] = anthropic_key
    
    def get_key(self, provider: str) -> Optional[str]:
        """Get API key for provider"""
        return self._api_keys.get(provider)
    
    def has_key(self, provider: str) -> bool:
        """Check if API key exists for provider"""
        return provider in self._api_keys
    
    def set_key(self, provider: str, key: str):
        """Set API key for provider (runtime only)"""
        self._api_keys[provider] = key
    
    def list_providers(self) -> list[str]:
        """List providers with available keys"""
        return list(self._api_keys.keys())
    
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