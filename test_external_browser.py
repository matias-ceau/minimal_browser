#!/usr/bin/env python3
"""Simple test script to validate external browser functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from minimal_browser.config.default_config import BrowserConfig, load_config
from minimal_browser.browser.external import ExternalBrowserManager, BrowserCache

def test_config_loading():
    """Test that configuration loads properly."""
    print("Testing configuration loading...")
    config = load_config()
    print(f"✓ Config loaded: {type(config)}")
    print(f"  - Default browser: {config.browser.default_external_browser}")
    print(f"  - Preferred browsers: {config.browser.preferred_browsers}")
    print(f"  - Cache enabled: {config.browser.cache_browser_detection}")
    print()

def test_browser_cache():
    """Test browser cache functionality."""
    print("Testing browser cache...")
    cache = BrowserCache(cache_ttl=1.0)  # Short TTL for testing
    
    # Test caching
    assert cache.is_browser_available("firefox") is None
    cache.cache_browser_availability("firefox", True)
    assert cache.is_browser_available("firefox") is True
    
    # Test failure tracking
    assert not cache.is_browser_unhealthy("chrome")
    cache.record_browser_failure("chrome")
    cache.record_browser_failure("chrome")
    cache.record_browser_failure("chrome")
    assert cache.is_browser_unhealthy("chrome")
    
    print("✓ Browser cache tests passed")
    print()

def test_browser_manager():
    """Test external browser manager."""
    print("Testing external browser manager...")
    config = BrowserConfig()
    manager = ExternalBrowserManager(config)
    
    # Test browser detection
    browsers = manager.detect_available_browsers()
    print(f"  - Detected browsers: {browsers}")
    
    # Test browser info
    info = manager.get_browser_info()
    print(f"  - Browser info: {info}")
    
    # Test URL validation (without actually opening browsers)
    success, message = manager.open_url("data:text/html,test")
    assert not success
    assert "data URL" in message.lower()
    print(f"  - Data URL protection: ✓ {message}")
    
    print("✓ Browser manager tests passed")
    print()

def main():
    """Run all tests."""
    print("=== External Browser Integration Tests ===\n")
    
    try:
        test_config_loading()
        test_browser_cache()
        test_browser_manager()
        
        print("🎉 All tests passed!")
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())