// ROADMAP.md

# Project Roadmap

This document outlines upcoming features, refactors, and improvements for the Minimal Browser project.  
Each item will be tracked via Git branches/issues and updated as progress is made.

---

## Authentication & Security
- [ ] Implement cookies to keep users logged in  
- [ ] Integrate with system password store for secure credential management  

## Performance
- [ ] Explore and prototype performance improvements via C or Rust integration  

## Architecture & Structure
- [ ] Refactor project structure to better separate concerns  
  - Create dedicated folders for HTML/Jinja templates  

## AI & Tools
- [ ] Enhance AI tool usage with Pydantic models for strict typing and clearer context  
- [ ] Add feature to capture screenshots and allow AI queries about the current page  
- [ ] Fix Unicode handling issues in AI generation  

## Export & Sharing
- [ ] Implement export functionality for any page to Markdown and other formats  

## User Interface
- [ ] Create split-screen view with optional AI sidebar  
- [ ] Redesign the command prompt UI to be centered and more visually appealing with icons/designs instead of plain text letters  

## File & Bookmark Management
- [ ] Develop a file browser with embedding capabilities  
- [ ] Implement recall-like smart bookmarks (supports files, code snippets, cross-context usage)  
- [ ] Add seamless bindings for already installed browser apps  

---

## Notes
- Branching and commit guidelines must follow the **Commit & Branching Policy**.  
- Features should be atomic and reviewed via pull request into `development` before merging to `main`.