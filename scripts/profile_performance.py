#!/usr/bin/env python3
"""
Performance profiling script for minimal_browser

Usage:
    python scripts/profile_performance.py --startup
    python scripts/profile_performance.py --html-rendering
    python scripts/profile_performance.py --memory
"""

import argparse
import time
import tracemalloc
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def profile_startup():
    """Profile application startup time breakdown"""
    print("=== Profiling Startup Time ===\n")
    
    # Measure import time
    print("1. Measuring import time...")
    start = time.time()
    try:
        import minimal_browser
        import_time = time.time() - start
        print(f"   ✓ Import time: {import_time:.3f}s")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return None
    
    # Measure Qt initialization
    print("\n2. Measuring Qt initialization...")
    start = time.time()
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        qt_init_time = time.time() - start
        print(f"   ✓ Qt init time: {qt_init_time:.3f}s")
    except Exception as e:
        print(f"   ✗ Qt init failed: {e}")
        qt_init_time = 0
    
    # Measure engine initialization
    print("\n3. Measuring engine initialization...")
    start = time.time()
    try:
        from minimal_browser.engines import get_engine
        engine = get_engine('qt')
        engine_time = time.time() - start
        print(f"   ✓ Engine init time: {engine_time:.3f}s")
    except Exception as e:
        print(f"   ✗ Engine init failed: {e}")
        engine_time = 0
    
    total = import_time + qt_init_time + engine_time
    print(f"\n{'='*40}")
    print(f"Total startup estimate: {total:.3f}s")
    print(f"{'='*40}\n")
    
    return total


def profile_html_rendering():
    """Profile HTML to data URL conversion at various sizes"""
    print("=== Profiling HTML Rendering ===\n")
    
    try:
        from minimal_browser.rendering.html import create_data_url
    except ImportError:
        print("Error: Could not import rendering module")
        return
    
    # Test various HTML sizes
    sizes = [1_000, 10_000, 100_000, 1_000_000]  # bytes
    
    print(f"{'Size (KB)':<12} {'Time (ms)':<12} {'Peak Mem (KB)':<15} {'Output (KB)':<12}")
    print("-" * 55)
    
    for size in sizes:
        html = "<html><body>" + "x" * size + "</body></html>"
        
        # Memory tracking
        tracemalloc.start()
        start = time.time()
        
        # Render
        try:
            data_url = create_data_url(html)
            
            # Measure
            elapsed = (time.time() - start) * 1000  # Convert to ms
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            print(f"{size/1024:<12.1f} {elapsed:<12.2f} {peak/1024:<15.1f} {len(data_url)/1024:<12.1f}")
        except Exception as e:
            tracemalloc.stop()
            print(f"{size/1024:<12.1f} ERROR: {e}")
    
    print()


def profile_memory():
    """Profile memory usage of key components"""
    print("=== Memory Usage Profile ===\n")
    
    tracemalloc.start()
    
    # Baseline
    baseline = tracemalloc.get_traced_memory()
    print(f"Baseline memory: {baseline[0]/1024:.1f} KB")
    
    # After importing main modules
    try:
        import minimal_browser
        after_import = tracemalloc.get_traced_memory()
        print(f"After imports: {after_import[0]/1024:.1f} KB (+{(after_import[0]-baseline[0])/1024:.1f} KB)")
    except Exception as e:
        print(f"Import failed: {e}")
        tracemalloc.stop()
        return
    
    # After Qt
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        after_qt = tracemalloc.get_traced_memory()
        print(f"After Qt init: {after_qt[0]/1024:.1f} KB (+{(after_qt[0]-after_import[0])/1024:.1f} KB)")
    except Exception as e:
        print(f"Qt init failed: {e}")
    
    # Peak memory
    final = tracemalloc.get_traced_memory()
    print(f"\nPeak memory: {final[1]/1024:.1f} KB")
    print(f"Total increase: {(final[0]-baseline[0])/1024:.1f} KB\n")
    
    tracemalloc.stop()


def main():
    parser = argparse.ArgumentParser(
        description="Profile minimal_browser performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/profile_performance.py --startup
  python scripts/profile_performance.py --html-rendering
  python scripts/profile_performance.py --memory
  python scripts/profile_performance.py --all
        """
    )
    parser.add_argument("--startup", action="store_true", help="Profile startup time")
    parser.add_argument("--html-rendering", action="store_true", help="Profile HTML rendering")
    parser.add_argument("--memory", action="store_true", help="Profile memory usage")
    parser.add_argument("--all", action="store_true", help="Run all profiling tests")
    
    args = parser.parse_args()
    
    # If no specific test selected, run all or show help
    if not any([args.startup, args.html_rendering, args.memory, args.all]):
        parser.print_help()
        return
    
    if args.all or args.startup:
        profile_startup()
    
    if args.all or args.html_rendering:
        profile_html_rendering()
    
    if args.all or args.memory:
        profile_memory()


if __name__ == "__main__":
    main()
