#!/usr/bin/env python3
"""Documentation health check script.

This script analyzes the codebase and documentation to identify:
- Outdated module references
- Undocumented features
- Missing or stale documentation sections

Run this periodically to ensure docs stay in sync with code.
"""

from __future__ import annotations

import ast
import re
from datetime import datetime
from pathlib import Path
from typing import Any


class DocChecker:
    """Checks documentation health against codebase."""

    def __init__(self, root_dir: Path | None = None):
        """Initialize the checker.
        
        Args:
            root_dir: Repository root directory. Defaults to parent of script.
        """
        if root_dir is None:
            root_dir = Path(__file__).parent.parent
        self.root = root_dir
        self.src_dir = root_dir / "src" / "minimal_browser"
        self.issues: list[str] = []
        
    def check_module_structure(self) -> None:
        """Verify documented modules match actual structure."""
        print("📂 Checking module structure...")
        
        # Get actual modules
        actual_modules = set()
        if self.src_dir.exists():
            for path in self.src_dir.iterdir():
                if path.is_dir() and not path.name.startswith("__"):
                    actual_modules.add(path.name)
        
        # Check docs/development/ARCHITECTURE.md mentions all modules
        arch_file = self.root / "docs" / "development" / "ARCHITECTURE.md"
        if arch_file.exists():
            arch_content = arch_file.read_text()
            
            missing_modules = []
            for module in sorted(actual_modules):
                if module not in arch_content:
                    missing_modules.append(module)
            
            if missing_modules:
                self.issues.append(
                    f"⚠️  docs/development/ARCHITECTURE.md missing modules: {', '.join(missing_modules)}"
                )
            else:
                print("✓ All modules documented in docs/development/ARCHITECTURE.md")
        else:
            self.issues.append("❌ docs/development/ARCHITECTURE.md not found")
    
    def check_last_updated(self) -> None:
        """Check if documentation update dates are recent."""
        print("\n📅 Checking last updated dates...")
        
        arch_file = self.root / "docs" / "development" / "ARCHITECTURE.md"
        if arch_file.exists():
            content = arch_file.read_text()
            match = re.search(r"Last updated:\s*(\d{4}-\d{2}-\d{2})", content)
            
            if match:
                doc_date = datetime.strptime(match.group(1), "%Y-%m-%d")
                today = datetime.now()
                days_old = (today - doc_date).days
                
                if days_old > 30:
                    self.issues.append(
                        f"⚠️  docs/development/ARCHITECTURE.md last updated {days_old} days ago"
                    )
                else:
                    print(f"✓ docs/development/ARCHITECTURE.md updated {days_old} days ago")
            else:
                self.issues.append("⚠️  docs/development/ARCHITECTURE.md missing 'Last updated' date")
    
    def check_ai_actions(self) -> None:
        """Verify AI action schemas are documented."""
        print("\n🤖 Checking AI actions...")
        
        # Parse schemas.py to find action classes
        schemas_file = self.src_dir / "ai" / "schemas.py"
        if not schemas_file.exists():
            self.issues.append("❌ ai/schemas.py not found")
            return
        
        try:
            with open(schemas_file) as f:
                tree = ast.parse(f.read())
            
            action_classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if node.name.endswith("Action"):
                        action_classes.append(node.name)
            
            # Check if actions are mentioned in docs
            arch_file = self.root / "docs" / "development" / "ARCHITECTURE.md"
            if arch_file.exists():
                arch_content = arch_file.read_text()
                
                undocumented = []
                for action in action_classes:
                    # Look for action name without "Action" suffix
                    action_name = action.replace("Action", "")
                    if action_name.lower() not in arch_content.lower():
                        undocumented.append(action)
                
                if undocumented:
                    self.issues.append(
                        f"⚠️  AI actions not documented: {', '.join(undocumented)}"
                    )
                else:
                    print(f"✓ All {len(action_classes)} AI actions documented")
        
        except Exception as e:
            self.issues.append(f"❌ Error parsing schemas.py: {e}")
    
    def check_vim_commands(self) -> None:
        """Check if vim commands in code are documented."""
        print("\n⌨️  Checking vim commands...")
        
        browser_file = self.src_dir / "minimal_browser.py"
        if not browser_file.exists():
            self.issues.append("❌ minimal_browser.py not found")
            return
        
        try:
            content = browser_file.read_text()
            
            # Find command patterns - but exclude basic vim commands
            basic_vim_commands = {"q", "w", "wq", "e ", "help", "h", "bd", "bn", "bp", "b"}
            
            command_patterns = [
                r'elif cmd\.startswith\("([^"]+)"\)',
                r'if cmd in \["([^"]+)"',
            ]
            
            commands = set()
            for pattern in command_patterns:
                for match in re.finditer(pattern, content):
                    cmd = match.group(1)
                    if cmd and not cmd.startswith("_") and cmd not in basic_vim_commands:
                        commands.add(cmd)
            
            # Check README for command documentation
            readme_file = self.root / "README.md"
            if readme_file.exists():
                readme_content = readme_file.read_text()
                
                undocumented = []
                for cmd in sorted(commands):
                    # Check for command or its shorthand
                    if f":{cmd}" not in readme_content and f"`:{cmd}`" not in readme_content:
                        undocumented.append(f":{cmd}")
                
                if undocumented:
                    self.issues.append(
                        f"⚠️  Commands possibly undocumented in README: {', '.join(undocumented[:10])}"
                    )
                    if len(undocumented) > 10:
                        self.issues.append(
                            f"    ... and {len(undocumented) - 10} more"
                        )
                else:
                    print(f"✓ Command documentation appears complete")
            
        except Exception as e:
            self.issues.append(f"❌ Error checking commands: {e}")
    
    def check_test_coverage_claim(self) -> None:
        """Verify documentation claims about testing match reality."""
        print("\n🧪 Checking test coverage claims...")
        
        tests_dir = self.root / "tests"
        test_files = []
        if tests_dir.exists():
            test_files = list(tests_dir.glob("**/*test*.py"))
        
        readme_file = self.root / "README.md"
        if readme_file.exists():
            readme_content = readme_file.read_text()
            
            if "no automated test suite" in readme_content.lower():
                if test_files:
                    self.issues.append(
                        f"⚠️  README claims no tests, but {len(test_files)} test files exist"
                    )
            elif "unit tests" in readme_content.lower() or "test coverage" in readme_content.lower():
                if not test_files:
                    self.issues.append(
                        "⚠️  README mentions tests, but no test files found"
                    )
                else:
                    print(f"✓ Test coverage claims match reality ({len(test_files)} test files)")
    
    def run_all_checks(self) -> bool:
        """Run all documentation checks.
        
        Returns:
            True if all checks passed, False if issues found.
        """
        print("🔍 Running documentation health checks...\n")
        
        self.check_module_structure()
        self.check_last_updated()
        self.check_ai_actions()
        self.check_vim_commands()
        self.check_test_coverage_claim()
        
        print("\n" + "=" * 60)
        if self.issues:
            print(f"\n❌ Found {len(self.issues)} documentation issue(s):\n")
            for issue in self.issues:
                print(f"  {issue}")
            print("\n" + "=" * 60)
            return False
        else:
            print("\n✅ All documentation checks passed!")
            print("=" * 60)
            return True


def main() -> None:
    """Run documentation checks."""
    checker = DocChecker()
    success = checker.run_all_checks()
    
    if not success:
        print("\n💡 Consider running this script regularly or in CI to catch docs drift")
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()
