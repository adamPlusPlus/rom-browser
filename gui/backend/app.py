#!/usr/bin/env python3
"""
ROM Browser GUI Backend
Web API for the ROM browser with game metadata integration
"""

import os
import json
import subprocess
import requests
import re
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import logging

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
CORS(app)

# Configuration
CLI_SCRIPT_PATH = "../../scripts/rom-browse.sh"
TEMP_DIR = "../temp"
DATA_DIR = "../data"

# API Keys (you'll need to get these from the respective services)
IGDB_API_KEY = os.getenv('IGDB_API_KEY', '')
RAWG_API_KEY = os.getenv('RAWG_API_KEY', '')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameMetadataService:
    """Service for fetching game metadata from various APIs"""
    
    def __init__(self):
        self.igdb_base_url = "https://api.igdb.com/v4"
        self.rawg_base_url = "https://api.rawg.io/api"
        
    def clean_game_title(self, title):
        """Clean game title for better API matching"""
        # Remove common suffixes and clean up
        title = re.sub(r'\s*\([^)]*\)\s*$', '', title)  # Remove trailing (World), (USA), etc.
        title = re.sub(r'\s*\[[^\]]*\]\s*$', '', title)  # Remove trailing [Rev 1], etc.
        title = re.sub(r'\s*\.zip$', '', title)  # Remove .zip extension
        title = re.sub(r'\s*\([^)]*DLC[^)]*\)', '', title)  # Remove DLC indicators
        title = re.sub(r'\s*\([^)]*Addon[^)]*\)', '', title)  # Remove Addon indicators
        return title.strip()
    
    def search_igdb(self, game_title):
        """Search IGDB for game information"""
        if not IGDB_API_KEY:
            return None
            
        try:
            headers = {
                'Client-ID': IGDB_API_KEY.split(':')[0] if ':' in IGDB_API_KEY else IGDB_API_KEY,
                'Authorization': f'Bearer {IGDB_API_KEY.split(":")[1] if ":" in IGDB_API_KEY else IGDB_API_KEY}'
            }
            
            # Search for games
            search_query = f'search "{game_title}"; fields name,summary,rating,rating_count,cover.url,screenshots.url,platforms.name,genres.name,release_dates.human; where platforms.name = "Xbox 360" | "Xbox" | "PlayStation 3" | "PlayStation 2" | "Nintendo Wii" | "Nintendo DS" | "Nintendo 3DS" | "PlayStation Portable" | "PC (Microsoft Windows)"; limit 5;'
            
            response = requests.post(f"{self.igdb_base_url}/games", 
                                  data=search_query, 
                                  headers=headers, 
                                  timeout=10)
            
            if response.status_code == 200:
                games = response.json()
                if games:
                    game = games[0]  # Take the first match
                    return {
                        'name': game.get('name', ''),
                        'summary': game.get('summary', ''),
                        'rating': game.get('rating', 0),
                        'rating_count': game.get('rating_count', 0),
                        'cover_url': f"https:{game['cover']['url']}" if game.get('cover') else None,
                        'screenshots': [f"https:{s['url']}" for s in game.get('screenshots', [])[:3]],
                        'platforms': [p['name'] for p in game.get('platforms', [])],
                        'genres': [g['name'] for g in game.get('genres', [])],
                        'release_date': game.get('release_dates', [{}])[0].get('human', '') if game.get('release_dates') else ''
                    }
        except Exception as e:
            logger.error(f"IGDB search error: {e}")
        
        return None
    
    def search_rawg(self, game_title):
        """Search RAWG for game information"""
        if not RAWG_API_KEY:
            return None
            
        try:
            params = {
                'key': RAWG_API_KEY,
                'search': game_title,
                'page_size': 5
            }
            
            response = requests.get(f"{self.rawg_base_url}/games", 
                                 params=params, 
                                 timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    game = data['results'][0]  # Take the first match
                    return {
                        'name': game.get('name', ''),
                        'description': game.get('description_raw', ''),
                        'metacritic': game.get('metacritic', 0),
                        'rating': game.get('rating', 0),
                        'rating_count': game.get('ratings_count', 0),
                        'background_image': game.get('background_image', ''),
                        'screenshots': [s['image'] for s in game.get('short_screenshots', [])[:3]],
                        'platforms': [p['platform']['name'] for p in game.get('platforms', [])],
                        'genres': [g['name'] for g in game.get('genres', [])],
                        'released': game.get('released', ''),
                        'website': game.get('website', ''),
                        'reddit_url': game.get('reddit_url', '')
                    }
        except Exception as e:
            logger.error(f"RAWG search error: {e}")
        
        return None
    
    def get_game_metadata(self, game_title):
        """Get comprehensive game metadata from multiple sources"""
        cleaned_title = self.clean_game_title(game_title)
        
        # Try IGDB first (better for console games)
        igdb_data = self.search_igdb(cleaned_title)
        if igdb_data:
            return {
                'source': 'IGDB',
                'title': igdb_data['name'],
                'description': igdb_data['summary'],
                'rating': igdb_data['rating'],
                'rating_count': igdb_data['rating_count'],
                'cover_art': igdb_data['cover_url'],
                'screenshots': igdb_data['screenshots'],
                'platforms': igdb_data['platforms'],
                'genres': igdb_data['genres'],
                'release_date': igdb_data['release_date']
            }
        
        # Fallback to RAWG
        rawg_data = self.search_rawg(cleaned_title)
        if rawg_data:
            return {
                'source': 'RAWG',
                'title': rawg_data['name'],
                'description': rawg_data['description'],
                'metacritic_score': rawg_data['metacritic'],
                'rating': rawg_data['rating'],
                'rating_count': rawg_data['rating_count'],
                'cover_art': rawg_data['background_image'],
                'screenshots': rawg_data['screenshots'],
                'platforms': rawg_data['platforms'],
                'genres': rawg_data['genres'],
                'release_date': rawg_data['released'],
                'website': rawg_data.get('website'),
                'reddit_url': rawg_data.get('reddit_url')
            }
        
        return None

# Initialize metadata service
metadata_service = GameMetadataService()

@app.route('/')
def index():
    """Serve the main GUI page"""
    return render_template('index.html')

@app.route('/api/platforms', methods=['GET'])
def get_platforms():
    """Get list of available platforms"""
    try:
        # Run the CLI script to get platforms
        result = subprocess.run([CLI_SCRIPT_PATH], 
                              input="xbox\nq\n", 
                              text=True, 
                              capture_output=True, 
                              timeout=30)
        
        if result.returncode == 0:
            # Parse the output to extract platform information
            lines = result.stdout.split('\n')
            platforms = []
            
            for line in lines:
                if '[' in line and ']' in line and 'Microsoft' in line:
                    # Extract platform name
                    platform_match = re.search(r'\[([^\]]+)\]\s*(.+)', line)
                    if platform_match:
                        dataset = platform_match.group(1)
                        platform_name = platform_match.group(2).strip()
                        platforms.append({
                            'dataset': dataset,
                            'name': platform_name,
                            'id': len(platforms) + 1
                        })
            
            return jsonify({'platforms': platforms})
        else:
            return jsonify({'error': 'Failed to get platforms'}), 500
            
    except Exception as e:
        logger.error(f"Error getting platforms: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/browse/<int:platform_id>', methods=['GET'])
def browse_platform(platform_id):
    """Browse a specific platform"""
    try:
        # Get platform info first
        platforms_result = get_platforms()
        if platforms_result[1] != 200:  # Check if error
            return platforms_result
            
        platforms = platforms_result[0].get_json()['platforms']
        if platform_id > len(platforms):
            return jsonify({'error': 'Invalid platform ID'}), 400
            
        platform = platforms[platform_id - 1]
        
        # Run CLI script to browse the platform
        input_commands = f"xbox\n{platform_id}\nq\n"
        result = subprocess.run([CLI_SCRIPT_PATH], 
                              input=input_commands, 
                              text=True, 
                              capture_output=True, 
                              timeout=30)
        
        if result.returncode == 0:
            # Parse the output to extract file information
            lines = result.stdout.split('\n')
            files = []
            
            for line in lines:
                if re.match(r'^\s*\d+\.\s+.+\.zip$', line):
                    # Extract file info
                    file_match = re.match(r'^\s*(\d+)\.\s+(.+)$', line)
                    if file_match:
                        file_id = int(file_match.group(1))
                        file_name = file_match.group(2)
                        files.append({
                            'id': file_id,
                            'name': file_name,
                            'is_directory': file_name.endswith('/'),
                            'is_file': file_name.endswith('.zip')
                        })
            
            return jsonify({
                'platform': platform,
                'files': files,
                'total_files': len(files)
            })
        else:
            return jsonify({'error': 'Failed to browse platform'}), 500
            
    except Exception as e:
        logger.error(f"Error browsing platform: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/<path:game_name>', methods=['GET'])
def get_game_metadata(game_name):
    """Get metadata for a specific game"""
    try:
        metadata = metadata_service.get_game_metadata(game_name)
        if metadata:
            return jsonify(metadata)
        else:
            return jsonify({'error': 'No metadata found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting game metadata: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<path:game_name>', methods=['POST'])
def download_game(game_name):
    """Download a specific game"""
    try:
        # This would integrate with your existing download functionality
        # For now, just return success
        return jsonify({'message': f'Download started for {game_name}'})
        
    except Exception as e:
        logger.error(f"Error downloading game: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print("Starting Myrient GUI Backend...")
    print("Make sure to set IGDB_API_KEY and RAWG_API_KEY environment variables for full functionality")
    print("IGDB API: https://api.igdb.com/")
    print("RAWG API: https://rawg.io/apidocs")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
