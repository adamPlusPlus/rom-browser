# Enhanced Game Collection System

A comprehensive game collection launcher with metadata, cover art, and advanced features.

## New Components

### Enhanced Launcher
- **`enhanced_game_launcher.py`** - Full-featured launcher with metadata viewer
- **`metadata_downloader.py`** - Downloads game metadata and cover art from IGDB
- **`igdb_config.json`** - Configuration for IGDB API access

## Features

### 🎮 Enhanced Game Launcher
- **Split-panel interface** - Games list on left, metadata viewer on right
- **Cover art display** - Shows game covers when available
- **Detailed metadata** - Rating, genres, summary, developer, publisher, etc.
- **Rating column** - Shows IGDB ratings in the games list
- **Metadata download** - One-click download for all games

### 📊 Metadata System
- **IGDB Integration** - Downloads from Internet Game Database
- **Local caching** - Stores metadata in SQLite database
- **Cover art storage** - Downloads and caches cover images
- **Smart search** - Cleans game names for better API results
- **Rate limiting** - Respects API limits

### 🖼️ Cover Art System
- **Automatic download** - Downloads covers when metadata is fetched
- **Local storage** - Stores in `covers/` directory
- **Image display** - Shows covers in metadata viewer
- **Fallback handling** - Graceful handling of missing covers

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure IGDB API
1. Go to https://api.igdb.com/
2. Create a Twitch account
3. Create a new app in Twitch Developer Console
4. Get your Client ID and Client Secret
5. Edit `igdb_config.json` with your credentials

### 3. Launch Enhanced Launcher
```bash
python enhanced_game_launcher.py
```

## Usage

### Basic Usage
1. **Launch the enhanced launcher**
2. **Select a game** from the list
3. **View metadata** in the right panel
4. **Download metadata** using the "Download Metadata" button
5. **Double-click** to launch games

### Metadata Features
- **IGDB Rating** - Professional game ratings
- **Genres** - Game categories and tags
- **Summary** - Game description
- **Developer/Publisher** - Company information
- **Release Date** - When the game was released
- **Platforms** - Supported systems
- **Metacritic Score** - Critical reception
- **Steam Integration** - Steam store links

### Cover Art Features
- **High-quality images** - Downloaded from IGDB
- **Automatic resizing** - Optimized for display
- **Cached storage** - Downloaded once, used forever
- **Fallback display** - Shows game name when no cover available

## File Structure

```
GameShortcuts/
├── enhanced_game_launcher.py    # Enhanced launcher with metadata
├── metadata_downloader.py       # IGDB metadata downloader
├── igdb_config.json            # API configuration
├── games.db                    # SQLite metadata database
├── covers/                     # Cover art storage
├── metadata/                    # Additional metadata files
└── favorites.json              # User favorites
```

## API Integration

### IGDB (Internet Game Database)
- **Professional ratings** and reviews
- **Comprehensive metadata** for thousands of games
- **High-quality cover art** and screenshots
- **Genre and platform** information
- **Developer and publisher** details

### Future Integrations
- **Steam API** - Steam store data and user reviews
- **Metacritic** - Critical scores and reviews
- **GOG** - GOG.com integration
- **Epic Games** - Epic Store integration

## Configuration

### IGDB Setup
Edit `igdb_config.json`:
```json
{
    "api_key": "your_client_id_here",
    "access_token": "your_access_token_here"
}
```

### Game Directories
Edit `game_directories.conf` to add your game folders.

## Troubleshooting

### Common Issues
1. **No metadata showing** - Check IGDB API configuration
2. **Cover art not loading** - Verify internet connection and API key
3. **Slow loading** - Metadata download is rate-limited for API courtesy

### API Limits
- **IGDB Free Tier** - 500 requests per month
- **Rate Limiting** - 0.5 second delay between requests
- **Caching** - Downloaded metadata is stored locally

## Advanced Features

### Database Management
- **SQLite database** stores all metadata locally
- **Automatic updates** when new metadata is downloaded
- **Duplicate prevention** - Won't re-download existing data

### Performance
- **Background downloads** - Non-blocking metadata fetching
- **Local caching** - Fast access to previously downloaded data
- **Smart updates** - Only downloads missing metadata

This enhanced system transforms your game collection into a professional game library with rich metadata and visual appeal!
