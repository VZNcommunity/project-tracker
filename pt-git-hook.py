#!/usr/bin/env python3

import sqlite3
import subprocess
import sys
import re
from pathlib import Path
from datetime import datetime

def get_project_tracker_db():
    """Get path to project tracker database."""
    data_dir = Path.home() / '.local' / 'share' / 'project-tracker'
    return data_dir / 'tracker.db'

def get_git_repo_path():
    """Get the current Git repository path."""
    try:
        repo_path = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'],
                                          stderr=subprocess.DEVNULL).decode().strip()
        return repo_path
    except:
        return None

def find_project_by_path(repo_path):
    """Find project ID by repository path."""
    db_path = get_project_tracker_db()
    if not db_path.exists():
        return None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT id, name FROM projects WHERE path = ?', (repo_path,))
    result = cursor.fetchone()
    conn.close()

    return result

def parse_commit_message(message):
    """Parse commit message for task references and updates."""
    # Look for patterns like:
    # "pt:123 completed" or "pt:123 done" - mark task as completed
    # "pt:123 progress" or "pt:123 working" - mark task as in progress
    # "pt:123 blocked" - mark task as blocked
    # "pt:123" - just log activity

    patterns = {
        r'pt:(\d+)\s+(completed?|done|finished?)': 'completed',
        r'pt:(\d+)\s+(progress|working|started?)': 'in_progress',
        r'pt:(\d+)\s+(blocked?)': 'blocked',
        r'pt:(\d+)': 'activity'
    }

    updates = []
    for pattern, action in patterns.items():
        matches = re.finditer(pattern, message.lower())
        for match in matches:
            task_id = int(match.group(1))
            updates.append((task_id, action))
            # Only process the first match per task to avoid conflicts
            break

    return updates

def update_task_from_git(task_id, action, commit_hash, message, project_id):
    """Update task based on Git commit."""
    db_path = get_project_tracker_db()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verify task exists and belongs to this project
    cursor.execute('SELECT title FROM tasks WHERE id = ? AND project_id = ?',
                   (task_id, project_id))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False, f"Task {task_id} not found in this project"

    task_title = result[0]

    # Log Git activity
    try:
        branch = subprocess.check_output(['git', 'branch', '--show-current'],
                                       stderr=subprocess.DEVNULL).decode().strip()
    except:
        branch = 'unknown'

    cursor.execute('''
        INSERT INTO git_activity (project_id, task_id, commit_hash, branch_name, message)
        VALUES (?, ?, ?, ?, ?)
    ''', (project_id, task_id, commit_hash, branch, message))

    # Update task status if specified
    if action in ['completed', 'in_progress', 'blocked']:
        cursor.execute('UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                      (action, task_id))

        # Update project timestamp
        cursor.execute('UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                       (project_id,))

    conn.commit()
    conn.close()

    return True, f"Updated task '{task_title}' -> {action}"

def main():
    """Main post-commit hook function."""
    repo_path = get_git_repo_path()
    if not repo_path:
        sys.exit(0)  # Not in a Git repo, silently exit

    project_result = find_project_by_path(repo_path)
    if not project_result:
        sys.exit(0)  # Project not tracked, silently exit

    project_id, project_name = project_result

    # Get latest commit info
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                            stderr=subprocess.DEVNULL).decode().strip()
        commit_message = subprocess.check_output(['git', 'log', '-1', '--pretty=format:%s'],
                                               stderr=subprocess.DEVNULL).decode().strip()
    except:
        sys.exit(0)  # Can't get Git info, silently exit

    # Parse commit message for task updates
    updates = parse_commit_message(commit_message)

    if updates:
        print(f"🔗 Project Tracker: Processing {len(updates)} task update(s) for '{project_name}'")

        for task_id, action in updates:
            success, message = update_task_from_git(task_id, action, commit_hash[:8],
                                                   commit_message, project_id)
            if success:
                print(f"   ✓ {message}")
            else:
                print(f"   ✗ {message}")

if __name__ == '__main__':
    main()