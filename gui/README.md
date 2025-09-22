# Myrient Game Browser GUI

A modern web-based frontend for the Myrient CLI browser with rich game metadata, cover art, and enhanced search capabilities.

## Features

### 🎮 **Game Browsing**
- Visual game grid with cover art
- Platform-based organization
- Real-time search and filtering
- Responsive design for all devices

### 📊 **Rich Metadata**
- **Cover Art**: High-quality game covers from IGDB
- **Metacritic Scores**: Professional game ratings
- **Game Descriptions**: Detailed game information
- **Screenshots**: In-game screenshots
- **Release Dates**: When games were released
- **Genres & Platforms**: Categorized game information

### 🔍 **Enhanced Search**
- Real-time search across all games
- Visual filters (genre, platform, rating)
- Smart game title cleaning
- Fuzzy matching for better results

### 🎨 **Modern UI**
- Clean, responsive design
- Smooth animations and transitions
- Dark/light theme support
- Mobile-friendly interface

## Quick Start

### 1. Setup
```bash
# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

### 2. Get API Keys (Optional but Recommended)
For full functionality, get free API keys:

- **IGDB API**: https://api.igdb.com/
  - Free tier: 500 requests/day
  - Best for console game metadata
  
- **RAWG API**: https://rawg.io/apidocs
  - Free tier: 20,000 requests/month
  - Good for PC games and additional metadata

### 3. Set Environment Variables
```bash
export IGDB_API_KEY="your_igdb_key_here"
export RAWG_API_KEY="your_rawg_key_here"
```

### 4. Start the Application
```bash
cd backend
python app.py
```

### 5. Open in Browser
Navigate to: http://localhost:5000

## How It Works

### Backend (Python Flask)
- **CLI Integration**: Interfaces with your existing `mbrowse.sh` script
- **Metadata APIs**: Fetches game data from IGDB and RAWG
- **REST API**: Provides endpoints for the frontend
- **Caching**: Stores metadata locally to reduce API calls

### Frontend (HTML/CSS/JavaScript)
- **Modern UI**: Clean, responsive interface
- **Real-time Updates**: Live search and filtering
- **Game Cards**: Visual representation of games
- **Modal Details**: Rich game information popup

### Data Flow
1. User selects a platform from the sidebar
2. Backend calls `mbrowse.sh` to get game list
3. Frontend displays games in a visual grid
4. Asynchronously fetches metadata for each game
5. Updates game cards with cover art, ratings, etc.

## API Endpoints

- `GET /api/platforms` - Get available platforms
- `GET /api/browse/<platform_id>` - Browse platform games
- `GET /api/game/<game_name>` - Get game metadata
- `POST /api/download/<game_name>` - Download game

## Configuration

### Backend Configuration
Edit `backend/app.py`:
```python
CLI_SCRIPT_PATH = "../myrient_batch_downloader/mbrowse.sh"
TEMP_DIR = "../myrient_batch_downloader/temp"
DATA_DIR = "../data"
```

### Frontend Configuration
Edit `frontend/static/js/app.js`:
```javascript
// Modify API endpoints, styling, or behavior
```

## Database Integration

The GUI integrates with several open databases:

### IGDB (Internet Game Database)
- **Cover Art**: High-resolution game covers
- **Screenshots**: In-game screenshots
- **Ratings**: User and critic ratings
- **Metadata**: Descriptions, genres, platforms

### RAWG (RAWG Video Games Database)
- **Metacritic Scores**: Professional critic scores
- **Additional Metadata**: Release dates, websites
- **Community Data**: User ratings and reviews

## Customization

### Adding New Metadata Sources
1. Add new API integration in `backend/app.py`
2. Update `GameMetadataService` class
3. Modify frontend to display new data

### Styling Changes
- Edit `frontend/static/css/style.css`
- Modify color scheme, layout, or animations
- Add new UI components

### CLI Integration
- Modify `CLI_SCRIPT_PATH` in backend
- Update command parsing logic
- Add new CLI features

## Troubleshooting

### Common Issues

**1. CLI Script Not Found**
```
Error: Failed to get platforms
```
- Ensure `mbrowse.sh` is executable
- Check `CLI_SCRIPT_PATH` in `app.py`
- Verify script permissions

**2. API Rate Limits**
```
Error: API rate limit exceeded
```
- Check your API key limits
- Implement caching (already included)
- Consider upgrading API plans

**3. No Game Metadata**
- Verify API keys are set correctly
- Check internet connection
- Some games may not be in databases

**4. Games Not Loading**
- Check browser console for errors
- Verify backend is running
- Check CLI script output

### Debug Mode
Enable debug mode in `backend/app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Feel free to modify and distribute.

## Credits

- **IGDB**: Game metadata and cover art
- **RAWG**: Additional game information
- **Font Awesome**: Icons
- **Flask**: Backend framework
- **Your CLI Script**: Core browsing functionality
