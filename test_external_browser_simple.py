#!/usr/bin/env python3
"""Simple test script to validate external browser functionality (no UI dependencies)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test only the components that don't require PySide6
from minimal_browser.browser.external import BrowserCache

def test_browser_cache():
    """Test browser cache functionality."""
    print("Testing browser cache...")
    cache = BrowserCache(cache_ttl=1.0)  # Short TTL for testing
    
    # Test initial state
    assert cache.is_browser_available("firefox") is None
    print("  ✓ Initial cache state is None")
    
    # Test caching availability
    cache.cache_browser_availability("firefox", True)
    assert cache.is_browser_available("firefox") is True
    print("  ✓ Browser availability caching works")
    
    cache.cache_browser_availability("chrome", False)
    assert cache.is_browser_available("chrome") is False
    print("  ✓ Browser unavailability caching works")
    
    # Test failure tracking
    assert not cache.is_browser_unhealthy("safari")
    print("  ✓ Initial health state is healthy")
    
    # Add some failures
    cache.record_browser_failure("safari")
    cache.record_browser_failure("safari")
    assert not cache.is_browser_unhealthy("safari")  # Still under threshold
    print("  ✓ Browser health tracking under threshold")
    
    cache.record_browser_failure("safari")  # This should make it unhealthy
    assert cache.is_browser_unhealthy("safari")
    print("  ✓ Browser health tracking over threshold")
    
    print("✓ Browser cache tests passed")
    print()

def test_config_structure():
    """Test that we can import and instantiate config classes."""
    print("Testing configuration structure...")
    
    # Test config class loading without full instantiation
    try:
        from minimal_browser.config.default_config import BrowserConfig
        
        # Create a test config
        config = BrowserConfig()
        
        # Test default values
        assert config.headless is False
        assert config.window_size == (1280, 720)
        assert config.default_external_browser is None
        assert "firefox" in config.preferred_browsers
        assert config.cache_browser_detection is True
        
        print("  ✓ BrowserConfig defaults are correct")
        print(f"  ✓ Preferred browsers: {config.preferred_browsers}")
        print(f"  ✓ Cache detection: {config.cache_browser_detection}")
        
        print("✓ Configuration structure tests passed")
        print()
        
    except ImportError as e:
        print(f"  ⚠ Config import failed (expected in some environments): {e}")
        print()

def main():
    """Run all tests."""
    print("=== External Browser Integration Tests (Simple) ===\n")
    
    try:
        test_browser_cache()
        test_config_structure()
        
        print("🎉 All simple tests passed!")
        print("\nNote: Full integration tests require PySide6 and would test:")
        print("- Browser detection and launching")
        print("- UI integration with keybindings")
        print("- Configuration file loading")
        print("- Full ExternalBrowserManager functionality")
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())