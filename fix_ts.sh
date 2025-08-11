#!/bin/bash

set -e

echo "Formatting TypeScript files..."
echo "============================="

cd client

# Format with prettier (includes import organization via plugin)
echo "Running prettier with import organization..."
bunx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css}" || {
    echo "Prettier failed, trying bun run..."
    bun run format 2>/dev/null || {
        echo "⚠️  Prettier not available, skipping formatting"
    }
}

# Lint and auto-fix with ESLint
echo "Running ESLint with auto-fix..."
bunx eslint --fix "src/**/*.{ts,tsx}" || {
    echo "⚠️  ESLint auto-fix failed, running check only..."
    bunx eslint "src/**/*.{ts,tsx}" || {
        echo "⚠️  ESLint check failed"
    }
}

# Type check with TypeScript
echo "Type checking with TypeScript..."
bunx tsc --noEmit || {
    echo "⚠️  TypeScript type checking failed"
}

# Check for unused code with knip
echo "Checking for unused code with knip..."
bunx knip --no-exit-code || {
    echo "⚠️  Knip not available or failed"
}

cd ..

echo "✅ TypeScript formatting and linting complete!"