# ROM Browser

A modern web-based ROM browser with metadata, cover art, and batch downloading for retro games.

## 🎮 Features

### **Game Browsing**
- Visual game grid with cover art
- Platform-based organization
- Real-time search and filtering
- Responsive design for all devices

### **Rich Metadata**
- **Cover Art**: High-quality game covers from IGDB
- **Metacritic Scores**: Professional game ratings
- **Game Descriptions**: Detailed game information
- **Screenshots**: In-game screenshots
- **Release Dates**: When games were released
- **Genres & Platforms**: Categorized game information

### **Enhanced Search**
- Real-time search across all games
- Visual filters (genre, platform, rating)
- Smart game title cleaning
- Fuzzy matching for better results

### **Batch Downloading**
- Queue-based downloading system
- Support for 100+ platforms
- Resume interrupted downloads
- Progress tracking and logging

## 🚀 Quick Start

### **CLI Usage**
```bash
# Browse ROMs
./scripts/rom-browse.sh

# Download ROMs
./scripts/rom-download.sh

# Download specific platform
./scripts/rom-download.sh PS2
```

### **Web GUI**
```bash
# Start the web interface
cd gui
./start_gui.sh

# Open in browser
# Navigate to: http://localhost:5000
```

## 📁 Project Structure

```
rom-browser/
├── scripts/              # CLI tools
│   ├── rom-browse.sh     # Main browser script
│   ├── rom-download.sh   # Batch downloader
│   └── download-ps2.sh   # PS2-specific downloader
├── gui/                  # Web interface
│   ├── backend/          # Flask backend
│   └── frontend/         # Web frontend
├── config/               # Configuration files
│   └── rom-filter.txt    # Game filtering rules
└── docs/                 # Documentation
```

## 🔧 Configuration

### **Supported Platforms**
- Nintendo: NES, SNES, N64, GameCube, Wii, Wii U, Switch
- Sony: PS1, PS2, PS3, PS4, PS5, PSP, PS Vita
- Microsoft: Xbox, Xbox 360, Xbox One, Xbox Series X|S
- Sega: Master System, Genesis, Sega CD, 32X, Saturn, Dreamcast
- And 100+ more platforms

### **ROM Sources**
- **Myrient.erista.me**: Primary source (Redump & No-Intro)
- **Extensible**: Easy to add new sources

## 📊 Output Formats

- **JSON**: Structured data for APIs
- **CSV**: Tabular data for spreadsheets
- **HTML**: Interactive reports
- **Markdown**: Documentation format

## 🛠️ Development

### **Requirements**
- Python 3.8+
- Bash shell (MinGW/Git Bash on Windows)
- curl command
- 7-Zip (for extraction)

### **Setup**
```bash
# Install Python dependencies
cd gui
pip install -r backend/requirements.txt

# Make scripts executable
chmod +x scripts/*.sh
```

## 📚 Documentation

- [CLI Usage Guide](docs/CLI.md)
- [Web GUI Guide](docs/GUI.md)
- [Configuration Reference](docs/CONFIG.md)
- [Contributing Guide](docs/CONTRIBUTING.md)

## 🎯 Use Cases

- **Retro Gaming**: Browse and download classic games
- **Game Preservation**: Access historical game collections
- **Research**: Study game metadata and trends
- **Collection Management**: Organize personal game libraries

## 📄 License

This project is open source. Feel free to modify and distribute.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🔗 Related Projects

- [PS3 Tools](../ps3-tools/) - PS3 ISO preparation utilities
- [StreamDeck Tools](../streamdeck-tools/) - StreamDeck integrations
- [Game Rating](../gamerat/) - Game rating and library management
