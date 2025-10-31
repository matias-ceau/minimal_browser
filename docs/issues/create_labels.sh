#!/bin/bash
# Create GitHub labels for placeholder implementation issues
# Repository: matias-ceau/minimal_browser

REPO="matias-ceau/minimal_browser"

echo "Creating labels for repository: $REPO"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed."
    echo "Install from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI."
    echo "Run: gh auth login"
    exit 1
fi

echo "Creating priority labels..."
gh label create "P1-high-priority" --color "d93f0b" --description "Critical features, high user impact" --repo "$REPO" 2>/dev/null && echo "✓ P1-high-priority" || echo "  P1-high-priority (already exists)"
gh label create "P2-medium-priority" --color "fbca04" --description "Important features, quality improvements" --repo "$REPO" 2>/dev/null && echo "✓ P2-medium-priority" || echo "  P2-medium-priority (already exists)"
gh label create "P3-low-priority" --color "0e8a16" --description "Nice to have, cleanup, documentation" --repo "$REPO" 2>/dev/null && echo "✓ P3-low-priority" || echo "  P3-low-priority (already exists)"

echo ""
echo "Creating type labels..."
gh label create "enhancement" --color "a2eeef" --description "New feature implementation" --repo "$REPO" 2>/dev/null && echo "✓ enhancement" || echo "  enhancement (already exists)"
gh label create "documentation" --color "0075ca" --description "Documentation updates and improvements" --repo "$REPO" 2>/dev/null && echo "✓ documentation" || echo "  documentation (already exists)"
gh label create "cleanup" --color "d4c5f9" --description "Code cleanup and refactoring" --repo "$REPO" 2>/dev/null && echo "✓ cleanup" || echo "  cleanup (already exists)"

echo ""
echo "Creating component labels..."
gh label create "storage" --color "c5def5" --description "Storage and persistence layer" --repo "$REPO" 2>/dev/null && echo "✓ storage" || echo "  storage (already exists)"
gh label create "rendering" --color "f9d0c4" --description "UI and rendering components" --repo "$REPO" 2>/dev/null && echo "✓ rendering" || echo "  rendering (already exists)"
gh label create "coordination" --color "bfdadc" --description "Multi-agent coordination system" --repo "$REPO" 2>/dev/null && echo "✓ coordination" || echo "  coordination (already exists)"
gh label create "engines" --color "fef2c0" --description "Web engine implementations" --repo "$REPO" 2>/dev/null && echo "✓ engines" || echo "  engines (already exists)"
gh label create "experimental" --color "e99695" --description "Experimental features" --repo "$REPO" 2>/dev/null && echo "✓ experimental" || echo "  experimental (already exists)"

echo ""
echo "Done! Labels have been created."
echo ""
echo "View labels at: https://github.com/$REPO/labels"
