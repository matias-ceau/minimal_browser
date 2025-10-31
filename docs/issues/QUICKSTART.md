# Quick Start Guide: Creating GitHub Issues for Placeholder Implementations

This guide walks you through creating GitHub issues from the placeholder implementation specifications.

## Prerequisites

- GitHub account with write access to `matias-ceau/minimal_browser`
- GitHub CLI (`gh`) installed and authenticated (recommended)
- OR ability to create issues manually via GitHub web interface

## Step 1: Create Labels (One-time setup)

### Using GitHub CLI (Recommended)

```bash
# Navigate to repository
cd /home/runner/work/minimal_browser/minimal_browser

# Create all labels at once
bash docs/issues/create_labels.sh
```

### Or create labels manually

1. Go to https://github.com/matias-ceau/minimal_browser/labels
2. Click "New label" for each label in `docs/issues/LABELS.md`
3. Copy name, description, and color hex codes

**Labels to create:**
- Priority: `P1-high-priority`, `P2-medium-priority`, `P3-low-priority`
- Type: `enhancement`, `documentation`, `cleanup`
- Component: `storage`, `rendering`, `coordination`, `engines`, `experimental`

## Step 2: Create Issues

### Method A: Using the Python Script (Easiest)

```bash
# Make sure gh CLI is authenticated
gh auth status

# Run the script
cd /home/runner/work/minimal_browser/minimal_browser
python3 docs/issues/create_issues.py

# The script will:
# - Read all ISSUE_*.md files
# - Create GitHub issues with appropriate labels
# - Print issue URLs
```

### Method B: Using GitHub CLI Manually

```bash
# Example for ISSUE_01
gh issue create \
  --repo matias-ceau/minimal_browser \
  --title "Implement Browsing Data Management Module" \
  --body-file docs/issues/ISSUE_01_browsing_data_management.md \
  --label "enhancement,P2-medium-priority,storage"

# Repeat for all 7 issues
```

### Method C: Manual via Web Interface

1. Go to https://github.com/matias-ceau/minimal_browser/issues/new
2. For each ISSUE_XX file:
   - Copy the title (first heading, remove `#`)
   - Copy the entire markdown content
   - Paste as issue body
   - Add labels as specified in the file
   - Click "Submit new issue"

## Step 3: Assign to Copilot Agents

### Option A: GitHub Copilot Workspace

If using GitHub Copilot Workspace:

```
# In issue comment
@copilot Please implement this feature following the specifications above.
Agent type: [frontend/backend/systems] specialist
```

### Option B: Manual Assignment

1. Go to each created issue
2. Click "Assignees" on the right sidebar
3. Search for and select appropriate agent/developer
4. Save

### Option C: Using Issue Templates

Create `.github/ISSUE_TEMPLATE/copilot_agent_task.md`:

```markdown
---
name: Copilot Agent Task
about: Task specification for copilot agent implementation
labels: enhancement
assignees: ''
---

## Agent Assignment
- [ ] Assigned to: [Agent Name/Type]
- [ ] Estimated effort: [Days]
- [ ] Priority: [P1/P2/P3]

## Related Files
<!-- Link to detailed specification in docs/issues/ -->

## Implementation Checklist
<!-- Copy acceptance criteria from spec -->
```

## Step 4: Create GitHub Project Board (Optional)

Organize issues in a project board:

```bash
# Create project
gh project create --owner matias-ceau --repo minimal_browser --title "Placeholder Implementations"

# Add issues to project (after they're created)
gh project item-add PROJECT_ID --owner matias-ceau --url ISSUE_URL
```

Or manually:
1. Go to https://github.com/matias-ceau/minimal_browser/projects
2. Click "New project"
3. Choose "Board" template
4. Add columns: "Backlog", "In Progress", "In Review", "Done"
5. Add created issues to board

## Step 5: Link Issues to Roadmap

Update `ROADMAP.md` to reference created issues:

```markdown
### P1 · Rendering Toolkit
- [x] Define API for `rendering/webapps.py` → Issue #XX
```

## Expected Issues

After running the script, you should have:

1. **Issue #N**: Implement Browsing Data Management Module
   - Labels: `enhancement`, `P2-medium-priority`, `storage`

2. **Issue #N+1**: Implement Web Applications Rendering Module
   - Labels: `enhancement`, `P1-high-priority`, `rendering`

3. **Issue #N+2**: Implement Agent Context Management
   - Labels: `enhancement`, `P2-medium-priority`, `coordination`, `experimental`

4. **Issue #N+3**: Implement Agent Goal Management
   - Labels: `enhancement`, `P2-medium-priority`, `coordination`, `experimental`

5. **Issue #N+4**: Implement Agent-to-Agent Communication System
   - Labels: `enhancement`, `P2-medium-priority`, `coordination`, `experimental`

6. **Issue #N+5**: Review and Update GTK WebEngine Documentation
   - Labels: `documentation`, `P3-low-priority`, `engines`

7. **Issue #N+6**: Remove Redundant Placeholder Comment in ConversationLog.save()
   - Labels: `cleanup`, `P3-low-priority`, `storage`

## Verification

After creating issues, verify:

```bash
# List all issues with specific labels
gh issue list --repo matias-ceau/minimal_browser --label "P1-high-priority"
gh issue list --repo matias-ceau/minimal_browser --label "enhancement"

# Or view in browser
gh repo view matias-ceau/minimal_browser --web
```

## Troubleshooting

### "gh not found"
Install GitHub CLI: https://cli.github.com/

### "Authentication required"
```bash
gh auth login
# Follow prompts
```

### "Permission denied"
You need write access to the repository. Contact repository owner.

### "Label does not exist"
Create labels first (Step 1) before creating issues.

### Script fails
Check Python version (3.7+):
```bash
python3 --version
```

## Next Steps

After issues are created:

1. **Review specifications** - Read each issue thoroughly
2. **Prioritize** - Decide implementation order (suggested in README.md)
3. **Assign agents** - Assign to copilot agents or developers
4. **Track progress** - Use project board or issue status
5. **Update docs** - Mark completed items in ROADMAP.md

## Getting Help

- Check `docs/issues/README.md` for detailed documentation
- Read individual ISSUE_XX files for specifications
- Review `docs/issues/SUMMARY.md` for overview
- Comment on specific issues for questions

---

**Tip**: Start with P3 issues (documentation, cleanup) to get familiar with the codebase before tackling P1/P2 implementations.
