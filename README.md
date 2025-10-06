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

**Bash Scripts (Shell Integration):**
```bash
# Browse ROMs
./scripts/rom-sourcing/rom-browse.sh

# Download ROMs
./scripts/rom-sourcing/rom-download.sh

# Download specific platform
./scripts/rom-sourcing/rom-download.sh PS2

# Generic file browser
./scripts/rom-sourcing/rom-files.sh
```

**Python Scripts (Enhanced Features):**
```bash
# Browse ROMs with advanced features
python scripts/rom-sourcing/rom_browser.py --dataset redump

# Download ROMs with progress tracking
python scripts/rom-sourcing/rom_downloader.py --platform "PlayStation 2" --max-files 10

# Generic file browser with filtering
python scripts/rom-sourcing/rom_files.py --url "https://myrient.erista.me/files/Redump/"

# Create game shortcuts
python scripts/game-management/create_shortcuts_config.py

# Create ROM shortcuts
python scripts/game-management/create_rom_shortcuts.py

# Download metadata
python scripts/game-management/smart_metadata_downloader.py
```

### **Native GUI (Tauri + React)**
```bash
# Install dependencies
cd gui
npm install

# Start development server
npm run tauri:dev

# Build for production
npm run tauri:build
```

## 📁 Project Structure

```
rom-browser/
├── scripts/              # CLI tools
│   ├── rom-sourcing/     # ROM browsing and downloading
│   │   ├── rom-browse.sh     # Main browser script (bash)
│   │   ├── rom-download.sh   # Batch downloader (bash)
│   │   ├── rom-files.sh      # Generic file browser (bash)
│   │   ├── rom_browser.py    # Main browser script (python)
│   │   ├── rom_downloader.py # Batch downloader (python)
│   │   └── rom_files.py      # Generic file browser (python)
│   ├── game-management/  # Game collection management
│   │   ├── create_shortcuts_config.py    # Config-based shortcut creator
│   │   ├── create_rom_shortcuts.py       # ROM-to-emulator shortcuts
│   │   ├── game_name_resolver.py         # Enhanced name mapping
│   │   ├── metadata_downloader.py        # IGDB/Screenscraper integration
│   │   ├── smart_metadata_downloader.py  # Batch metadata processing
│   │   ├── custom_ratings_manager.py     # User ratings management
│   │   ├── config_manager.py             # App configuration
│   │   └── games.db                      # Metadata database
│   └── shortcuts/        # Legacy shortcut scripts
├── gui/                  # Native desktop application
│   ├── src/              # React frontend
│   │   ├── components/   # UI components
│   │   ├── App.tsx       # Main app
│   │   └── main.tsx      # Entry point
│   ├── src-tauri/        # Rust backend
│   │   ├── src/main.rs   # Tauri commands
│   │   └── Cargo.toml    # Rust dependencies
│   └── package.json      # Node.js dependencies
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
- Node.js 18+ (for GUI)
- Rust (for GUI)
- Bash shell (MinGW/Git Bash on Windows)
- curl command
- 7-Zip (for extraction)

### **Setup**
```bash
# Install GUI dependencies
cd gui
npm install

# Install Tauri CLI
cargo install tauri-cli

# Make scripts executable
chmod +x scripts/*.sh
```

## 📚 Documentation

- This section consolidates documentation from the GUI and Game Shortcuts projects.

### Web GUI (from gui/README.md)

#### Features
- Game browsing with cover art; platform-based organization; real-time search and filtering; responsive UI
- Rich metadata: IGDB covers, Metacritic, descriptions, screenshots, release dates, genres, platforms
- Modern UI: animations, dark/light theme, mobile-friendly

#### Quick Start
```bash
# Setup
chmod +x gui/setup.sh
./gui/setup.sh

# Start backend
cd gui/backend
python app.py

# Open
# http://localhost:5000
```

#### API Endpoints
- GET /api/platforms
- GET /api/browse/<platform_id>
- GET /api/game/<game_name>
- POST /api/download/<game_name>

#### Configuration
- Backend: edit `gui/backend/app.py`
- Frontend: edit `gui/frontend/static/js/app.js`

### Game Management Suite (from scripts/game-management/)

#### Components
- Scripts: `create_shortcuts_config.py`, `create_rom_shortcuts.py`, `game_name_resolver.py`, `metadata_downloader.py`, `smart_metadata_downloader.py`, `custom_ratings_manager.py`, `config_manager.py`
- Database: `games.db` - SQLite metadata storage

#### Quick Start
```bash
# Create game shortcuts
python scripts/game-management/create_shortcuts_config.py

# Create ROM shortcuts  
python scripts/game-management/create_rom_shortcuts.py

# Download metadata for all games
python scripts/game-management/smart_metadata_downloader.py

# Enhanced name resolution with directory scanning
python scripts/game-management/game_name_resolver.py
```

#### Features
- **Game Shortcut Creator**: scans directories, filters non-games, handles DOSBox, creates named shortcuts
- **ROM Shortcut Creator**: maps ROM dirs to emulators, supports major emulators and formats
- **Enhanced Name Resolver**: directory scanning, external mappings, database integration
- **Metadata Downloader**: IGDB/Screenscraper integration with cover art and ratings
- **Smart Batch Processing**: API rate limiting, incomplete metadata tracking
- **Custom Ratings Manager**: user-defined ratings and tags
- **Configuration Manager**: app settings and themes

### ROM Shortcuts (summary)

Use the ROM shortcuts creator to generate launcher shortcuts for console ROMs via your preferred emulators.

Quick start
```bash
# Configure ROM directories and emulator paths (create if missing)
# Expected format (one per line):
#   <ROM_DIRECTORY> = <EMULATOR_EXE_PATH>
# Example:
#   D:\ROMs\PS2 = F:\Program Files\PCSX2\pcsx2.exe
#   D:\ROMs\N64 = F:\Program Files\Project64\Project64.exe

python scripts/game-management/create_rom_shortcuts.py --dry-run  # preview
python scripts/game-management/create_rom_shortcuts.py            # create
```

Notes
- Place ROM directory/emulator mappings in a `rom_directories.conf` file alongside the script or in the working directory.
- Generated shortcuts follow the same naming and filtering rules as game shortcuts.
- Supports common ROM formats; emulator command-lines can be adjusted in the script if needed.

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
