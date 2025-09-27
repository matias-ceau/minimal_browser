"""Enhanced external browser integration module."""

from __future__ import annotations

import os
import time
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config.default_config import BrowserConfig


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


class ExternalBrowserManager:
    """Enhanced external browser management with configuration support."""
    
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.cache = BrowserCache() if config.cache_browser_detection else None
        self._detected_browsers: Optional[List[str]] = None
    
    def detect_available_browsers(self, force_refresh: bool = False) -> List[str]:
        """Detect available browsers on the system."""
        if not force_refresh and self._detected_browsers is not None:
            return self._detected_browsers
        
        available_browsers = []
        
        for browser_name in self.config.preferred_browsers:
            # Check cache first
            if self.cache:
                cached_result = self.cache.is_browser_available(browser_name)
                if cached_result is not None:
                    if cached_result:
                        available_browsers.append(browser_name)
                    continue
                
                # Skip if browser is marked as unhealthy
                if self.cache.is_browser_unhealthy(browser_name):
                    continue
            
            # Test browser availability
            try:
                browser_obj = webbrowser.get(browser_name)
                if browser_obj:
                    available_browsers.append(browser_name)
                    if self.cache:
                        self.cache.cache_browser_availability(browser_name, True)
            except webbrowser.Error:
                if self.cache:
                    self.cache.cache_browser_availability(browser_name, False)
                continue
            except Exception:
                # Unexpected error, treat as unavailable
                if self.cache:
                    self.cache.cache_browser_availability(browser_name, False)
                continue
        
        self._detected_browsers = available_browsers
        return available_browsers
    
    def get_preferred_browser(self) -> Optional[str]:
        """Get the preferred browser based on configuration."""
        if self.config.default_external_browser:
            # Check if the configured default is available
            available_browsers = self.detect_available_browsers()
            if self.config.default_external_browser in available_browsers:
                return self.config.default_external_browser
        
        # Return first available browser from preferred list
        available_browsers = self.detect_available_browsers()
        return available_browsers[0] if available_browsers else None
    
    def open_url(self, url: str, browser_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Open URL in external browser.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Validate URL
        if not url or url.startswith("data:"):
            return False, "Cannot open data URLs in external browser"
        
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Determine which browser to use
        target_browser = browser_name or self.get_preferred_browser()
        
        try:
            if target_browser:
                # Try specific browser
                browser_obj = webbrowser.get(target_browser)
                browser_obj.open(url)
                return True, f"Opened in {target_browser}: {url[:40]}..."
            else:
                # Fallback to system default
                webbrowser.open(url)
                return True, f"Opened in system default browser: {url[:40]}..."
                
        except webbrowser.Error as e:
            error_msg = f"Browser '{target_browser}' not found" if target_browser else "No suitable browser found"
            
            # Record failure for caching
            if self.cache and target_browser:
                self.cache.record_browser_failure(target_browser)
            
            # Try fallback to system default if specific browser failed
            if target_browser and target_browser != "default":
                try:
                    webbrowser.open(url)
                    return True, f"Opened in system default browser: {url[:40]}..."
                except Exception:
                    pass
            
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Failed to open URL: {str(e)}"
            
            # Record failure for caching
            if self.cache and target_browser:
                self.cache.record_browser_failure(target_browser)
            
            return False, error_msg
    
    def get_browser_info(self) -> Dict[str, any]:
        """Get information about browser configuration and availability."""
        available_browsers = self.detect_available_browsers()
        preferred_browser = self.get_preferred_browser()
        
        return {
            "available_browsers": available_browsers,
            "preferred_browser": preferred_browser,
            "default_configured": self.config.default_external_browser,
            "cache_enabled": self.cache is not None,
            "browser_count": len(available_browsers)
        }