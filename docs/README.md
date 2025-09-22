# Myrient Universal ROM Batch Downloader

This directory contains scripts to automatically download ROMs from your Myrient remote archive based on platform selection and download queue.

## Files

- **`universal_rom_downloader.sh`** - Universal ROM downloader supporting multiple platforms (recommended)
- **`ps2_downloader.sh`** - Legacy PS2-only downloader script
- **`download_queue`** - Your list of games to download (in same directory)

## Prerequisites

- MinGW/bash shell (which you already have)
- `curl` command available
- Internet connection

## Usage

### Universal ROM Downloader (Recommended)

The universal downloader supports multiple platforms and now provides dataset selection and interactive filtering:

```bash
cd myrient_batch_downloader

# Interactive mode (choose dataset, mode, then platform)
./universal_rom_downloader.sh

# Start on a specific platform (name, code, or number all work)
./universal_rom_downloader.sh PS2
./universal_rom_downloader.sh "Xbox 360"
./universal_rom_downloader.sh 9

# Get help
./universal_rom_downloader.sh --help
```

### Legacy PS2 Downloader

```bash
cd myrient_batch_downloader
./ps2_downloader.sh
```

## Supported Platforms

The universal downloader supports **100+ platforms** including:

### Nintendo Systems
- NES, SNES, N64, GameCube, Wii, Wii U, Switch

### Sony Systems  
- PS1, PS2, PS3, PS4, PS5, PSP, PS Vita

### Microsoft Systems
- Xbox, Xbox 360, Xbox One, Xbox Series X|S

### Sega Systems
- Master System, Mega Drive/Genesis, Sega CD, 32X, Saturn, Dreamcast

### Retro Systems
- Atari 2600/5200/7800/Jaguar/Lynx
- NEC PC Engine/TurboGrafx-16, PC-FX
- SNK Neo Geo, Neo Geo Pocket
- Bandai WonderSwan
- Commodore Amiga, C64
- Apple II, Macintosh

### PC & Modern Platforms
- Windows, Linux, macOS, Android, iOS
- Web, VR, AR, Cloud, Mobile platforms
- Various game genres and categories

## How It Works

1. **Dataset Selection**: Choose between Redump and No-Intro
2. **Mode Selection**: Continue the queue or single-game download
3. **Platform Selection**: Dynamically fetched from the dataset root and filtered as you type (case-insensitive). CLI hints (name/code/number) still apply as initial filters.
4. **Queue Mode**: Reads your `download_queue` file and processes each game in order
5. **Single-Game Mode**: Enter a rough title for auto-match, or browse/search titles interactively
6. **Smart Search & Best Match**: Flexible matching and scoring with region/language preference
7. **Sequential Downloads**: Downloads one game at a time with progress bars
8. **Queue Management**: Automatically removes successfully downloaded games from the queue
9. **Comprehensive Logging**: Logs all operations for debugging

## Features

- **Multi-Platform Support**: Download from any supported Myrient archive
- **Dataset Toggle**: Redump and No-Intro root listings
- **Interactive Selection**: Fuzzy filtering for platforms and titles (type to narrow, number to pick)
- **Flexible Input**: Accept platform names, abbreviations, short codes (e.g., `PS2`, `X360`), or numbers
- **Archive Types**: Supports `.zip` and `.7z`
- **Single-Game Mode**: Enter a rough title or browse/search; prefers USA region when available
- **Smart Matching**: Multiple search patterns for better game discovery
- **Sequential Downloads**: Respectful to server with configurable delays
- **Resume Support**: Can resume interrupted downloads
- **Progress Tracking**: Shows download progress and overall completion status
- **Detailed Logging**: Comprehensive logs in `download_log.txt`
- **Queue Management**: Automatic cleanup of completed downloads
- **Error Handling**: Continues with next game if one fails

## Command Line Options

```bash
./universal_rom_downloader.sh [platform] [subtype]

Examples:
  ./universal_rom_downloader.sh                    # Interactive (choose queue or single game)
  ./universal_rom_downloader.sh PS2               # Start on PS2 (you'll still pick mode)
  ./universal_rom_downloader.sh "Xbox 360"         # Start on Xbox 360
  ./universal_rom_downloader.sh 9                 # Start on platform number 9
  ./universal_rom_downloader.sh --help            # Show help
```

## Configuration

Edit the script to modify:

- `MYRIENT_BASE_URL`: Base URL for Myrient archives
- `DOWNLOAD_DIR`: Where to save downloaded files
- `QUEUE_FILE`: Path to your download queue file
- `PLATFORMS`: Add/remove supported platforms
- Wait times between downloads (currently 3 seconds)

## Output

- **Downloads**: Saved to `./downloads/` directory
- **Logs**: Detailed logs in `download_log.txt`
- **Queue Updates**: Modified `download_queue` file with completed games removed

## Troubleshooting

### Common Issues

1. **Archive Not Accessible**: Check internet connection and Myrient URL
2. **Games Not Found**: Some games may have different names in archives
3. **Download Failures**: Check log file for specific error messages
4. **Permission Errors**: Ensure scripts are executable (`chmod +x script.sh`)

### Manual Search

If a game isn't found automatically, manually search the Myrient archive at:
https://myrient.erista.me/files/Redump/

## Notes

- Scripts are respectful to Myrient servers with delays between downloads
- Failed downloads are not removed from the queue
- Automatic URL encoding/decoding for special characters
- All operations are logged for debugging
- Optimized for MinGW/bash environment

## Example Output

```
Available Platforms:
Enter platform name or number:

 1. Nintendo - Nintendo Entertainment System
 2. Nintendo - Super Nintendo Entertainment System
 3. Nintendo - Nintendo 64
 4. Nintendo - Nintendo GameCube
 5. Nintendo - Nintendo Wii
 6. Nintendo - Nintendo Wii U
 7. Nintendo - Nintendo Switch
 8. Sony - PlayStation
 9. Sony - PlayStation 2
10. Sony - PlayStation 3
...

Enter platform: 9
Selected platform: Sony - PlayStation 2
Archive index downloaded successfully
Found 67 games to process
[1/67] Processing: OutRun 2006: Coast to Coast
Searching for: OutRun 2006: Coast to Coast
Found 1 potential matches for: OutRun 2006: Coast to Coast
Downloading: OutRun 2006: Coast to Coast
✓ Completed: OutRun 2006: Coast to Coast
Removed 'OutRun 2006: Coast to Coast' from download queue
Waiting 3 seconds before next download...
```
