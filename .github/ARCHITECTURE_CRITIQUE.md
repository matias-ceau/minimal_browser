# Architecture & Documentation Critique

## Current State Analysis

### Documentation Strengths ✅
- **ROADMAP.md**: Well-structured feature planning with clear priorities
- **FEATURE_REQUESTS.md**: Detailed tracking with FR-### numbering system  
- **Inline documentation**: Good docstrings in key modules (`ai/schemas.py`, `engines/base.py`)
- **Code organization**: Logical module separation (engines/, ai/, storage/, templates/)

### Critical Documentation Gaps ❌

#### 1. Missing Architectural Overview
- **Problem**: No centralized explanation of how engines, AI pipeline, and UI interact
- **Impact**: New contributors must reverse-engineer core patterns from scattered files
- **Solution**: The new `.github/copilot-instructions.md` addresses this

#### 2. Development Workflow Documentation
- **Problem**: No documentation of build/test/lint commands
- **Impact**: Contributors don't know how to validate changes
- **Current**: Only `pyproject.toml` hints at structure
- **Missing**: Setup instructions, environment requirements, debugging workflows

#### 3. AI Integration Complexity Undocumented
- **Problem**: Complex ResponseProcessor logic scattered across multiple methods
- **Impact**: Adding new AI actions requires deep code diving
- **Evidence**: `_intelligent_parse()` has complex regex patterns with no explanation

## Architecture Assessment

### Well-Designed Patterns ✅

#### 1. Engine Abstraction
```python
# src/minimal_browser/engines/base.py
class WebEngine(ABC):
    @abstractmethod
    def create_widget(self) -> Any: pass
```
**Strength**: Clean separation enables Qt/GTK engine swapping

#### 2. Pydantic Schema Validation
```python
# src/minimal_browser/ai/schemas.py  
AIAction = Union[NavigateAction, SearchAction, HtmlAction]
```
**Strength**: Type-safe AI response handling prevents runtime errors

#### 3. Modal Interface Design
**Strength**: Vim-like modes provide familiar UX for power users

### Architectural Concerns ⚠️

#### 1. Mixed Responsibilities in Main File
- **Issue**: `minimal_browser.py` is 1,569 lines with UI, AI worker, and HTML generation
- **Evidence**: HTML templates hardcoded in Python strings (lines 400-600)
- **Impact**: Hard to maintain, test, and extend

#### 2. Inconsistent Error Handling
- **Issue**: Qt WebEngine initialization has fallback, but AI responses don't
- **Evidence**: `to_data_url()` has comprehensive error handling, but `ResponseProcessor` doesn't
- **Risk**: Silent failures in AI pipeline

#### 3. OpenRouter API Coupling
- **Issue**: Hardcoded OpenRouter assumptions throughout AI module
- **Evidence**: Model names like `"openrouter/openai/gpt-5-codex-preview"`
- **Limitation**: Difficult to add other AI providers

## Specific Recommendations

### Immediate Actions (High Priority)

#### 1. Extract HTML Templates
**Current**: HTML templates embedded as Python strings
```python
# Bad: In minimal_browser.py lines 400+
return f"""<!DOCTYPE html><html>..."""
```
**Recommended**: 
```python
# Good: Use templates/ directory
from jinja2 import Template
template = Template(open('templates/calculator.html').read())
return template.render(query=query)
```

#### 2. Create Development Documentation
**Missing**: `CONTRIBUTING.md` with:
- Environment setup (`pip install -e .`)
- Required environment variables (`OPENROUTER_API_KEY`)
- Test commands (`python -m py_compile src/`)
- Debugging steps (Qt issues, AI failures)

#### 3. Standardize Error Handling
**Pattern**: Implement consistent error handling across modules
```python
# Recommended pattern
class AIResponseError(Exception): pass
class WebEngineError(Exception): pass
```

### Medium-Term Improvements

#### 1. Split Main Browser Class
**Current**: Monolithic `MinimalBrowser` class
**Recommended**: 
- `BrowserWindow` (UI only)
- `AIController` (AI integration)  
- `TemplateRenderer` (HTML generation)
- `CommandHandler` (vim commands)

#### 2. Plugin Architecture for AI Providers
**Current**: OpenRouter-only
**Recommended**: Provider interface
```python
class AIProvider(ABC):
    @abstractmethod
    def get_response(self, query: str) -> str: pass
```

#### 3. Configuration Management
**Missing**: Centralized config system
**Recommended**: 
```python
# config.py
@dataclass
class BrowserConfig:
    ai_provider: str = "openrouter"
    default_search_engine: str = "google"
    cache_size_mb: int = 50
```

## Documentation Quality Score

| Category | Score | Rationale |
|----------|-------|-----------|
| **API Documentation** | 7/10 | Good Pydantic schemas, missing AI client docs |
| **Architecture Overview** | 3/10 | No centralized explanation (now fixed) |
| **Setup Instructions** | 2/10 | Only pyproject.toml, no step-by-step |
| **Development Workflow** | 1/10 | No build/test/lint documentation |
| **Code Examples** | 6/10 | Good inline examples, missing integration examples |
| **Error Handling Guide** | 4/10 | Some patterns documented, inconsistent |

**Overall Score: 4/10** - Functional but requires significant improvement for contributor onboarding.

## Success Metrics

### Documentation Completeness
- [ ] All public APIs documented with examples
- [ ] Development setup takes <5 minutes for new contributors  
- [ ] Architecture overview helps contributors understand design decisions
- [ ] Error handling patterns are consistent and documented

### Code Maintainability  
- [ ] Main browser file <800 lines (currently 1,569)
- [ ] HTML templates extracted to files
- [ ] AI provider interface abstracts OpenRouter dependency
- [ ] Configuration system centralizes settings

This critique should guide the next phase of architectural improvements outlined in the ROADMAP.md.