#!/usr/bin/env python3

import sqlite3
import os
import sys
from pathlib import Path
import json

def get_project_tracker_db():
    """Get path to project tracker database."""
    data_dir = Path.home() / '.local' / 'share' / 'project-tracker'
    return data_dir / 'tracker.db'

def get_template_content():
    """Get the CLAUDE.md template content."""
    template_path = Path.home() / '.local' / 'bin' / 'pt-claude-template.md'
    with open(template_path, 'r') as f:
        return f.read()

def get_active_tasks(project_id):
    """Get active tasks for a project formatted for CLAUDE.md."""
    db_path = get_project_tracker_db()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, title, description, status, priority
        FROM tasks
        WHERE project_id = ? AND status != 'completed'
        ORDER BY priority DESC, id ASC
    ''', (project_id,))

    tasks = cursor.fetchall()
    conn.close()

    if not tasks:
        return "No active tasks"

    task_list = []
    priority_symbols = {'high': '🔥', 'medium': '⚡', 'low': '📝'}
    status_symbols = {'pending': '⏸️', 'in_progress': '🔄', 'blocked': '🚫'}

    for tid, title, desc, status, priority in tasks:
        priority_symbol = priority_symbols.get(priority, '📝')
        status_symbol = status_symbols.get(status, '⏸️')

        task_item = f"- {status_symbol} **[{tid}]** {priority_symbol} {title}"
        if desc:
            task_item += f"\n  - {desc}"

        task_list.append(task_item)

    return '\n'.join(task_list)

def detect_project_type(project_path):
    """Detect project type and return appropriate configuration."""
    path = Path(project_path)

    # Check for various project indicators
    if (path / 'package.json').exists():
        with open(path / 'package.json') as f:
            package_data = json.load(f)
            dependencies = {**package_data.get('dependencies', {}),
                          **package_data.get('devDependencies', {})}

            if 'typescript' in dependencies or (path / 'tsconfig.json').exists():
                return {
                    'agent_type': 'typescript',
                    'tech_stack': 'TypeScript/Node.js',
                    'commands': 'npm install, npm run build, npm test',
                    'agent_capabilities': 'TypeScript compilation, Node.js modules, package management'
                }
            else:
                return {
                    'agent_type': 'javascript',
                    'tech_stack': 'JavaScript/Node.js',
                    'commands': 'npm install, npm run build, npm test',
                    'agent_capabilities': 'JavaScript modules, Node.js runtime, package management'
                }

    elif (path / 'pyproject.toml').exists() or (path / 'setup.py').exists():
        return {
            'agent_type': 'python',
            'tech_stack': 'Python',
            'commands': 'pip install -e ., python -m pytest, pre-commit run --all-files',
            'agent_capabilities': 'Python packages, testing frameworks, code quality tools'
        }

    elif (path / 'Cargo.toml').exists():
        return {
            'agent_type': 'rust',
            'tech_stack': 'Rust',
            'commands': 'cargo build, cargo test, cargo run',
            'agent_capabilities': 'Rust compilation, dependency management, testing'
        }

    else:
        return {
            'agent_type': 'general-purpose',
            'tech_stack': 'Mixed/Unknown',
            'commands': 'See project documentation',
            'agent_capabilities': 'General file operations and code analysis'
        }

def generate_claude_md(project_id, project_name, project_path, description):
    """Generate enhanced CLAUDE.md content."""
    template = get_template_content()
    active_tasks = get_active_tasks(project_id)
    project_config = detect_project_type(project_path)

    # Replace template placeholders
    content = template.replace('[PROJECT_ID]', str(project_id))
    content = content.replace('[PROJECT_STATUS]', 'Active')
    content = content.replace('[PROJECT_PRIORITY]', 'Medium')
    content = content.replace('[ACTIVE_TASKS_PLACEHOLDER]', active_tasks)
    content = content.replace('[TECH_STACK_DESCRIPTION]', project_config['tech_stack'])
    content = content.replace('[PROJECT_COMMANDS]', project_config['commands'])
    content = content.replace('[AGENT_TYPE]', project_config['agent_type'])
    content = content.replace('[AGENT_CAPABILITIES]', project_config['agent_capabilities'])

    # Add project-specific content
    content = content.replace('[DEVELOPMENT_WORKFLOW]',
        f"Standard {project_config['tech_stack']} development workflow with Git integration and project tracking.")

    content = content.replace('[PERFORMANCE_NOTES]',
        f"Project is tracked via pt:{project_id}. Use Git commit messages with task references for automatic updates.")

    content = content.replace('[FILE_STRUCTURE_OVERVIEW]',
        f"Standard {project_config['tech_stack']} project structure. See README.md for details.")

    content = content.replace('[TESTING_APPROACH]',
        f"Follow {project_config['tech_stack']} testing best practices. Run tests before marking tasks as completed.")

    content = content.replace('[DEPLOYMENT_INFO]',
        "See project documentation for deployment procedures.")

    content = content.replace('[CUSTOM_GUIDELINES]',
        f"- This project is tracked with pt:{project_id}\n- Use task references in Git commits\n- Update project tracker when completing milestones")

    return content

def main():
    """Main function to enhance CLAUDE.md files."""
    if len(sys.argv) < 2:
        print("Usage: pt-enhance-claude <project_id_or_name> [--backup]")
        print("       pt-enhance-claude --all [--backup]")
        sys.exit(1)

    backup = '--backup' in sys.argv

    db_path = get_project_tracker_db()
    if not db_path.exists():
        print("✗ Project tracker database not found")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if sys.argv[1] == '--all':
        # Process all projects
        cursor.execute('SELECT id, name, path, description FROM projects WHERE path IS NOT NULL')
        projects = cursor.fetchall()

        if not projects:
            print("✗ No projects with paths found")
            sys.exit(1)

        success_count = 0
        for pid, name, path, desc in projects:
            if process_project(pid, name, path, desc, backup):
                success_count += 1

        print(f"\n✓ Enhanced CLAUDE.md for {success_count}/{len(projects)} projects")

    else:
        # Process specific project
        project_ref = sys.argv[1]
        try:
            project_id = int(project_ref)
            cursor.execute('SELECT id, name, path, description FROM projects WHERE id = ?', (project_id,))
        except ValueError:
            cursor.execute('SELECT id, name, path, description FROM projects WHERE name LIKE ?', (f'%{project_ref}%',))

        result = cursor.fetchone()
        if not result:
            print(f"✗ Project '{project_ref}' not found")
            sys.exit(1)

        pid, name, path, desc = result
        if process_project(pid, name, path, desc, backup):
            print("✓ CLAUDE.md enhanced successfully")

    conn.close()

def process_project(project_id, name, path, description, backup):
    """Process a single project."""
    if not path or not os.path.exists(path):
        print(f"✗ {name} - Path '{path}' does not exist")
        return False

    claude_md_path = Path(path) / 'CLAUDE.md'

    try:
        # Backup existing file if requested
        if backup and claude_md_path.exists():
            backup_path = claude_md_path.with_suffix('.md.backup')
            claude_md_path.rename(backup_path)
            print(f"📦 {name} - Backed up existing CLAUDE.md")

        # Generate new content
        content = generate_claude_md(project_id, name, path, description)

        # Write enhanced CLAUDE.md
        with open(claude_md_path, 'w') as f:
            f.write(content)

        print(f"✓ {name} - Enhanced CLAUDE.md created")
        return True

    except Exception as e:
        print(f"✗ {name} - Failed to enhance CLAUDE.md: {e}")
        return False

if __name__ == '__main__':
    main()