#!/usr/bin/env python3
"""
Script to create GitHub issues from the identified placeholder implementations.

This script reads the issue markdown files and creates corresponding GitHub issues
using the GitHub CLI (gh) or GitHub API.

Requirements:
    - GitHub CLI installed: https://cli.github.com/
    - Authenticated: gh auth login
    - Or use GITHUB_TOKEN environment variable

Usage:
    python create_issues.py

The script will:
1. Read each ISSUE_XX_*.md file
2. Extract title, labels, and body
3. Create GitHub issue via gh CLI
4. Print issue URL
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Issue configuration
REPO = "matias-ceau/minimal_browser"
ISSUE_DIR = Path(__file__).parent  # Use the directory where this script is located

ISSUES = [
    {
        "file": "ISSUE_01_browsing_data_management.md",
        "title": "Implement Browsing Data Management Module",
        "labels": ["enhancement", "P2-medium-priority", "storage"],
        "assignees": [],  # Can be filled with copilot agent usernames
    },
    {
        "file": "ISSUE_02_webapps_rendering.md",
        "title": "Implement Web Applications Rendering Module",
        "labels": ["enhancement", "P1-high-priority", "rendering"],
        "assignees": [],
    },
    {
        "file": "ISSUE_03_agent_context_management.md",
        "title": "Implement Agent Context Management",
        "labels": ["enhancement", "P2-medium-priority", "coordination", "experimental"],
        "assignees": [],
    },
    {
        "file": "ISSUE_04_agent_goal_management.md",
        "title": "Implement Agent Goal Management",
        "labels": ["enhancement", "P2-medium-priority", "coordination", "experimental"],
        "assignees": [],
    },
    {
        "file": "ISSUE_05_agent_to_agent_communication.md",
        "title": "Implement Agent-to-Agent Communication System",
        "labels": ["enhancement", "P2-medium-priority", "coordination", "experimental"],
        "assignees": [],
    },
    {
        "file": "ISSUE_06_gtk_engine_documentation.md",
        "title": "Review and Update GTK WebEngine Documentation",
        "labels": ["documentation", "P3-low-priority", "engines"],
        "assignees": [],
    },
    {
        "file": "ISSUE_07_conversation_log_cleanup.md",
        "title": "Remove Redundant Placeholder Comment in ConversationLog.save()",
        "labels": ["cleanup", "P3-low-priority", "storage"],
        "assignees": [],
    },
]


def read_issue_body(filepath: Path) -> str:
    """Read issue body from markdown file."""
    with open(filepath, "r") as f:
        return f.read()


def create_issue_via_gh(
    title: str,
    body: str,
    labels: List[str],
    assignees: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Create GitHub issue using gh CLI.
    
    Returns:
        Issue URL if successful, None otherwise
    """
    cmd = [
        "gh",
        "issue",
        "create",
        "--repo",
        REPO,
        "--title",
        title,
        "--body",
        body,
    ]
    
    if labels:
        cmd.extend(["--label", ",".join(labels)])
    
    if assignees:
        cmd.extend(["--assignee", ",".join(assignees)])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        issue_url = result.stdout.strip()
        return issue_url
    except subprocess.CalledProcessError as e:
        print(f"Error creating issue: {e}")
        print(f"STDERR: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: gh CLI not found. Install from https://cli.github.com/")
        return None


def main():
    """Create all GitHub issues."""
    print(f"Creating issues for repository: {REPO}")
    print(f"Reading issue files from: {ISSUE_DIR}")
    print()
    
    created_issues = []
    failed_issues = []
    
    for issue_config in ISSUES:
        filepath = ISSUE_DIR / issue_config["file"]
        
        if not filepath.exists():
            print(f"❌ File not found: {filepath}")
            failed_issues.append(issue_config["title"])
            continue
        
        print(f"Creating issue: {issue_config['title']}")
        body = read_issue_body(filepath)
        
        issue_url = create_issue_via_gh(
            title=issue_config["title"],
            body=body,
            labels=issue_config["labels"],
            assignees=issue_config["assignees"] if issue_config["assignees"] else None,
        )
        
        if issue_url:
            print(f"✅ Created: {issue_url}")
            created_issues.append((issue_config["title"], issue_url))
        else:
            print(f"❌ Failed to create issue")
            failed_issues.append(issue_config["title"])
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Created: {len(created_issues)} issues")
    print(f"❌ Failed: {len(failed_issues)} issues")
    print()
    
    if created_issues:
        print("Created Issues:")
        for title, url in created_issues:
            print(f"  - {title}")
            print(f"    {url}")
        print()
    
    if failed_issues:
        print("Failed Issues:")
        for title in failed_issues:
            print(f"  - {title}")
        print()


if __name__ == "__main__":
    main()
