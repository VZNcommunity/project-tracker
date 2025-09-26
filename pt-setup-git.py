#!/usr/bin/env python3

import sqlite3
import os
import sys
import subprocess
from pathlib import Path

def get_project_tracker_db():
    """Get path to project tracker database."""
    data_dir = Path.home() / '.local' / 'share' / 'project-tracker'
    return data_dir / 'tracker.db'

def setup_git_hooks(project_path):
    """Set up Git hooks for a project."""
    hooks_dir = Path(project_path) / '.git' / 'hooks'
    if not hooks_dir.exists():
        print(f"✗ {project_path} - Not a Git repository")
        return False

    # Create post-commit hook
    post_commit_hook = hooks_dir / 'post-commit'
    hook_content = f"""#!/bin/bash
# Project Tracker Git Integration
{Path.home() / '.local' / 'bin' / 'pt-git-hook.py'}
"""

    try:
        with open(post_commit_hook, 'w') as f:
            f.write(hook_content)
        post_commit_hook.chmod(0o755)
        print(f"✓ {project_path} - Git hook installed")
        return True
    except Exception as e:
        print(f"✗ {project_path} - Failed to install hook: {e}")
        return False

def main():
    """Set up Git hooks for all tracked projects or specific project."""
    db_path = get_project_tracker_db()
    if not db_path.exists():
        print("✗ Project tracker database not found. Run 'pt add-project' first.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if len(sys.argv) > 1:
        # Setup for specific project
        project_ref = sys.argv[1]
        try:
            project_id = int(project_ref)
            cursor.execute('SELECT name, path FROM projects WHERE id = ?', (project_id,))
        except ValueError:
            cursor.execute('SELECT name, path FROM projects WHERE name LIKE ?', (f'%{project_ref}%',))

        result = cursor.fetchone()
        if not result:
            print(f"✗ Project '{project_ref}' not found")
            sys.exit(1)

        name, path = result
        if not path:
            print(f"✗ Project '{name}' has no path configured")
            sys.exit(1)

        print(f"Setting up Git hooks for '{name}'...")
        setup_git_hooks(path)
    else:
        # Setup for all projects with paths
        cursor.execute('SELECT name, path FROM projects WHERE path IS NOT NULL')
        projects = cursor.fetchall()

        if not projects:
            print("✗ No projects with paths found")
            sys.exit(1)

        print(f"Setting up Git hooks for {len(projects)} project(s)...")
        success_count = 0

        for name, path in projects:
            if path and os.path.exists(path):
                if setup_git_hooks(path):
                    success_count += 1
            else:
                print(f"✗ {name} - Path '{path}' does not exist")

        print(f"\n✓ Successfully set up Git hooks for {success_count}/{len(projects)} projects")

        if success_count > 0:
            print("\n💡 Git Integration Usage:")
            print("   In commit messages, use:")
            print("   • 'pt:123 completed' - mark task 123 as completed")
            print("   • 'pt:123 progress' - mark task 123 as in progress")
            print("   • 'pt:123 blocked' - mark task 123 as blocked")
            print("   • 'pt:123' - log activity for task 123")

    conn.close()

if __name__ == '__main__':
    main()