#!/bin/bash

# ROM Browser GUI Startup Script
echo "Starting ROM Browser GUI..."

# Change to the backend directory
cd "$(dirname "$0")/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    cd ..
    ./setup.sh
    cd backend
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Check if required files exist
if [ ! -f "../../scripts/rom-browse.sh" ]; then
    echo "Error: CLI script not found at ../../scripts/rom-browse.sh"
    echo "Please ensure the scripts directory is in the correct location"
    exit 1
fi

if [ ! -f "../frontend/templates/index.html" ]; then
    echo "Error: Template files not found"
    echo "Please ensure the frontend directory structure is correct"
    exit 1
fi

echo "Starting Flask application..."
echo "Open http://localhost:5000 in your browser"
echo "Press Ctrl+C to stop"

# Start the Flask app
python app.py
