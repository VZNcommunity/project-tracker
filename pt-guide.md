# Project Tracker (pt) - User Guide

A comprehensive CLI-based project and task management system designed for developers, integrated with Git workflows and system performance optimization.

## Overview

Project Tracker (`pt`) is a custom project management solution that combines:
- **CLI-based task management** (inspired by Taskwarrior)
- **Git integration** with automatic progress tracking
- **Claude Code integration** via enhanced CLAUDE.md files
- **System performance optimization** for development workflows
- **Integration with your existing 41+ custom scripts**

## Quick Start

### 1. Basic Project Management

```bash
# Add your existing projects
pt add-project "my-project" -p "/path/to/project" -d "Project description"

# List all projects
pt projects

# View project status
pt status "my-project"
```

### 2. Task Management

```bash
# Add tasks
pt add "my-project" "Implement user auth" -p high --due 2025-10-15
pt add "my-project" "Write tests" -p medium

# List tasks
pt list                    # All tasks
pt list -p "my-project"   # Project-specific
pt list -s pending        # By status

# Update task status
pt start 123              # Mark as in progress
pt complete 123           # Mark as completed
pt block 123              # Mark as blocked
```

### 3. Git Integration

```bash
# Setup Git hooks for automatic tracking
pt-setup-git             # For all projects
pt-setup-git "my-project" # For specific project

# In Git commits, use task references:
git commit -m "Add authentication pt:123 completed"
git commit -m "Working on user interface pt:124 progress"
git commit -m "Bug found in payment system pt:125 blocked"
```

### 4. Development Sessions

```bash
# Start optimized development session
pt-dev start "my-project" -t 123  # Also starts working on task 123
pt-dev status                     # Check environment status
pt-dev end                        # Restore balanced performance
```

### 5. Enhanced CLAUDE.md Integration

```bash
# Generate enhanced CLAUDE.md files with project tracking
pt-enhance-claude "my-project"    # Single project
pt-enhance-claude --all --backup  # All projects with backup
```

## Core Commands Reference

### Project Commands
- `pt add-project <name>` - Add new project
  - `-p, --path <path>` - Project directory path
  - `-d, --description <text>` - Project description
- `pt projects` - List all projects
  - `-s, --status <status>` - Filter by status
- `pt status [project]` - Show project status (or overall if no project)

### Task Commands
- `pt add <project> "<title>"` - Add new task
  - `-d, --description <text>` - Task description
  - `-p, --priority <high|medium|low>` - Task priority
  - `--due <YYYY-MM-DD>` - Due date
- `pt list` - List tasks
  - `-p, --project <project>` - Filter by project
  - `-s, --status <status>` - Filter by status
- `pt start <task_id>` - Mark task as in progress
- `pt complete <task_id>` - Mark task as completed
- `pt block <task_id>` - Mark task as blocked

### Integration Commands
- `pt-setup-git [project]` - Setup Git hooks
- `pt-enhance-claude <project>` - Enhance CLAUDE.md files
  - `--all` - Process all projects
  - `--backup` - Backup existing files
- `pt-dev start <project>` - Start development session
  - `-t, --task <id>` - Start working on specific task
- `pt-dev status` - Show development environment status
- `pt-dev end` - End development session

## Git Integration Features

### Automatic Task Updates via Commit Messages

Use these patterns in commit messages to automatically update task status:

- `pt:123 completed` or `pt:123 done` - Mark task as completed
- `pt:123 progress` or `pt:123 working` - Mark as in progress
- `pt:123 blocked` - Mark as blocked
- `pt:123` - Log activity (no status change)

### Examples:
```bash
git commit -m "Implement OAuth integration pt:45 completed"
git commit -m "Fix authentication bug pt:67 done"
git commit -m "Working on payment gateway pt:89 progress"
git commit -m "Database migration issue pt:12 blocked"
```

## Development Session Integration

The `pt-dev` command integrates with your existing performance scripts:

### System Optimization
- **CPU Governor**: Automatically switches to performance mode
- **NVIDIA GPU**: Enables maximum performance for development workloads
- **Memory**: Optimizes for development tools and compilers

### Project-Specific Optimizations
- **TypeScript**: Provides npm/Node.js specific tips
- **Python**: Includes pytest and pip guidance
- **Git Integration**: Shows branch status and uncommitted changes
- **Task Context**: Displays active tasks and priorities

### Performance Scripts Integration
- Uses your existing `gaming-performance.sh` for CPU optimization
- Integrates with `nvidia-gaming-performance.sh` for GPU performance
- Automatically restores balanced settings when ending session

## CLAUDE.md Enhancement

Enhanced CLAUDE.md files include:

### Project Tracking Section
- Tracker ID and status
- Quick command reference
- Active tasks list (auto-updated)

### Development Context
- Project type detection (TypeScript, Python, Rust, etc.)
- Appropriate command suggestions
- Performance considerations
- Git integration instructions

