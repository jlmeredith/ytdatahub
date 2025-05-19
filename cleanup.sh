#!/bin/zsh
echo "==== YTDataHub Cleanup Script ===="
echo "Cleaning up Python cache and build files..."

# Set globstar option for recursive matching
setopt extended_glob 2>/dev/null

echo "Removing Python cache directories..."
# Remove __pycache__ directories (with safeguards)
find . -name "__pycache__" -type d -exec rm -rf {} \; 2>/dev/null || echo "No __pycache__ directories found or unable to remove some"

echo "Removing compiled Python files..."
# Remove .pyc files
find . -name "*.pyc" -delete 2>/dev/null
# Remove .pyo files
find . -name "*.pyo" -delete 2>/dev/null
# Remove .pyd files
find . -name "*.pyd" -delete 2>/dev/null

echo "Removing build directories and artifacts..."
# Remove build directories
rm -rf build dist .eggs 2>/dev/null
# Remove pytest cache
rm -rf .pytest_cache 2>/dev/null
# Remove coverage reports
rm -rf .coverage htmlcov coverage.xml 2>/dev/null
# Remove egg-info directories
rm -rf *.egg-info 2>/dev/null || echo "No egg-info directories found at root level"
find . -name "*.egg-info" -type d -exec rm -rf {} \; 2>/dev/null

echo "Removing temporary files..."
# Remove .DS_Store files (macOS)
find . -name ".DS_Store" -delete 2>/dev/null
# Remove swap files
find . -name "*.swp" -delete 2>/dev/null
# Remove temp files
find . -name "*~" -delete 2>/dev/null

echo "✅ Cleanup complete!"
echo "If you need to preserve specific cache files in the future,"
echo "please modify this script to exclude those directories."
