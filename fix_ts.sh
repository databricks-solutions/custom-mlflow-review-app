#!/bin/bash

set -e

echo "Formatting TypeScript files..."
echo "============================="

cd client

# Format with prettier (includes import organization via plugin)
echo "Running prettier with import organization..."
npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css}" || {
    echo "Prettier failed, trying npm script..."
    npm run format 2>/dev/null || {
        echo "⚠️  Prettier not available, skipping formatting"
    }
}

# Lint and auto-fix with ESLint
echo "Running ESLint with auto-fix..."
npx eslint --fix "src/**/*.{ts,tsx}" || {
    echo "ESLint auto-fix failed, trying npm script..."
    npm run lint --fix 2>/dev/null || {
        echo "⚠️  ESLint auto-fix failed, running check only..."
        npx eslint "src/**/*.{ts,tsx}" || npm run lint 2>/dev/null || {
            echo "⚠️  ESLint check failed"
        }
    }
}

# Type check with TypeScript
echo "Type checking with TypeScript..."
npx tsc --noEmit || {
    echo "⚠️  TypeScript type checking failed"
}

# Check for unused code with knip
echo "Checking for unused code with knip..."
npx knip --no-exit-code || {
    echo "⚠️  Knip not available or failed"
}

cd ..

echo "✅ TypeScript formatting and linting complete!"