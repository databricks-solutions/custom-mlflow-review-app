#!/bin/bash

set -e

echo "Formatting Python files..."
echo "========================="

# Format Python code with ruff
echo "Formatting Python files with ruff..."
uv run ruff format .
uv run ruff check --fix .

# Type check Python code with ty
echo "Type checking Python files with ty..."
uv run ty check

echo "✅ Python formatting complete!"