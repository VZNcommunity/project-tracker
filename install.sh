#!/bin/bash

# Project Tracker Installation Script

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log() {
    echo -e "$1"
}

log "${BLUE}🛠️  Installing Project Tracker (pt)${NC}"
log "======================================="

# Create directories
BIN_DIR="$HOME/.local/bin"
SHARE_DIR="$HOME/.local/share/project-tracker"

mkdir -p "$BIN_DIR"
mkdir -p "$SHARE_DIR"

# Copy executable scripts
scripts=(
    "project-tracker.py"
    "pt-git-hook.py"
    "pt-setup-git.py"
    "pt-enhance-claude.py"
    "pt-dev-session.py"
    "pt-ai.py"
    "pt-help"
)

log "${CYAN}📂 Installing scripts to $BIN_DIR...${NC}"

for script in "${scripts[@]}"; do
    if [[ -f "$script" ]]; then
        cp "$script" "$BIN_DIR/"
        chmod +x "$BIN_DIR/$script"
        log "   ✓ $script"
    else
        log "   ${YELLOW}⚠ $script not found${NC}"
    fi
done

# Copy template and documentation
docs=(
    "pt-claude-template.md"
    "pt-guide.md"
)

for doc in "${docs[@]}"; do
    if [[ -f "$doc" ]]; then
        cp "$doc" "$BIN_DIR/"
        log "   ✓ $doc"
    else
        log "   ${YELLOW}⚠ $doc not found${NC}"
    fi
done

# Create symlinks for easier access
log "${CYAN}🔗 Creating convenient symlinks...${NC}"
symlinks=(
    "project-tracker.py:pt"
    "pt-setup-git.py:pt-setup-git"
    "pt-enhance-claude.py:pt-enhance-claude"
    "pt-dev-session.py:pt-dev"
    "pt-ai.py:pt-ai"
)

for link in "${symlinks[@]}"; do
    source="${link%:*}"
    target="${link#*:}"

    if [[ -f "$BIN_DIR/$source" ]]; then
        ln -sf "$BIN_DIR/$source" "$BIN_DIR/$target"
        log "   ✓ $target -> $source"
    fi
done

# Setup Python virtual environment for AI features
log "${CYAN}🐍 Setting up Python virtual environment for AI features...${NC}"
if command -v python3 >/dev/null 2>&1; then
    if [[ ! -d "$HOME/.local/share/project-tracker/venv" ]]; then
        python3 -m venv "$HOME/.local/share/project-tracker/venv"
        log "   ✓ Virtual environment created"
    fi

    source "$HOME/.local/share/project-tracker/venv/bin/activate"
    pip install --quiet google-generativeai
    deactivate
    log "   ✓ Google Generative AI installed"
else
    log "   ${YELLOW}⚠ Python3 not found - AI features will be limited${NC}"
fi

# Initialize database
log "${CYAN}🗄️  Initializing database...${NC}"
if command -v python3 >/dev/null 2>&1; then
    python3 "$BIN_DIR/project-tracker.py" --help >/dev/null 2>&1 || true
    log "   ✓ Database initialized at $SHARE_DIR/tracker.db"
else
    log "   ${RED}✗ Python3 not found - database initialization skipped${NC}"
fi

# Check PATH
log "${CYAN}🔍 Checking PATH configuration...${NC}"
if echo "$PATH" | grep -q "$HOME/.local/bin"; then
    log "   ${GREEN}✓ ~/.local/bin is in your PATH${NC}"
else
    log "   ${YELLOW}⚠ ~/.local/bin is not in your PATH${NC}"
    log "   ${CYAN}Add this to your shell configuration (~/.bashrc, ~/.zshrc):${NC}"
    log "   export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

log ""
log "${GREEN}🎉 Installation Complete!${NC}"
log ""
log "Quick Start:"
log "  ${CYAN}pt-help${NC}                                    # Get help"
log "  ${CYAN}pt add-project \"my-project\" -p \"/path/to/project\"${NC} # Add project"
log "  ${CYAN}pt add \"my-project\" \"First task\" -p high${NC}        # Add task"
log "  ${CYAN}pt-setup-git \"my-project\"${NC}                       # Enable Git integration"
log "  ${CYAN}pt-dev start \"my-project\"${NC}                       # Start dev session"
log ""
log "AI Features (requires API key):"
log "  ${CYAN}pt-ai config --api-key YOUR_GOOGLE_AI_KEY${NC}        # Configure AI"
log "  ${CYAN}pt-ai add \"my-project\" \"create user auth system\"${NC}  # Natural language tasks"
log "  ${CYAN}pt-ai chat \"my-project\" \"how to implement OAuth?\"${NC} # Ask questions"
log "  ${CYAN}pt-ai analyze 123${NC}                            # AI analysis of task"
log ""
log "Documentation:"
log "  ${CYAN}pt-help guide${NC}                              # Full user guide"
log "  ${CYAN}pt-help commands${NC}                           # Command reference"
log "  ${CYAN}pt-help git${NC}                                # Git integration help"
log ""
log "${BLUE}Happy coding! 🚀${NC}"