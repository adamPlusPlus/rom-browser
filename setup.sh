#!/bin/bash

# ROM Browser Setup Script
echo "Setting up ROM Browser..."

# Create necessary directories
mkdir -p downloads
mkdir -p temp
mkdir -p logs

# Make scripts executable
chmod +x scripts/*.sh
chmod +x gui/start_gui.sh
chmod +x gui/setup.sh

# Setup GUI if requested
if [ "$1" = "--gui" ] || [ "$1" = "-g" ]; then
    echo "Setting up GUI components..."
    cd gui
    ./setup.sh
    cd ..
fi

echo "ROM Browser setup complete!"
echo ""
echo "Usage:"
echo "  CLI: ./scripts/rom-browse.sh"
echo "  GUI: ./gui/start_gui.sh"
echo "  Download: ./scripts/rom-download.sh"
