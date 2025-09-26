#!/usr/bin/env python3

import os
import sys
import sqlite3
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Any
import subprocess
import textwrap

# Check if we're running from the project directory with venv
project_dir = Path(__file__).parent
venv_python = project_dir / 'venv' / 'bin' / 'python'
if venv_python.exists() and sys.executable != str(venv_python):
    # Re-run with the virtual environment Python
    os.execv(str(venv_python), [str(venv_python)] + sys.argv)

try:
    import google.generativeai as genai
except ImportError:
    print("Error: google-generativeai not installed. Run:")
    print("cd ~/Development/project-tracker && source venv/bin/activate && pip install google-generativeai")
    sys.exit(1)

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    PURPLE = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'

class ProjectTrackerAI:
    def __init__(self):
        self.data_dir = Path.home() / '.local' / 'share' / 'project-tracker'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / 'tracker.db'
        self.config_path = self.data_dir / 'ai_config.json'

        self.init_ai_database()
        self.load_config()
        self.setup_genai()

    def log(self, message: str, color: str = Colors.NC):
        """Print colored log message."""
        print(f"{color}{message}{Colors.NC}")

    def init_ai_database(self):
        """Initialize AI-related database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # AI conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')

        # AI insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                task_id INTEGER,
                insight_type TEXT,
                content TEXT,
                confidence REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')

        # Extend tasks table with AI metadata (with error handling for existing columns)
        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN ai_generated BOOLEAN DEFAULT FALSE')
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN ai_estimate_hours REAL')
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN ai_complexity TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.commit()
        conn.close()

    def load_config(self):
        """Load AI configuration."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'api_key': None,
                'model': 'gemini-1.5-pro',
                'max_tokens': 8192,
                'temperature': 0.7
            }
            self.save_config()

    def save_config(self):
        """Save AI configuration."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        # Secure the config file
        os.chmod(self.config_path, 0o600)

    def setup_genai(self):
        """Setup Google Generative AI."""
        api_key = self.config.get('api_key') or os.getenv('GOOGLE_AI_API_KEY')

        if not api_key:
            self.log("⚠ Google AI API key not configured.", Colors.YELLOW)
            self.log("Set it with: pt ai config --api-key YOUR_API_KEY", Colors.CYAN)
            self.log("Or set environment variable: export GOOGLE_AI_API_KEY=your_key", Colors.CYAN)
            return False

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.config['model'])
            return True
        except Exception as e:
            self.log(f"✗ Failed to setup Google AI: {e}", Colors.RED)
            return False

    def get_project_info(self, project_ref: str) -> Optional[Dict]:
        """Get project information by ID or name."""
        conn = sqlite3.connect(self.db_path)
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

    def get_project_context(self, project_id: int) -> str:
        """Get comprehensive project context for AI."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get project details
        cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        project = cursor.fetchone()

        if not project:
            return ""

        # Get active tasks
        cursor.execute('''
            SELECT id, title, description, status, priority, due_date
            FROM tasks
            WHERE project_id = ? AND status != 'completed'
            ORDER BY priority DESC, id ASC
        ''', (project_id,))

        active_tasks = cursor.fetchall()

        # Get recent completed tasks
        cursor.execute('''
            SELECT id, title, description
            FROM tasks
            WHERE project_id = ? AND status = 'completed'
            ORDER BY updated_at DESC
            LIMIT 5
        ''', (project_id,))

        completed_tasks = cursor.fetchall()

        # Get recent Git activity
        cursor.execute('''
            SELECT commit_hash, branch_name, message, timestamp
            FROM git_activity
            WHERE project_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (project_id,))

        git_activity = cursor.fetchall()

        conn.close()

        # Build context string
        context = f"""Project: {project[1]}
Description: {project[3] or 'No description'}
Path: {project[2] or 'No path specified'}
Status: {project[4]}

"""

        if active_tasks:
            context += "Active Tasks:\n"
            for task in active_tasks:
                context += f"- [{task[0]}] {task[1]} (Priority: {task[4]}, Status: {task[3]})\n"
                if task[2]:  # description
                    context += f"  Description: {task[2]}\n"
            context += "\n"

        if completed_tasks:
            context += "Recently Completed Tasks:\n"
            for task in completed_tasks:
                context += f"- [{task[0]}] {task[1]}\n"
            context += "\n"

        if git_activity:
            context += "Recent Git Activity:\n"
            for activity in git_activity:
                context += f"- {activity[0][:8]} on {activity[1]}: {activity[2]}\n"
            context += "\n"

        # Add file structure if path exists
        if project[2] and os.path.exists(project[2]):
            try:
                result = subprocess.run(['find', project[2], '-type', 'f', '-name', '*.py', '-o', '-name', '*.js', '-o', '-name', '*.ts', '-o', '-name', '*.md'],
                                      capture_output=True, text=True, timeout=5)
                if result.stdout:
                    files = result.stdout.strip().split('\n')[:20]  # Limit to 20 files
                    context += "Key Files:\n"
                    for file in files:
                        rel_path = os.path.relpath(file, project[2])
                        context += f"- {rel_path}\n"
                    context += "\n"
            except:
                pass

        return context

    def chat(self, project_ref: str, message: str, conversation_id: str = None) -> str:
        """Have a conversation with AI about the project."""
        if not hasattr(self, 'model'):
            return "AI not configured. Run 'pt ai config --api-key YOUR_API_KEY' first."

        project_info = self.get_project_info(project_ref)
        if not project_info:
            return f"Project '{project_ref}' not found."

        project_context = self.get_project_context(project_info['id'])

        # Create conversation prompt
        system_prompt = f"""You are an AI assistant for the Project Tracker tool. You help developers manage their projects and code.

Current Project Context:
{project_context}

Instructions:
- Provide helpful, specific advice based on the project context
- When suggesting tasks, be specific and actionable
- Consider the existing codebase and project structure
- If asked to create tasks, format them clearly
- Be concise but thorough
- Reference existing tasks and files when relevant

User's question: {message}"""

        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = f"conv_{project_info['id']}_{len(message)}"

            response = self.model.generate_content(system_prompt)

            # Store conversation in database
            self.store_conversation(project_info['id'], conversation_id, 'user', message)
            self.store_conversation(project_info['id'], conversation_id, 'assistant', response.text)

            return response.text

        except Exception as e:
            return f"Error communicating with AI: {e}"

    def store_conversation(self, project_id: int, conversation_id: str, role: str, content: str):
        """Store conversation in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO ai_conversations (project_id, conversation_id, role, content)
            VALUES (?, ?, ?, ?)
        ''', (project_id, conversation_id, role, content))

        conn.commit()
        conn.close()

    def create_task_from_nl(self, project_ref: str, description: str) -> bool:
        """Create a task from natural language description using AI."""
        if not hasattr(self, 'model'):
            self.log("AI not configured. Run 'pt ai config --api-key YOUR_API_KEY' first.", Colors.RED)
            return False

        project_info = self.get_project_info(project_ref)
        if not project_info:
            self.log(f"Project '{project_ref}' not found.", Colors.RED)
            return False

        project_context = self.get_project_context(project_info['id'])

        # AI prompt for task creation
        prompt = f"""Based on the following project context, analyze this task request and break it down into a structured task.

Project Context:
{project_context}

Task Request: {description}

Please respond with a JSON object containing:
- "title": A concise, clear task title
- "description": Detailed description of what needs to be done
- "priority": "high", "medium", or "low" based on the request
- "estimated_hours": Rough estimate of hours needed
- "complexity": "simple", "moderate", or "complex"
- "subtasks": Array of smaller subtasks if this is complex (optional)
- "dependencies": Any dependencies on existing tasks (reference task IDs if relevant)

Only respond with the JSON object, no other text."""

        try:
            response = self.model.generate_content(prompt)
            task_data = json.loads(response.text.strip())

            # Create the main task
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO tasks (project_id, title, description, priority, ai_generated, ai_estimate_hours, ai_complexity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_info['id'],
                task_data['title'],
                task_data['description'],
                task_data['priority'],
                True,
                task_data.get('estimated_hours'),
                task_data.get('complexity')
            ))

            task_id = cursor.lastrowid

            # Update project timestamp
            cursor.execute('UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (project_info['id'],))

            conn.commit()
            conn.close()

            # Display created task
            priority_color = {
                'high': Colors.RED,
                'medium': Colors.YELLOW,
                'low': Colors.CYAN
            }.get(task_data['priority'], Colors.NC)

            self.log(f"✓ Created AI task '{task_data['title']}' (ID: {task_id})", Colors.GREEN)
            self.log(f"  Priority: {priority_color}{task_data['priority'].upper()}{Colors.NC}")
            if task_data.get('estimated_hours'):
                self.log(f"  Estimated: {task_data['estimated_hours']} hours")
            if task_data.get('complexity'):
                self.log(f"  Complexity: {task_data['complexity']}")

            # Create subtasks if any
            if 'subtasks' in task_data and task_data['subtasks']:
                self.log(f"  Creating {len(task_data['subtasks'])} subtasks...", Colors.CYAN)
                for i, subtask in enumerate(task_data['subtasks'], 1):
                    cursor.execute('''
                        INSERT INTO tasks (project_id, title, description, priority, ai_generated)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        project_info['id'],
                        f"{task_data['title']} - {subtask}",
                        f"Subtask {i} of main task [{task_id}]: {subtask}",
                        'medium',
                        True
                    ))

                conn.commit()
                conn.close()

            return True

        except json.JSONDecodeError:
            self.log("✗ AI response was not valid JSON. Trying again...", Colors.RED)
            return False
        except Exception as e:
            self.log(f"✗ Error creating task: {e}", Colors.RED)
            return False

    def analyze_task(self, task_id: int):
        """Analyze a task and provide AI insights."""
        if not hasattr(self, 'model'):
            self.log("AI not configured.", Colors.RED)
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get task details
        cursor.execute('''
            SELECT t.*, p.name, p.path, p.description
            FROM tasks t
            JOIN projects p ON t.project_id = p.id
            WHERE t.id = ?
        ''', (task_id,))

        task = cursor.fetchone()
        if not task:
            self.log(f"Task {task_id} not found.", Colors.RED)
            return

        project_context = self.get_project_context(task[1])  # project_id

        # AI analysis prompt
        prompt = f"""Analyze this task within the project context and provide insights.

Project Context:
{project_context}

Task Details:
- ID: {task[0]}
- Title: {task[2]}
- Description: {task[3]}
- Status: {task[4]}
- Priority: {task[5]}

Please provide:
1. Implementation approach recommendations
2. Potential challenges or blockers
3. Required technologies/tools
4. Testing strategy
5. Time estimate refinement
6. Dependencies with other tasks

Keep the response practical and actionable."""

        try:
            response = self.model.generate_content(prompt)

            self.log(f"{Colors.BLUE}🧠 AI Analysis for Task [{task_id}]: {task[2]}{Colors.NC}")
            self.log("=" * 60)

            # Format and display the response
            formatted_response = textwrap.fill(response.text, width=80,
                                             initial_indent="", subsequent_indent="")
            print(formatted_response)

            # Store insight in database
            cursor.execute('''
                INSERT INTO ai_insights (project_id, task_id, insight_type, content)
                VALUES (?, ?, ?, ?)
            ''', (task[1], task_id, 'analysis', response.text))

            conn.commit()

        except Exception as e:
            self.log(f"Error analyzing task: {e}", Colors.RED)
        finally:
            conn.close()

    def configure(self, api_key: str = None):
        """Configure AI settings."""
        if api_key:
            self.config['api_key'] = api_key
            self.save_config()
            self.log("✓ API key saved securely.", Colors.GREEN)

            # Test the configuration
            if self.setup_genai():
                self.log("✓ Google AI connection successful!", Colors.GREEN)
                self.log(f"Using model: {self.config['model']}", Colors.CYAN)
            else:
                self.log("✗ Failed to connect to Google AI.", Colors.RED)
        else:
            self.log("Current AI Configuration:", Colors.BLUE)
            self.log(f"  Model: {self.config['model']}")
            self.log(f"  Max Tokens: {self.config['max_tokens']}")
            self.log(f"  Temperature: {self.config['temperature']}")
            self.log(f"  API Key: {'Set' if self.config.get('api_key') else 'Not set'}")

def main():
    ai = ProjectTrackerAI()

    parser = argparse.ArgumentParser(description='Project Tracker AI - Intelligent project management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Configuration
    config_cmd = subparsers.add_parser('config', help='Configure AI settings')
    config_cmd.add_argument('--api-key', help='Set Google AI API key')

    # Chat
    chat_cmd = subparsers.add_parser('chat', help='Chat with AI about a project')
    chat_cmd.add_argument('project', help='Project ID or name')
    chat_cmd.add_argument('message', help='Your message to the AI')

    # Task creation
    add_cmd = subparsers.add_parser('add', help='Create task from natural language')
    add_cmd.add_argument('project', help='Project ID or name')
    add_cmd.add_argument('description', help='Natural language task description')

    # Task analysis
    analyze_cmd = subparsers.add_parser('analyze', help='Analyze a task with AI')
    analyze_cmd.add_argument('task_id', type=int, help='Task ID to analyze')

    # Interactive chat
    interactive_cmd = subparsers.add_parser('interactive', help='Start interactive chat session')
    interactive_cmd.add_argument('project', help='Project ID or name')

    args = parser.parse_args()

    if args.command == 'config':
        ai.configure(args.api_key)
    elif args.command == 'chat':
        response = ai.chat(args.project, args.message)
        ai.log(f"{Colors.BLUE}🤖 AI Response:{Colors.NC}")
        print(textwrap.fill(response, width=80))
    elif args.command == 'add':
        ai.create_task_from_nl(args.project, args.description)
    elif args.command == 'analyze':
        ai.analyze_task(args.task_id)
    elif args.command == 'interactive':
        project_info = ai.get_project_info(args.project)
        if not project_info:
            ai.log(f"Project '{args.project}' not found.", Colors.RED)
            return

        ai.log(f"{Colors.PURPLE}🤖 Interactive AI Chat - Project: {project_info['name']}{Colors.NC}")
        ai.log("Type 'quit' or 'exit' to end the session.")
        ai.log("=" * 50)

        while True:
            try:
                user_input = input(f"\n{Colors.CYAN}You:{Colors.NC} ")
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    ai.log("👋 Goodbye!", Colors.GREEN)
                    break

                response = ai.chat(args.project, user_input)
                ai.log(f"{Colors.BLUE}🤖 AI:{Colors.NC}")
                print(textwrap.fill(response, width=80, initial_indent="", subsequent_indent=""))

            except KeyboardInterrupt:
                ai.log("\n👋 Goodbye!", Colors.GREEN)
                break
            except EOFError:
                break
    else:
        parser.print_help()

if __name__ == '__main__':
    main()