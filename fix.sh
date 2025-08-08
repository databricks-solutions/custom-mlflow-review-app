#!/bin/bash

set -e

echo "Formatting code..."
echo "=================="

# Run Python formatting
./fix_py.sh

# Run TypeScript formatting  
./fix_ts.sh

echo "✅ Code formatting complete!"