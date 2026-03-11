#!/bin/bash
set -e

cd "$(dirname "$0")/bot"

echo "Running all tests..."
echo "========================"

uv run pytest tests/ -v

echo ""
echo "========================"
echo "Tests complete!"
