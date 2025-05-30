#!/bin/bash
# Start YTDataHub Streamlit Application

# Navigate to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Start Streamlit with the correct main file
echo "Starting YTDataHub Streamlit Application..."
echo "Access the application at: http://localhost:8501"
python -m streamlit run youtube.py --server.port 8501 --server.headless false
