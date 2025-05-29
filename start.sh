#!/bin/bash

# Ensure we're in the project directory
cd "$(dirname "$0")"

# Activate the virtual environment
source ./venv/bin/activate

# Run the application
streamlit run youtube.py 