// FEATURE_REQUESTS.md

# Feature Requests

This document tracks individual feature requests as a companion to the roadmap.  
Each request should translate directly into a GitHub Issue when implemented for better tracking.

---

## Authentication & Security

### FR-001: Persistent Login Cookies
Enable cookie-based sessions so users stay logged in across browser restarts.  
**Priority:** High

### FR-002: Password Store Integration
Integrate with the system password manager (e.g., GNOME Keyring, macOS Keychain, or Windows Credential Manager).  
**Priority:** High

---

## Performance

### FR-003: Native Module Optimization
Investigate integrating C or Rust modules for CPU-intensive parts of the browser.  
**Priority:** Medium

---

## Architecture & Structure

### FR-004: Project Refactor
Restructure the project to improve separation of concerns.  
- Dedicated `templates/` folder for HTML/Jinja files  
- Clearer boundaries between UI, storage, and AI logic  
**Priority:** Medium

---

## AI & Tools

### FR-005: Pydantic AI Integration
Use Pydantic to enforce types and context for AI interactions.  
**Priority:** Medium

### FR-006: AI Page Screenshot Analysis
Add ability to screenshot the current page and query the AI about its contents.  
**Priority:** High

### FR-007: Unicode Bugfix in AI Outputs
Ensure AI-generated content properly handles Unicode without errors.  
**Priority:** High

---

## Export & Sharing

### FR-008: Page Export Capabilities
Implement export of any page to:  
- Markdown  
- PDF  
- HTML snapshot  
**Priority:** High

---

## User Interface

### FR-009: Split View with AI Sidebar
Enable side-by-side browsing and AI assistant panel.  
**Priority:** Medium

### FR-010: Improved Command Prompt
Redesign the command prompt to be centered, styled, and icon-based instead of text-only letters.  
**Priority:** Low

---

## File & Bookmark Management

### FR-011: File Browser and Embeddings
Implement a file browser with embedding capability for code/assets.  
**Priority:** Medium

### FR-012: Smart Bookmarks (Recall)
Allow bookmarking of files/snippets/code for cross-context retrieval.  
**Priority:** High

### FR-013: Bindings for Installed Browser Apps
Provide easy bindings to already installed browser apps for system integration.  
**Priority:** Medium