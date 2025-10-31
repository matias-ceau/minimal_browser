# GitHub Labels for Placeholder Implementation Issues

This document provides commands to create the necessary labels for managing the placeholder implementation issues.

## Using GitHub CLI

```bash
# Priority Labels (using color gradient)
gh label create "P1-high-priority" --color "d93f0b" --description "Critical features, high user impact" --repo matias-ceau/minimal_browser
gh label create "P2-medium-priority" --color "fbca04" --description "Important features, quality improvements" --repo matias-ceau/minimal_browser
gh label create "P3-low-priority" --color "0e8a16" --description "Nice to have, cleanup, documentation" --repo matias-ceau/minimal_browser

# Type Labels
gh label create "enhancement" --color "a2eeef" --description "New feature implementation" --repo matias-ceau/minimal_browser
gh label create "documentation" --color "0075ca" --description "Documentation updates and improvements" --repo matias-ceau/minimal_browser
gh label create "cleanup" --color "d4c5f9" --description "Code cleanup and refactoring" --repo matias-ceau/minimal_browser

# Component Labels
gh label create "storage" --color "c5def5" --description "Storage and persistence layer" --repo matias-ceau/minimal_browser
gh label create "rendering" --color "f9d0c4" --description "UI and rendering components" --repo matias-ceau/minimal_browser
gh label create "coordination" --color "bfdadc" --description "Multi-agent coordination system" --repo matias-ceau/minimal_browser
gh label create "engines" --color "fef2c0" --description "Web engine implementations" --repo matias-ceau/minimal_browser
gh label create "experimental" --color "e99695" --description "Experimental features" --repo matias-ceau/minimal_browser
```

## Label Reference

### Priority Labels
| Label | Color | Description | Usage |
|-------|-------|-------------|-------|
| `P1-high-priority` | 🔴 #d93f0b | Critical features, high user impact | ISSUE_02 |
| `P2-medium-priority` | 🟡 #fbca04 | Important features, quality improvements | ISSUE_01, 03, 04, 05 |
| `P3-low-priority` | 🟢 #0e8a16 | Nice to have, cleanup, documentation | ISSUE_06, 07 |

### Type Labels
| Label | Color | Description | Usage |
|-------|-------|-------------|-------|
| `enhancement` | 🔵 #a2eeef | New feature implementation | ISSUE_01-05 |
| `documentation` | 🔷 #0075ca | Documentation updates | ISSUE_06 |
| `cleanup` | 🟣 #d4c5f9 | Code cleanup and refactoring | ISSUE_07 |

### Component Labels
| Label | Color | Description | Usage |
|-------|-------|-------------|-------|
| `storage` | 🔵 #c5def5 | Storage/persistence layer | ISSUE_01, 07 |
| `rendering` | 🟠 #f9d0c4 | UI/rendering components | ISSUE_02 |
| `coordination` | 🔷 #bfdadc | Multi-agent coordination | ISSUE_03, 04, 05 |
| `engines` | 🟡 #fef2c0 | Web engine implementations | ISSUE_06 |
| `experimental` | 🔴 #e99695 | Experimental features | ISSUE_03, 04, 05 |

## Label Assignment by Issue

```
ISSUE_01: enhancement, P2-medium-priority, storage
ISSUE_02: enhancement, P1-high-priority, rendering
ISSUE_03: enhancement, P2-medium-priority, coordination, experimental
ISSUE_04: enhancement, P2-medium-priority, coordination, experimental
ISSUE_05: enhancement, P2-medium-priority, coordination, experimental
ISSUE_06: documentation, P3-low-priority, engines
ISSUE_07: cleanup, P3-low-priority, storage
```

## Checking Existing Labels

Before creating labels, check what already exists:

```bash
gh label list --repo matias-ceau/minimal_browser
```

## Deleting Labels (if needed)

If you need to recreate labels:

```bash
gh label delete "P1-high-priority" --repo matias-ceau/minimal_browser --yes
gh label delete "P2-medium-priority" --repo matias-ceau/minimal_browser --yes
gh label delete "P3-low-priority" --repo matias-ceau/minimal_browser --yes
# ... etc
```

## Using GitHub Web Interface

If you prefer the web interface:

1. Go to https://github.com/matias-ceau/minimal_browser/labels
2. Click "New label"
3. Enter label name, description, and color
4. Click "Create label"
5. Repeat for all labels

## Label Best Practices

### Priority Labels
- Only one priority label per issue
- Re-evaluate priorities quarterly
- High priority = blocks users or critical functionality
- Low priority = enhancement, nice-to-have

### Component Labels
- Use multiple if issue spans components
- Helps filter and search issues
- Useful for code owners and specialists

### Type Labels
- Use to track work types
- Helps with sprint planning
- Filter by type for similar work

### Experimental Label
- Use for features still in research/prototype phase
- May change significantly
- Not guaranteed for production

## Automation

Consider setting up GitHub Actions to auto-label based on:
- File paths in PR (e.g., `src/storage/*` → `storage` label)
- PR title keywords (e.g., "docs:" → `documentation` label)
- Issue template selections

Example `.github/labeler.yml`:
```yaml
storage:
  - src/minimal_browser/storage/**/*

rendering:
  - src/minimal_browser/rendering/**/*

coordination:
  - src/minimal_browser/coordination/**/*

engines:
  - src/minimal_browser/engines/**/*

documentation:
  - docs/**/*
  - "**/*.md"
```

---

**Note**: Labels can be edited at any time via GitHub web interface or CLI.
