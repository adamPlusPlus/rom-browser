# Game Shortcuts Collection

A comprehensive suite of tools for managing game shortcuts and creating a unified game launcher.

## Components

### Scripts
- **`create_game_shortcuts.py`** - Multi-directory game shortcut creator
- **`create_shortcuts_config.py`** - Configuration-based shortcut creator (recommended)
- **`create_shortcuts_single.py`** - Single directory shortcut creator
- **`create_rom_shortcuts.py`** - ROM/emulator shortcut creator
- **`game_launcher.py`** - Basic GUI game launcher
- **`modern_game_launcher.py`** - Enhanced GUI game launcher (recommended)

### Configuration Files
- **`game_directories.conf`** - Game directory mappings
- **`rom_directories.conf`** - ROM directory and emulator mappings

### Documentation
- **`ROM_README.md`** - ROM shortcut creator documentation

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure game directories:**
   Edit `game_directories.conf` to add your game directories

3. **Create game shortcuts:**
   ```bash
   python create_shortcuts_config.py
   ```

4. **Configure ROM directories (optional):**
   Edit `rom_directories.conf` to add ROM directories and emulators

5. **Create ROM shortcuts (optional):**
   ```bash
   python create_rom_shortcuts.py
   ```

6. **Launch the game launcher:**
   ```bash
   python modern_game_launcher.py
   ```

## Features

### Game Shortcut Creator
- Scans multiple directories for executables
- Filters out non-game executables (uninstallers, crash handlers, etc.)
- Handles DOSBox games and other special cases
- Creates shortcuts with descriptive names

### ROM Shortcut Creator
- Maps ROM directories to emulators
- Supports all major console emulators
- Creates shortcuts that launch ROMs directly
- Handles various ROM formats

### Game Launcher GUI
- Modern, dark-themed interface
- Search and filter games
- Favorites system
- Game type categorization
- Double-click to launch games
- Statistics and last played tracking

## Directory Structure

```
GameShortcuts/
├── create_game_shortcuts.py      # Multi-directory scanner
├── create_shortcuts_config.py    # Config-based scanner (main)
├── create_shortcuts_single.py    # Single directory scanner
├── create_rom_shortcuts.py       # ROM/emulator scanner
├── game_launcher.py              # Basic GUI launcher
├── modern_game_launcher.py       # Enhanced GUI launcher
├── game_directories.conf         # Game directory config
├── rom_directories.conf          # ROM directory config
├── requirements.txt              # Python dependencies
└── ROM_README.md                 # ROM documentation
```

## Output Directories

- **Games**: `E:\Desktop\Games`
- **ROMs**: `E:\Desktop\ROMs`

## Usage Examples

### Create all game shortcuts:
```bash
python create_shortcuts_config.py --dry-run  # Preview
python create_shortcuts_config.py           # Create
```

### Create ROM shortcuts:
```bash
python create_rom_shortcuts.py --dry-run    # Preview
python create_rom_shortcuts.py              # Create
```

### Launch game collection:
```bash
python modern_game_launcher.py
```

## Customization

### Adding New Game Directories
Edit `game_directories.conf`:
```
# Add your directories
D:\MyGames = 
E:\SteamLibrary\steamapps\common = 
```

### Adding ROM Directories
Edit `rom_directories.conf`:
```
# Format: ROM_DIRECTORY = EMULATOR_PATH
D:\ROMs\PS2 = F:\Program Files\PCSX2\pcsx2.exe
D:\ROMs\N64 = F:\Program Files\Project64\Project64.exe
```

### Changing Output Directories
Edit the `OUTPUT_DIR` setting in the config files:
```
OUTPUT_DIR = C:\MyShortcuts
```

## Troubleshooting

### Common Issues
1. **Shortcuts not created**: Check that directories exist and are accessible
2. **Games not showing in launcher**: Ensure shortcuts are in the correct output directory
3. **ROMs not launching**: Verify emulator paths are correct in `rom_directories.conf`

### Dependencies
- Python 3.6+
- Windows (for pywin32)
- pywin32 (for Windows shortcuts)
- Pillow (for GUI icons)

## License

This project is provided as-is for personal use.
