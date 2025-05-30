#!/bin/bash

# YTDataHub - Main Application Startup Script
# This script starts the Streamlit application with proper environment setup

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting YTDataHub Application...${NC}"

# Ensure we're in the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo -e "${YELLOW}Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if Streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo -e "${RED}❌ Streamlit not found in virtual environment!${NC}"
    echo -e "${YELLOW}Installing requirements...${NC}"
    pip install -r requirements.txt
fi

# Create data directory if it doesn't exist
mkdir -p data

# Start the application
echo -e "${GREEN}✅ Starting Streamlit application on http://localhost:8501${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the application${NC}"
echo ""

python -m streamlit run youtube.py --server.port 8501