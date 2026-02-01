#!/bin/bash
# Safety check for dependencies and correct environment
ABS_PATH=$(pwd)
export PYTHONPATH=$ABS_PATH

echo "Attempting to run AgriTech AI from virtual environment..."
./venv/bin/python3 -m streamlit run app.py
