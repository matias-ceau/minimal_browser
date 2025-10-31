# Issue: Review and Update GTK WebEngine Documentation

## Priority
**P3 - Low Priority** (Documentation/Cleanup)

## Component
`src/minimal_browser/engines/gtk_engine.py`

## Current State
The file is marked as a placeholder in the module docstring:
```python
"""GTK WebKit engine implementation (placeholder)"""
```

However, the module actually contains a **complete implementation** with all required WebEngine methods:
- Widget creation
- URL loading and navigation
- JavaScript execution
- Find in page
- Callbacks for load events
- Settings configuration

## Description
This is a documentation issue, not an implementation gap. The GTK WebEngine is actually fully implemented but incorrectly labeled as a placeholder. This may confuse contributors or users evaluating the codebase.

## Required Changes

### 1. Update Module Docstring
Replace the placeholder docstring with accurate documentation:

```python
"""GTK WebKit engine implementation.

This module provides a GTK-based web engine using WebKit for platforms
that prefer or require GTK over Qt. The implementation is feature-complete
but requires GTK 4.0 and WebKit 6.0 to be installed.

Installation:
    - Debian/Ubuntu: sudo apt install gir1.2-webkit-6.0 python3-gi
    - Arch: sudo pacman -S webkit-gtk python-gobject
    - Fedora: sudo dnf install webkit-gtk python3-gobject

Note: This engine is an alternative to the Qt WebEngine and provides
similar functionality but with different system requirements.
"""
```

### 2. Add Usage Documentation
Add a README or documentation section explaining:
- When to use GTK engine vs Qt engine
- Platform compatibility
- Installation requirements
- Known limitations
- Performance comparison (if any)

### 3. Update Architecture Documentation
Update `docs/development/ARCHITECTURE.md` to reflect that GTK engine is implemented:
- Current: "GTK implementation is placeholder"
- Update: "GTK implementation is complete but requires separate dependencies"

### 4. Add Configuration Examples
Document how to configure the browser to use GTK engine:
```python
# Example configuration
from minimal_browser.engines.gtk_engine import GtkWebEngine

engine = GtkWebEngine()
browser = VimBrowser(engine=engine)
```

## Acceptance Criteria
- [ ] Update module docstring to remove "placeholder" label
- [ ] Add installation instructions in docstring
- [ ] Update ARCHITECTURE.md to reflect implementation status
- [ ] Add engine selection documentation
- [ ] Document any GTK-specific limitations or features
- [ ] Add engine comparison section (Qt vs GTK)

## Related Issues/Features
- Related to TAURI_INVESTIGATION.md mention of GTK as placeholder
- Update docs/development/ARCHITECTURE.md section on engines

## Suggested Implementation Approach
1. Review current GTK implementation for completeness
2. Update module docstring with accurate description
3. Add installation instructions
4. Document engine selection process
5. Update ARCHITECTURE.md
6. Add examples in README or docs/
7. Test installation instructions on different platforms (if possible)

## Assignment
**Suggested for Copilot Agent**: Documentation specialist agent
**Estimated Effort**: 1-2 hours for documentation updates
**Dependencies**: None

## Additional Notes
- The implementation appears complete based on code review
- May want to verify all methods work as expected
- Could add integration tests for GTK engine (currently no tests exist)
- Consider adding GTK engine to CI/CD if dependencies can be installed
- Not urgent since Qt engine is the primary/default implementation