### Claude Code Integration
- Specialized agent type recommendations
- Project-specific capabilities
- Performance optimization notes

## File Structure

The project tracker creates the following structure:

```
~/.local/
├── bin/
│   ├── pt -> project-tracker.py          # Main CLI tool
│   ├── pt-setup-git                      # Git integration setup
│   ├── pt-enhance-claude                 # CLAUDE.md enhancement
│   ├── pt-dev                            # Development session manager
│   └── pt-claude-template.md             # CLAUDE.md template
└── share/
    └── project-tracker/
        └── tracker.db                     # SQLite database
```

## Database Schema

### Projects Table
- `id`: Primary key
- `name`: Project name
- `path`: File system path
- `description`: Project description
- `status`: Project status (active, archived, etc.)
- `created_at`, `updated_at`: Timestamps

### Tasks Table
- `id`: Primary key
- `project_id`: Foreign key to projects
- `title`: Task title
- `description`: Task description
- `status`: pending, in_progress, completed, blocked
- `priority`: high, medium, low
- `due_date`: Optional due date
- `created_at`, `updated_at`: Timestamps

### Git Activity Table
- `id`: Primary key
- `project_id`, `task_id`: Foreign keys
- `commit_hash`: Git commit hash
- `branch_name`: Git branch
- `message`: Commit message
- `timestamp`: Activity timestamp

## Integration with Existing Scripts

Your project tracker integrates with your existing 41+ custom scripts:

### Gaming & Performance Scripts
- `gaming-performance.sh` - CPU governor control
- `nvidia-gaming-performance.sh` - GPU performance optimization
- `optimize-gaming.sh` - Overall system optimization

### Development Workflow
- Automatically detects project types
- Provides context-appropriate suggestions
- Integrates with your existing development tools

### System Monitoring
- Uses existing system status scripts
- Provides unified development environment status
- Maintains compatibility with current workflow

## Best Practices

### 1. Project Organization
- Use descriptive project names
- Always include project paths for Git integration
- Add meaningful descriptions for context

### 2. Task Management
- Break large tasks into smaller, manageable pieces
- Use priority levels effectively (high for blockers, medium for features, low for nice-to-haves)
- Set due dates for time-sensitive tasks

### 3. Git Workflow
- Use consistent commit message patterns
- Reference task IDs in all relevant commits
- Review task status with `pt status` before major commits

### 4. Development Sessions
- Start sessions for focused work periods
- Use task-specific sessions to maintain context
- End sessions to restore system balance

### 5. Claude Code Integration
- Keep CLAUDE.md files updated with `pt-enhance-claude`
- Reference task IDs in Claude Code conversations
- Use project tracking context for better assistance

## Troubleshooting

### Common Issues

**Git hooks not triggering:**
```bash
# Re-run setup
pt-setup-git "project-name"

# Check hook permissions
ls -la /path/to/project/.git/hooks/post-commit
```

**Database issues:**
```bash
# Database location
ls -la ~/.local/share/project-tracker/

# Reset if needed (WARNING: loses all data)
rm ~/.local/share/project-tracker/tracker.db
```

**Performance script integration:**
```bash
# Test individual scripts
gaming-performance.sh status
nvidia-gaming-performance.sh status

# Check CPU governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

### Backup and Recovery

**Export project data:**
```bash
# Database is at:
~/.local/share/project-tracker/tracker.db

# Scripts are at:
~/.local/bin/pt*
```

**Restore from backup:**
```bash
# Copy database back to:
cp backup-tracker.db ~/.local/share/project-tracker/tracker.db

# Re-setup Git hooks:
pt-setup-git --all
```

## Advanced Usage

### Custom Workflow Integration

You can extend the project tracker by creating custom scripts that interact with the database:

```python
import sqlite3
from pathlib import Path

def get_db():
    return Path.home() / '.local' / 'share' / 'project-tracker' / 'tracker.db'

def get_active_projects():
    conn = sqlite3.connect(get_db())
    cursor = conn.cursor()
    cursor.execute('SELECT name, path FROM projects WHERE status = "active"')
    return cursor.fetchall()
```

### Automation Scripts

Create scripts that automatically:
- Update task status based on external events
- Generate progress reports
- Sync with external project management tools
- Create backups of project data

## Future Enhancements

The system is designed to be extensible. Potential improvements:

1. **Web Dashboard**: Terminal-based or web interface for visualization
2. **Time Tracking**: Built-in time tracking for tasks
3. **Reporting**: Advanced analytics and progress reports
4. **External Integration**: Sync with GitHub Issues, Jira, etc.
5. **Team Features**: Multi-user support and collaboration
6. **Mobile Companion**: Simple mobile app for status updates

## Support

For issues or improvements:
1. Check the troubleshooting section
2. Verify integration with existing scripts
3. Test individual components separately
4. Consider system-specific adjustments

The project tracker is built to work specifically with your Arch Linux environment and existing script ecosystem, providing a personalized project management solution that grows with your development workflow.