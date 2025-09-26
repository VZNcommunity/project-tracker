# Project Tracker (pt)

A comprehensive CLI-based project and task management system designed for developers, with Git integration, system performance optimization, and Claude Code enhancement.

## Features

🛠️ **CLI Project Management**
- Taskwarrior-inspired interface with colored output
- SQLite database for reliable data storage
- Project and task CRUD operations with priorities and due dates

🔗 **Git Integration**
- Automatic Git hooks for commit-based task updates
- Smart commit message parsing (`pt:123 completed`)
- Branch and repository activity tracking

🚀 **Development Session Optimization**
- System performance optimization for coding sessions
- Integration with gaming-performance and NVIDIA scripts
- Project-type aware development environment setup

📝 **Claude Code Integration**
- Enhanced CLAUDE.md files with project tracking metadata
- Automatic project type detection and agent recommendations
- Active task listings and quick command references

🤖 **AI-Powered Features** *(New!)*
- Natural language task creation using Google AI Studio
- Intelligent project consultation and guidance
- Task analysis with implementation recommendations
- Interactive AI chat sessions with full project context

## Quick Start

```bash
# Install (copy scripts to ~/.local/bin/)
./install.sh

# Add your first project
pt add-project "my-project" -p "/path/to/project" -d "Project description"

# Add tasks
pt add "my-project" "Implement feature X" -p high --due 2025-10-15

# Setup Git integration
pt-setup-git "my-project"

# Start development session (optimizes system performance)
pt-dev start "my-project" -t 1

# Use Git commit messages to update tasks
git commit -m "Add user authentication pt:1 completed"

# AI Features (requires Google AI Studio API key)
pt-ai config --api-key YOUR_GOOGLE_AI_KEY
pt-ai add "my-project" "create user dashboard with real-time analytics"
pt-ai chat "my-project" "how should I implement caching for this API?"
```

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd project-tracker
```

2. Run the install script:
```bash
./install.sh
```

3. Start using:
```bash
pt-help  # Get started
```

## Commands

### Core Project Management
- `pt add-project <name>` - Add new project
- `pt projects` - List all projects
- `pt status [project]` - Show status overview
- `pt add <project> "<title>"` - Add task
- `pt list` - List tasks
- `pt start/complete/block <task_id>` - Update task status

### Git Integration
- `pt-setup-git [project]` - Install Git hooks
- Use `pt:123 completed` in commit messages for automatic updates

### Development Sessions
- `pt-dev start <project> [-t task_id]` - Start optimized dev session
- `pt-dev status` - Show system and project status
- `pt-dev end` - End session and restore balanced performance

### Claude Code Enhancement
- `pt-enhance-claude <project|--all>` - Generate enhanced CLAUDE.md files

### AI Features
- `pt-ai config --api-key <key>` - Configure Google AI Studio
- `pt-ai add <project> "<description>"` - Create tasks from natural language
- `pt-ai chat <project> "<question>"` - Ask AI about your project
- `pt-ai analyze <task_id>` - Get AI insights on tasks
- `pt-ai interactive <project>` - Start interactive AI session

## Architecture

- **project-tracker.py** - Main CLI application with SQLite database
- **pt-git-hook.py** - Git post-commit hook for automatic task updates
- **pt-setup-git.py** - Git integration setup and management
- **pt-enhance-claude.py** - CLAUDE.md file enhancement with tracking metadata
- **pt-dev-session.py** - Development session management with performance optimization
- **pt-ai.py** - AI integration with Google AI Studio for natural language processing
- **pt-claude-template.md** - Template for enhanced CLAUDE.md files
- **pt-help** - Comprehensive help system

## Database Schema

### Projects
- ID, name, path, description, status, timestamps

### Tasks
- ID, project_id, title, description, status, priority, due_date, timestamps
- AI fields: ai_generated, ai_estimate_hours, ai_complexity

### Git Activity
- ID, project_id, task_id, commit_hash, branch, message, timestamp

### AI Features
- ai_conversations: Conversation history with project context
- ai_insights: AI-generated analysis and recommendations

## Integration Features

### Git Workflow
Automatic task updates via commit message patterns:
- `pt:123 completed` - Mark task as completed
- `pt:123 progress` - Mark as in progress
- `pt:123 blocked` - Mark as blocked
- `pt:123` - Log activity

### System Performance
Integrates with existing performance scripts:
- CPU governor management
- NVIDIA GPU performance optimization
- Project-type specific development environment setup

### Claude Code Enhancement
Generated CLAUDE.md files include:
- Project tracking metadata and commands
- Active task listings (auto-updated)
- Project-specific agent recommendations
- Development workflow guidance

## Requirements

- Python 3.6+
- Git
- SQLite3
- Linux environment (tested on Arch Linux)
- Optional: gaming-performance.sh and nvidia-gaming-performance.sh scripts
- Optional: Google AI Studio API key for AI features

## Contributing

This is a personalized project management system designed for a specific development environment. However, the architecture is modular and can be adapted for other setups.

## License

MIT License - Feel free to adapt and modify for your own development workflow.

## Screenshots

```
🛠️  Project Tracker (pt) - Overview
====================================

A comprehensive CLI project management system with:
  • Task and project tracking
  • Git integration with automatic updates
  • Development session optimization
  • Claude Code integration via enhanced CLAUDE.md
  • Integration with your existing performance scripts

📊 Overall Status
========================================
📁 Projects: 2 active / 2 total
📋 Tasks: 2 total
   Progress: [██████████░░░░░░░░░░] 50.0% (1/2)
   ✓ Completed: 1
   ⏸️  Pending: 1
```