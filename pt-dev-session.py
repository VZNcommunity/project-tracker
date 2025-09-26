#!/usr/bin/env python3

import sqlite3
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse

def get_project_tracker_db():
    """Get path to project tracker database."""
    data_dir = Path.home() / '.local' / 'share' / 'project-tracker'
    return data_dir / 'tracker.db'

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    PURPLE = '\033[0;35m'
    NC = '\033[0m'

def log(message, color=Colors.NC):
    """Print colored log message."""
    print(f"{color}{message}{Colors.NC}")

def get_project_info(project_ref):
    """Get project information by ID or name."""
    db_path = get_project_tracker_db()
    if not db_path.exists():
        return None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        project_id = int(project_ref)
        cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
    except ValueError:
        cursor.execute('SELECT * FROM projects WHERE name LIKE ?', (f'%{project_ref}%',))

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'id': result[0],
            'name': result[1],
            'path': result[2],
            'description': result[3],
            'status': result[4]
        }
    return None

def get_active_tasks(project_id):
    """Get active tasks for the project."""
    db_path = get_project_tracker_db()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, title, status, priority
        FROM tasks
        WHERE project_id = ? AND status != 'completed'
        ORDER BY priority DESC, id ASC
    ''', (project_id,))

    tasks = cursor.fetchall()
    conn.close()
    return tasks

def optimize_system_for_development(project_type):
    """Optimize system performance for development work."""
    log("🚀 Optimizing system for development...", Colors.BLUE)

    # Set CPU governor to performance
    try:
        current_governor = subprocess.check_output(
            ['cat', '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor']
        ).decode().strip()

        if current_governor != 'performance':
            log(f"   CPU Governor: {current_governor} -> performance")
            # Use your existing gaming-performance.sh script for CPU optimization
            subprocess.run(['gaming-performance.sh', 'performance'], check=False)
        else:
            log("   ✓ CPU Governor: Already in performance mode", Colors.GREEN)
    except:
        log("   ⚠ Could not check CPU governor", Colors.YELLOW)

    # NVIDIA optimizations for TypeScript/heavy development
    if project_type in ['typescript', 'javascript'] or 'heavy' in project_type.lower():
        try:
            log("   Enabling NVIDIA performance for development workload...")
            subprocess.run(['nvidia-gaming-performance.sh', 'performance'], check=False)
        except:
            log("   ⚠ NVIDIA performance script not available", Colors.YELLOW)

def start_development_session(project_info, task_id=None):
    """Start an optimized development session."""
    log(f"{Colors.PURPLE}🛠️  Starting Development Session{Colors.NC}")
    log("=" * 50)

    project_name = project_info['name']
    project_path = project_info['path']
    project_id = project_info['id']

    log(f"📁 Project: {project_name} (ID: {project_id})")
    if project_path:
        log(f"📂 Path: {project_path}")

    # Detect project type
    if project_path and os.path.exists(project_path):
        project_type = detect_project_type(project_path)
        log(f"🔧 Type: {project_type}")

        # Optimize system
        optimize_system_for_development(project_type)

        # Show Git status
        try:
            os.chdir(project_path)
            branch = subprocess.check_output(['git', 'branch', '--show-current']).decode().strip()
            status = subprocess.check_output(['git', 'status', '--porcelain']).decode().strip()

            log(f"🌿 Git: {branch}")
            if status:
                log(f"   {Colors.YELLOW}⚠ {len(status.splitlines())} uncommitted changes{Colors.NC}")
            else:
                log(f"   {Colors.GREEN}✓ Working directory clean{Colors.NC}")
        except:
            log("   ⚠ Not a Git repository or error accessing Git", Colors.YELLOW)

    # Show active tasks
    tasks = get_active_tasks(project_id)
    if tasks:
        log(f"\n📋 Active Tasks ({len(tasks)}):")
        priority_symbols = {'high': '🔥', 'medium': '⚡', 'low': '📝'}
        status_symbols = {'pending': '⏸️', 'in_progress': '🔄', 'blocked': '🚫'}

        for tid, title, status, priority in tasks:
            priority_symbol = priority_symbols.get(priority, '📝')
            status_symbol = status_symbols.get(status, '⏸️')

            color = Colors.BLUE if status == 'in_progress' else Colors.YELLOW
            log(f"   {color}[{tid}] {status_symbol} {priority_symbol} {title}{Colors.NC}")

        if task_id:
            # Mark specific task as in progress
            try:
                subprocess.run(['pt', 'start', str(task_id)], check=True)
                log(f"\n✓ Marked task {task_id} as in progress", Colors.GREEN)
            except:
                log(f"\n✗ Could not start task {task_id}", Colors.RED)
    else:
        log(f"\n{Colors.CYAN}💡 No active tasks. Add some with: pt add {project_id} \"Task title\"{Colors.NC}")

    # Development environment tips
    log(f"\n{Colors.CYAN}💡 Development Session Tips:{Colors.NC}")
    log("   • Use Git commit messages with task references (pt:123 completed)")
    log("   • Monitor system performance with your custom scripts")
    log("   • Run pt status to track progress")

    if project_type == 'typescript':
        log("   • TypeScript: npm run dev for development server")
        log("   • Use npm run build to test compilation")
    elif project_type == 'python':
        log("   • Python: pip install -e . for development install")
        log("   • Run tests with pytest before completing tasks")

def detect_project_type(project_path):
    """Detect the type of project."""
    path = Path(project_path)

    if (path / 'package.json').exists():
        if (path / 'tsconfig.json').exists():
            return 'typescript'
        return 'javascript'
    elif (path / 'pyproject.toml').exists() or (path / 'setup.py').exists():
        return 'python'
    elif (path / 'Cargo.toml').exists():
        return 'rust'
    elif (path / 'go.mod').exists():
        return 'go'
    else:
        return 'general'

def end_development_session():
    """End development session and restore normal performance settings."""
    log(f"{Colors.BLUE}🛑 Ending Development Session{Colors.NC}")

    # Restore balanced performance
    try:
        subprocess.run(['gaming-performance.sh', 'balanced'], check=False)
        subprocess.run(['nvidia-gaming-performance.sh', 'balanced'], check=False)
        log("✓ System performance restored to balanced mode", Colors.GREEN)
    except:
        log("⚠ Could not restore balanced performance settings", Colors.YELLOW)

    log("💤 Development session ended")

def main():
    parser = argparse.ArgumentParser(description='Development Session Manager with Project Tracking')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Start session
    start_cmd = subparsers.add_parser('start', help='Start development session')
    start_cmd.add_argument('project', help='Project ID or name')
    start_cmd.add_argument('-t', '--task', type=int, help='Task ID to start working on')

    # End session
    end_cmd = subparsers.add_parser('end', help='End development session')

    # Status
    status_cmd = subparsers.add_parser('status', help='Show current development status')

    args = parser.parse_args()

    if args.command == 'start':
        project_info = get_project_info(args.project)
        if not project_info:
            log(f"✗ Project '{args.project}' not found", Colors.RED)
            sys.exit(1)

        start_development_session(project_info, args.task)

    elif args.command == 'end':
        end_development_session()

    elif args.command == 'status':
        # Show system status and current development environment
        log(f"{Colors.BLUE}🖥️  Development Environment Status{Colors.NC}")
        log("=" * 45)

        # CPU Governor
        try:
            governor = subprocess.check_output(
                ['cat', '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor']
            ).decode().strip()

            if governor == 'performance':
                log(f"⚡ CPU: {Colors.GREEN}Performance Mode{Colors.NC}")
            else:
                log(f"⚡ CPU: {Colors.YELLOW}{governor.title()} Mode{Colors.NC}")
        except:
            log("⚡ CPU: Unknown status")

        # NVIDIA Status (if available)
        try:
            subprocess.run(['nvidia-gaming-performance.sh', 'status'], check=False)
        except:
            pass

        # Overall project status
        log(f"\n{Colors.CYAN}📊 Project Tracking Overview:{Colors.NC}")
        subprocess.run(['pt', 'status'], check=False)

    else:
        parser.print_help()

if __name__ == '__main__':
    main()