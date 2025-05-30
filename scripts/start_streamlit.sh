#!/bin/bash
cd /Users/jamiemeredith/Projects/ytdatahub
source venv/bin/activate
python -m streamlit run youtube.py --server.port 8501
