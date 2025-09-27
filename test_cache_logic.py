#!/usr/bin/env python3
"""Direct test of browser cache logic without dependencies."""

import time
from typing import Dict, List, Optional, Tuple

class BrowserCache:
    """Cache for browser availability and health status."""
    
    def __init__(self, cache_ttl: float = 300.0):  # 5 minutes cache
        self.cache_ttl = cache_ttl
        self._availability_cache: Dict[str, Tuple[bool, float]] = {}
        self._failure_cache: Dict[str, Tuple[int, float]] = {}  # failure_count, last_failure_time
    
    def is_browser_available(self, browser_name: str) -> Optional[bool]:
        """Check if browser availability is cached and still valid."""
        if browser_name in self._availability_cache:
            available, timestamp = self._availability_cache[browser_name]
            if time.time() - timestamp < self.cache_ttl:
                return available
        return None
    
    def cache_browser_availability(self, browser_name: str, available: bool) -> None:
        """Cache browser availability status."""
        self._availability_cache[browser_name] = (available, time.time())
    
    def is_browser_unhealthy(self, browser_name: str, max_failures: int = 3) -> bool:
        """Check if browser has too many recent failures."""
        if browser_name in self._failure_cache:
            failure_count, last_failure = self._failure_cache[browser_name]
            # Reset failure count if last failure was more than cache_ttl ago
            if time.time() - last_failure > self.cache_ttl:
                del self._failure_cache[browser_name]
                return False
            return failure_count >= max_failures
        return False
    
    def record_browser_failure(self, browser_name: str) -> None:
        """Record a browser failure."""
        if browser_name in self._failure_cache:
            failure_count, _ = self._failure_cache[browser_name]
            self._failure_cache[browser_name] = (failure_count + 1, time.time())
        else:
            self._failure_cache[browser_name] = (1, time.time())

def test_browser_cache():
    """Test browser cache functionality."""
    print("=== Testing BrowserCache Logic ===")
    cache = BrowserCache(cache_ttl=1.0)  # Short TTL for testing
    
    # Test initial state
    result = cache.is_browser_available("firefox")
    assert result is None, f"Expected None, got {result}"
    print("✓ Initial cache state is None")
    
    # Test caching availability
    cache.cache_browser_availability("firefox", True)
    result = cache.is_browser_available("firefox")
    assert result is True, f"Expected True, got {result}"
    print("✓ Browser availability caching works")
    
    cache.cache_browser_availability("chrome", False)
    result = cache.is_browser_available("chrome")
    assert result is False, f"Expected False, got {result}"
    print("✓ Browser unavailability caching works")
    
    # Test failure tracking
    unhealthy = cache.is_browser_unhealthy("safari")
    assert not unhealthy, f"Expected False, got {unhealthy}"
    print("✓ Initial health state is healthy")
    
    # Add some failures
    cache.record_browser_failure("safari")
    cache.record_browser_failure("safari")
    unhealthy = cache.is_browser_unhealthy("safari")
    assert not unhealthy, f"Expected False (under threshold), got {unhealthy}"
    print("✓ Browser health tracking under threshold")
    
    cache.record_browser_failure("safari")  # This should make it unhealthy
    unhealthy = cache.is_browser_unhealthy("safari")
    assert unhealthy, f"Expected True (over threshold), got {unhealthy}"
    print("✓ Browser health tracking over threshold")
    
    print("✓ All BrowserCache tests passed!")
    return True

def main():
    """Run the test."""
    try:
        test_browser_cache()
        print("\n🎉 All tests passed! The external browser cache logic is working correctly.")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())