#!/usr/bin/env python3

import sqlite3
import argparse
import os
import sys
import json
import subprocess
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import textwrap

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    PURPLE = '\033[0;35m'
    NC = '\033[0m'  # No Color

class ProjectTracker:
    def __init__(self):
        self.data_dir = Path.home() / '.local' / 'share' / 'project-tracker'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / 'tracker.db'
        self.init_database()

    def init_database(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                path TEXT,
                description TEXT,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                due_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')

        # Git integration table for tracking commits/branches
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS git_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                task_id INTEGER,
                commit_hash TEXT,
                branch_name TEXT,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')

        conn.commit()
        conn.close()

    def log(self, message: str, color: str = Colors.NC):
        """Print colored log message."""
        print(f"{color}{message}{Colors.NC}")

    def get_git_info(self, path: str) -> Optional[Dict]:
        """Get Git repository information from a path."""
        try:
            os.chdir(path)
            # Get current branch
            branch = subprocess.check_output(['git', 'branch', '--show-current'],
                                          stderr=subprocess.DEVNULL).decode().strip()
            # Get latest commit
            commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                          stderr=subprocess.DEVNULL).decode().strip()
            # Get repo status
            status = subprocess.check_output(['git', 'status', '--porcelain'],
                                          stderr=subprocess.DEVNULL).decode().strip()
            return {
                'branch': branch,
                'commit': commit[:8],
                'has_changes': bool(status)
            }
        except:
            return None

    def add_project(self, name: str, path: str = None, description: str = None):
        """Add a new project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO projects (name, path, description)
                VALUES (?, ?, ?)
            ''', (name, path, description))
            project_id = cursor.lastrowid
            conn.commit()

            self.log(f"✓ Added project '{name}' (ID: {project_id})", Colors.GREEN)

            # If path provided, check for Git info
            if path and os.path.exists(path):
                git_info = self.get_git_info(path)
                if git_info:
                    self.log(f"  Git: {git_info['branch']} ({git_info['commit']})", Colors.CYAN)

        except sqlite3.IntegrityError:
            self.log(f"✗ Project '{name}' already exists", Colors.RED)
        finally:
            conn.close()

    def list_projects(self, status_filter: str = None):
        """List all projects with their status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = 'SELECT * FROM projects'
        params = []
        if status_filter:
            query += ' WHERE status = ?'
            params.append(status_filter)
        query += ' ORDER BY updated_at DESC'

        cursor.execute(query, params)
        projects = cursor.fetchall()

        if not projects:
            self.log("No projects found", Colors.YELLOW)
            conn.close()
            return

        self.log(f"{Colors.BLUE}📁 Projects Overview{Colors.NC}")
        self.log("=" * 50)

        for project in projects:
            pid, name, path, desc, status, created, updated = project

            # Get task count
            cursor.execute('SELECT COUNT(*) FROM tasks WHERE project_id = ?', (pid,))
            task_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM tasks WHERE project_id = ? AND status = "completed"', (pid,))
            completed_count = cursor.fetchone()[0]

            # Status color
            status_color = Colors.GREEN if status == 'active' else Colors.YELLOW

            self.log(f"{Colors.CYAN}[{pid}]{Colors.NC} {name} {status_color}({status}){Colors.NC}")
            if desc:
                wrapped_desc = textwrap.fill(desc, width=60, initial_indent="    ", subsequent_indent="    ")
                print(wrapped_desc)

            if path:
                self.log(f"    📂 {path}", Colors.BLUE)

            self.log(f"    📊 Tasks: {completed_count}/{task_count} completed")

            # Git info if available
            if path and os.path.exists(path):
                git_info = self.get_git_info(path)
                if git_info:
                    changes_indicator = " (uncommitted changes)" if git_info['has_changes'] else ""
                    self.log(f"    🌿 Git: {git_info['branch']} ({git_info['commit']}){changes_indicator}", Colors.PURPLE)

            print()

        conn.close()

    def add_task(self, project_ref: str, title: str, description: str = None,
                 priority: str = 'medium', due_date: str = None):
        """Add a task to a project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Find project by ID or name
        try:
            project_id = int(project_ref)
            cursor.execute('SELECT name FROM projects WHERE id = ?', (project_id,))
        except ValueError:
            cursor.execute('SELECT id, name FROM projects WHERE name LIKE ?', (f'%{project_ref}%',))
            result = cursor.fetchone()
            if result:
                project_id, project_name = result
            else:
                self.log(f"✗ Project '{project_ref}' not found", Colors.RED)
                conn.close()
                return

        # Parse due date if provided
        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                self.log(f"✗ Invalid date format. Use YYYY-MM-DD", Colors.RED)
                conn.close()
                return

        cursor.execute('''
            INSERT INTO tasks (project_id, title, description, priority, due_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (project_id, title, description, priority, parsed_due_date))

        task_id = cursor.lastrowid
        conn.commit()

        # Update project timestamp
        cursor.execute('UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (project_id,))
        conn.commit()

        priority_color = {
            'high': Colors.RED,
            'medium': Colors.YELLOW,
            'low': Colors.CYAN
        }.get(priority, Colors.NC)

        self.log(f"✓ Added task '{title}' to project (ID: {task_id})", Colors.GREEN)
        self.log(f"  Priority: {priority_color}{priority.upper()}{Colors.NC}")
        if due_date:
            self.log(f"  Due: {due_date}")

        conn.close()

    def list_tasks(self, project_ref: str = None, status_filter: str = None):
        """List tasks, optionally filtered by project and/or status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = '''
            SELECT t.id, t.title, t.description, t.status, t.priority, t.due_date,
                   p.name as project_name, t.created_at
            FROM tasks t
            JOIN projects p ON t.project_id = p.id
        '''
        params = []

        conditions = []
        if project_ref:
            try:
                project_id = int(project_ref)
                conditions.append('t.project_id = ?')
                params.append(project_id)
            except ValueError:
                conditions.append('p.name LIKE ?')
                params.append(f'%{project_ref}%')

        if status_filter:
            conditions.append('t.status = ?')
            params.append(status_filter)

        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)

        query += ' ORDER BY t.priority DESC, t.due_date ASC, t.created_at DESC'

        cursor.execute(query, params)
        tasks = cursor.fetchall()

        if not tasks:
            self.log("No tasks found", Colors.YELLOW)
            conn.close()
            return

        self.log(f"{Colors.BLUE}📋 Tasks Overview{Colors.NC}")
        self.log("=" * 60)

        for task in tasks:
            tid, title, desc, status, priority, due_date, project_name, created = task

            # Status colors
            status_colors = {
                'pending': Colors.YELLOW,
                'in_progress': Colors.BLUE,
                'completed': Colors.GREEN,
                'blocked': Colors.RED
            }

            priority_symbols = {
                'high': '🔥',
                'medium': '⚡',
                'low': '📝'
            }

            status_color = status_colors.get(status, Colors.NC)
            priority_symbol = priority_symbols.get(priority, '📝')

            self.log(f"{Colors.CYAN}[{tid}]{Colors.NC} {priority_symbol} {title} {status_color}({status}){Colors.NC}")
            self.log(f"    📁 Project: {project_name}")

            if desc:
                wrapped_desc = textwrap.fill(desc, width=70, initial_indent="    📄 ", subsequent_indent="       ")
                print(wrapped_desc)

            if due_date:
                due_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                days_left = (due_obj - date.today()).days
                if days_left < 0:
                    self.log(f"    📅 Due: {due_date} ({Colors.RED}OVERDUE by {abs(days_left)} days{Colors.NC})")
                elif days_left == 0:
                    self.log(f"    📅 Due: {due_date} ({Colors.YELLOW}TODAY{Colors.NC})")
                elif days_left <= 7:
                    self.log(f"    📅 Due: {due_date} ({Colors.YELLOW}{days_left} days left{Colors.NC})")
                else:
                    self.log(f"    📅 Due: {due_date} ({days_left} days left)")

            print()

        conn.close()

    def update_task_status(self, task_id: int, new_status: str):
        """Update task status."""
        valid_statuses = ['pending', 'in_progress', 'completed', 'blocked']
        if new_status not in valid_statuses:
            self.log(f"✗ Invalid status. Use: {', '.join(valid_statuses)}", Colors.RED)
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT title, project_id FROM tasks WHERE id = ?', (task_id,))
        result = cursor.fetchone()
        if not result:
            self.log(f"✗ Task {task_id} not found", Colors.RED)
            conn.close()
            return

        title, project_id = result
        cursor.execute('UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                      (new_status, task_id))

        # Update project timestamp
        cursor.execute('UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (project_id,))
        conn.commit()

        status_colors = {
            'pending': Colors.YELLOW,
            'in_progress': Colors.BLUE,
            'completed': Colors.GREEN,
            'blocked': Colors.RED
        }

        status_color = status_colors.get(new_status, Colors.NC)
        self.log(f"✓ Updated '{title}' to {status_color}{new_status}{Colors.NC}", Colors.GREEN)

        conn.close()

    def project_status(self, project_ref: str = None):
        """Show detailed project status with Git integration."""
        if project_ref is None:
            self.log("📊 Overall Status", Colors.BLUE)
            self.log("=" * 40)
            self.show_overall_stats()
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Find project
        try:
            project_id = int(project_ref)
            cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        except ValueError:
            cursor.execute('SELECT * FROM projects WHERE name LIKE ?', (f'%{project_ref}%',))

        project = cursor.fetchone()
        if not project:
            self.log(f"✗ Project '{project_ref}' not found", Colors.RED)
            conn.close()
            return

        pid, name, path, desc, status, created, updated = project

        self.log(f"{Colors.BLUE}📁 {name} - Detailed Status{Colors.NC}")
        self.log("=" * 50)

        if desc:
            self.log(f"📄 Description: {desc}")

        if path:
            self.log(f"📂 Path: {path}")

        # Git information
        if path and os.path.exists(path):
            git_info = self.get_git_info(path)
            if git_info:
                self.log(f"🌿 Git Branch: {git_info['branch']}")
                self.log(f"📝 Latest Commit: {git_info['commit']}")
                if git_info['has_changes']:
                    self.log(f"{Colors.YELLOW}⚠ Uncommitted changes present{Colors.NC}")
                else:
                    self.log(f"{Colors.GREEN}✓ Working directory clean{Colors.NC}")

        # Task statistics
        cursor.execute('SELECT status, COUNT(*) FROM tasks WHERE project_id = ? GROUP BY status', (pid,))
        status_counts = dict(cursor.fetchall())

        total_tasks = sum(status_counts.values())
        if total_tasks > 0:
            self.log(f"\n📊 Task Statistics (Total: {total_tasks})")
            for status, count in status_counts.items():
                percentage = (count / total_tasks) * 100
                status_colors = {
                    'pending': Colors.YELLOW,
                    'in_progress': Colors.BLUE,
                    'completed': Colors.GREEN,
                    'blocked': Colors.RED
                }
                color = status_colors.get(status, Colors.NC)
                self.log(f"  {color}{status.replace('_', ' ').title()}: {count} ({percentage:.1f}%){Colors.NC}")
        else:
            self.log(f"\n{Colors.YELLOW}No tasks found for this project{Colors.NC}")

        conn.close()

    def show_overall_stats(self):
        """Show overall statistics across all projects."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Project counts
        cursor.execute('SELECT COUNT(*) FROM projects WHERE status = "active"')
        active_projects = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM projects')
        total_projects = cursor.fetchone()[0]

        # Task counts
        cursor.execute('SELECT status, COUNT(*) FROM tasks GROUP BY status')
        task_counts = dict(cursor.fetchall())

        total_tasks = sum(task_counts.values())

        self.log(f"📁 Projects: {active_projects} active / {total_projects} total")

        if total_tasks > 0:
            self.log(f"📋 Tasks: {total_tasks} total")

            # Progress bar for completed tasks
            completed = task_counts.get('completed', 0)
            if total_tasks > 0:
                progress = completed / total_tasks
                bar_length = 20
                filled = int(progress * bar_length)
                bar = '█' * filled + '░' * (bar_length - filled)
                self.log(f"   Progress: [{bar}] {progress:.1%} ({completed}/{total_tasks})")

            # Status breakdown
            status_colors = {
                'pending': Colors.YELLOW,
                'in_progress': Colors.BLUE,
                'completed': Colors.GREEN,
                'blocked': Colors.RED
            }

            for status, count in task_counts.items():
                if count > 0:
                    color = status_colors.get(status, Colors.NC)
                    self.log(f"   {color}{status.replace('_', ' ').title()}: {count}{Colors.NC}")
        else:
            self.log("📋 No tasks found")

        conn.close()

def main():
    tracker = ProjectTracker()

    parser = argparse.ArgumentParser(description='Project Tracker - CLI project and task management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Project commands
    add_project = subparsers.add_parser('add-project', help='Add a new project')
    add_project.add_argument('name', help='Project name')
    add_project.add_argument('-p', '--path', help='Project path')
    add_project.add_argument('-d', '--description', help='Project description')

    list_projects = subparsers.add_parser('projects', help='List all projects')
    list_projects.add_argument('-s', '--status', help='Filter by status')

    # Task commands
    add_task = subparsers.add_parser('add', help='Add a new task')
    add_task.add_argument('project', help='Project ID or name')
    add_task.add_argument('title', help='Task title')
    add_task.add_argument('-d', '--description', help='Task description')
    add_task.add_argument('-p', '--priority', choices=['low', 'medium', 'high'], default='medium')
    add_task.add_argument('--due', help='Due date (YYYY-MM-DD)')

    list_tasks = subparsers.add_parser('list', help='List tasks')
    list_tasks.add_argument('-p', '--project', help='Filter by project')
    list_tasks.add_argument('-s', '--status', help='Filter by status')

    # Status commands
    complete = subparsers.add_parser('complete', help='Mark task as completed')
    complete.add_argument('task_id', type=int, help='Task ID')

    start = subparsers.add_parser('start', help='Mark task as in progress')
    start.add_argument('task_id', type=int, help='Task ID')

    block = subparsers.add_parser('block', help='Mark task as blocked')
    block.add_argument('task_id', type=int, help='Task ID')

    status = subparsers.add_parser('status', help='Show project status')
    status.add_argument('project', nargs='?', help='Project ID or name (optional)')

    args = parser.parse_args()

    if args.command == 'add-project':
        tracker.add_project(args.name, args.path, args.description)
    elif args.command == 'projects':
        tracker.list_projects(args.status)
    elif args.command == 'add':
        tracker.add_task(args.project, args.title, args.description, args.priority, args.due)
    elif args.command == 'list':
        tracker.list_tasks(args.project, args.status)
    elif args.command == 'complete':
        tracker.update_task_status(args.task_id, 'completed')
    elif args.command == 'start':
        tracker.update_task_status(args.task_id, 'in_progress')
    elif args.command == 'block':
        tracker.update_task_status(args.task_id, 'blocked')
    elif args.command == 'status':
        tracker.project_status(args.project)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()