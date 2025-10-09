# ROM Browser GUI

A modern, native desktop application built with Tauri, React, and TypeScript for browsing and managing ROM collections.

## Features

- **Native Performance**: Built with Tauri for fast, native desktop performance
- **Modern UI**: Clean, responsive interface with smooth animations
- **3D Ready**: Integrated with Three.js for future 3D visualizations
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Python Integration**: Seamlessly integrates with existing Python scripts

## Technology Stack

- **Frontend**: React 18 + TypeScript
- **Backend**: Rust (Tauri)
- **3D Graphics**: Three.js + React Three Fiber
- **UI Components**: Lucide React icons
- **Build Tool**: Vite

## Development Setup

### Prerequisites

- **Node.js 18+**: https://nodejs.org/en/download/
- **Rust**: https://rustup.rs/
- **Git**: For version control

### Installation

1. **Install Dependencies**:
   ```bash
   cd gui
   npm install
   ```

2. **Install Tauri CLI**:
   ```bash
   cargo install tauri-cli
   ```

3. **Start Development Server**:
   ```bash
   npm run tauri:dev
   ```

### Building for Production

```bash
npm run tauri:build
```

## Project Structure

```
gui/
├── src/
│   ├── components/          # React components
│   │   ├── Header.tsx
│   │   ├── PlatformSidebar.tsx
│   │   └── GameBrowser.tsx
│   ├── App.tsx             # Main app component
│   ├── App.css            # App styles
│   ├── main.tsx           # App entry point
│   └── index.css          # Global styles
├── src-tauri/
│   ├── src/
│   │   └── main.rs        # Rust backend
│   ├── Cargo.toml         # Rust dependencies
│   └── tauri.conf.json    # Tauri configuration
├── package.json           # Node.js dependencies
├── vite.config.ts         # Vite configuration
└── tsconfig.json          # TypeScript configuration
```

## Tauri Commands

The Rust backend provides these commands to the frontend:

- `get_platforms()`: Get list of available platforms
- `browse_platform(platform_id)`: Browse games for a platform
- `download_game(game_name, url)`: Download a specific game
- `get_game_metadata(game_name)`: Get metadata for a game

## Integration with Python Scripts

The GUI integrates with your existing Python scripts:

- **ROM Browsing**: `scripts/rom-sourcing/rom_browser.py`
- **ROM Downloading**: `scripts/rom-sourcing/rom_downloader.py`
- **Metadata**: `scripts/game-management/smart_metadata_downloader.py`
- **Game Management**: `scripts/game-management/game_name_resolver.py`

## Future Enhancements

- **3D Game Visualization**: Interactive 3D game collections
- **Advanced Filtering**: Genre, rating, release date filters
- **Batch Operations**: Multi-game downloads and management
- **Favorites System**: Save and organize favorite games
- **Cover Art Integration**: High-quality game covers
- **Progress Tracking**: Download progress and queue management

## Development Notes

- **Hot Reload**: Changes to frontend code automatically refresh
- **DevTools**: Full browser devtools available in development mode
- **TypeScript**: Full type safety for better development experience
- **Responsive**: Works on different screen sizes and orientations

## Troubleshooting

### Common Issues

1. **Node.js not found**: Install Node.js from https://nodejs.org/
2. **Rust not found**: Install Rust from https://rustup.rs/
3. **Build errors**: Run `cargo clean` and try again
4. **Permission errors**: Ensure scripts are executable

### Debug Mode

Enable debug mode in `src-tauri/tauri.conf.json`:
```json
{
  "tauri": {
    "allowlist": {
      "all": true
    }
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Feel free to modify and distribute.
