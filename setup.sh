#!/bin/bash

set -e

echo "🚀 Databricks App Template Setup"
echo "================================="
echo "Starting Python-based setup script..."
echo ""

# Check for uv first - required to run the Python setup script
if ! command -v uv &> /dev/null; then
    echo "📦 uv (Python package manager) is required but not installed."
    echo "   uv is a fast Python package manager used for this setup script."
    echo "   Visit: https://docs.astral.sh/uv/"
    echo ""
    read -p "Would you like to install uv now? (y/N): " install_uv
    
    if [[ ! "$install_uv" =~ ^[Yy]$ ]]; then
        echo "❌ Setup requires uv to continue. Please install uv manually:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "   Then run this setup script again."
        exit 1
    fi
    
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Update PATH for this session
    if [ -f "$HOME/.local/bin/env" ]; then
        source $HOME/.local/bin/env
    elif [ -f "$HOME/.cargo/env" ]; then
        source ~/.cargo/env
    fi
    
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    
    if ! command -v uv &> /dev/null; then
        echo "❌ Failed to install uv. Please install manually:"
        echo "   Visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    
    echo "✅ uv installed successfully"
fi

# Install dependencies first
echo "📦 Installing Python dependencies..."
uv sync --dev

echo ""
echo "📦 Installing frontend dependencies..."
cd client
if command -v bun &> /dev/null; then
    bun install
else
    echo "⚠️  bun not found, using npm as fallback..."
    npm install
fi

echo ""
echo "🎭 Installing Playwright browser binaries..."
if npx playwright install; then
    echo "✅ Playwright browsers installed successfully"
else
    echo "⚠️  Failed to install Playwright browsers"
    echo "💡 You can install them later with: npx playwright install"
fi

cd ..

echo ""
echo "🤖 Checking Claude Code CLI..."
if command -v claude &> /dev/null; then
    echo "✅ Claude Code CLI found"
    echo "🎭 Checking Claude MCP Playwright integration..."
    
    # Check if playwright MCP server already exists
    if claude mcp list | grep -q "playwright"; then
        echo "✅ Claude MCP Playwright integration already installed"
    else
        echo "🔧 Adding Claude MCP Playwright integration..."
        if claude mcp add playwright npx '@playwright/mcp@latest'; then
            echo "✅ Claude MCP Playwright integration added"
            echo "💡 You may need to restart Claude Code to use Playwright integration"
        else
            echo "⚠️  Failed to add Claude MCP Playwright integration"
            echo "💡 You can add it manually with: claude mcp add playwright npx '@playwright/mcp@latest'"
        fi
    fi
else
    echo "⚠️  Claude Code CLI not found"
    echo "💡 Install Claude Code CLI to enable Playwright integration"
    echo "    Visit: https://claude.ai/code"
    echo "    After installing Claude Code, run:"
    echo "    claude mcp add playwright npx '@playwright/mcp@latest'"
fi


echo ""

# Run the Python setup script with all arguments passed through
echo "🐍 Running Python setup script..."
echo ""

uv run python setup.py "$@"

# Get the exit code from the Python script
PYTHON_EXIT_CODE=$?

# Exit with the same code as the Python script
exit $PYTHON_EXIT_CODE