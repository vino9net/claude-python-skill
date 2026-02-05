#!/bin/bash
# =============================================================================
# Claude Code Web Remote Environment Setup Script
# =============================================================================
#
# This script is intended for the remote environment of Claude Code Web.
# It runs automatically via SessionStart hook when starting a new session.
#
# What it does:
#   1. Checks if running in Claude Code Web remote environment
#   2. Installs uv (Python package manager) if not present
#   3. Runs 'uv sync' to install all project dependencies
#
# Configuration:
#   This script is triggered by .claude/settings.json SessionStart hook.
#
# Manual usage (for testing):
#   CLAUDE_CODE_REMOTE=true ./scripts/init_remote_env.sh
#
# =============================================================================

set -e

# Configuration (can be overridden via environment variables)
UV_VERSION="${UV_VERSION:-0.7.19}"

# Only run in remote Claude Code Web environment
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  echo "Not in Claude Code Web remote environment, skipping..."
  exit 0
fi

echo "=== Claude Code Web Remote Environment Setup ==="

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
  echo "Installing uv v${UV_VERSION}..."
  curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh

  # Add uv to PATH for this session
  export PATH="$HOME/.local/bin:$PATH"

  # Persist PATH for subsequent bash commands in this session
  if [ -n "$CLAUDE_ENV_FILE" ]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
  fi
fi

echo "uv version: $(uv --version)"

# Sync all dependencies from pyproject.toml / uv.lock
echo "Running uv sync with extras: edgar, indexing..."
uv sync
echo "=== Setup complete! ==="
exit 0

