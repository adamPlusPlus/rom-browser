#!/bin/bash

# Myrient GUI Setup Script
echo "Setting up Myrient Game Browser GUI..."

# Create virtual environment for Python backend
cd backend
python -m venv venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install Python dependencies
pip install -r requirements.txt

echo "Backend setup complete!"
echo ""
echo "To get full functionality, you'll need API keys:"
echo "1. IGDB API: https://api.igdb.com/ (Free tier available)"
echo "2. RAWG API: https://rawg.io/apidocs (Free tier available)"
echo ""
echo "Set them as environment variables:"
echo "export IGDB_API_KEY='your_igdb_key'"
echo "export RAWG_API_KEY='your_rawg_key'"
echo ""
echo "To start the GUI:"
echo "cd backend && python app.py"
echo ""
echo "Then open http://localhost:5000 in your browser"
