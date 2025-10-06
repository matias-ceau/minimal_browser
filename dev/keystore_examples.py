"""
Password Store Integration - Usage Examples

This file demonstrates how to use the system keychain integration
for secure API key management in Minimal Browser.
"""

from minimal_browser.ai.auth import auth_manager
from minimal_browser.storage.keystore import keystore

# Example 1: Check if keyring is available
# =========================================
print(f"System keychain available: {keystore.available}")


# Example 2: Store API key in system keychain
# ============================================
# This stores the key securely in:
# - GNOME Keyring (Linux)
# - macOS Keychain (macOS)  
# - Windows Credential Manager (Windows)

auth_manager.set_key(
    provider='openrouter',
    key='sk-or-v1-your-api-key-here',
    store_in_keychain=True  # Persists across sessions
)


# Example 3: Check available keys
# ================================
print(f"Providers with keys: {auth_manager.list_providers()}")
print(f"Keys in keychain: {auth_manager.list_keychain_providers()}")


# Example 4: Get API key
# ======================
# This automatically loads from the highest priority source:
# 1. Environment variable (OPENROUTER_API_KEY)
# 2. System keychain
# 3. Runtime-set key

api_key = auth_manager.get_key('openrouter')
if api_key:
    print(f"OpenRouter key available: {api_key[:10]}...")
else:
    print("No OpenRouter key found")


# Example 5: Delete key from keychain
# ====================================
# Remove from runtime AND keychain
auth_manager.delete_key(
    provider='openrouter',
    delete_from_keychain=True
)


# Example 6: Store multiple provider keys
# ========================================
providers = {
    'openrouter': 'sk-or-v1-...',
    'openai': 'sk-...',
    'anthropic': 'sk-ant-...',
}

for provider, key in providers.items():
    auth_manager.set_key(provider, key, store_in_keychain=True)
    print(f"Stored {provider} key in keychain")


# Example 7: Using environment variables (traditional method)
# ===========================================================
# Set in your shell before running the browser:
#   export OPENROUTER_API_KEY="sk-or-v1-..."
#   python -m minimal_browser
#
# Environment variables take precedence over keychain storage,
# so you can temporarily override stored keys.


# Example 8: Configuration preferences
# =====================================
from minimal_browser.config.default_config import load_config

config = load_config()
security = config.security

print(f"Use system keychain: {security.use_system_keychain}")
print(f"Prefer env over keychain: {security.prefer_env_over_keychain}")

# You can modify these in ~/.config/minimal_browser/config.toml:
# [security]
# use_system_keychain = true
# prefer_env_over_keychain = true
