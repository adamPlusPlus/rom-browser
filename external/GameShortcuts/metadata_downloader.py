#!/usr/bin/env python3
"""
Game Metadata Downloader
Downloads game metadata and cover art from IGDB (Internet Game Database).
"""

import os
import sys
import json
import requests
import sqlite3
from pathlib import Path
import time
from datetime import datetime
import hashlib


class GameMetadataDownloader:
    def __init__(self, api_key=None):
        # Screenscraper.fr - free and unlimited for registered users
        self.username, self.password = self.get_screenscraper_credentials()
        self.base_url = "https://www.screenscraper.fr/api2"
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'GameLauncher/1.0'
        }
        
        # Local storage paths
        self.metadata_dir = Path("metadata")
        self.covers_dir = Path("covers")
        self.db_path = Path("games.db")
        
        # Create directories
        self.metadata_dir.mkdir(exist_ok=True)
        self.covers_dir.mkdir(exist_ok=True)
        
        # Initialize database
        self.init_database()
        
    def get_screenscraper_credentials(self):
        """Get Screenscraper.fr credentials from environment or config file."""
        # Try environment variables first
        username = os.getenv('SCREENSCRAPER_USERNAME')
        password = os.getenv('SCREENSCRAPER_PASSWORD')
        
        if username and password:
            return username, password
            
        # Try config file
        config_file = Path("screenscraper_config.json")
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('username'), config.get('password')
        
        # Return None if no credentials found
        return None, None
        
    def get_access_token(self):
        """Get IGDB access token (simplified - in production, implement proper OAuth flow)."""
        # Try config file first
        config_file = Path("igdb_config.json")
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('access_token', 'your_access_token_here')
        
        # Try environment variable
        return os.getenv('IGDB_ACCESS_TOKEN', 'your_access_token_here')
        
    def init_database(self):
        """Initialize SQLite database for game metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                igdb_id INTEGER,
                cover_url TEXT,
                cover_path TEXT,
                rating REAL,
                rating_count INTEGER,
                summary TEXT,
                genres TEXT,
                platforms TEXT,
                release_date TEXT,
                developer TEXT,
                publisher TEXT,
                steam_id INTEGER,
                metacritic_score INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def search_game(self, game_name):
        """Search for a game using multiple sources."""
        # Try Steam API first (completely free, no limits)
        steam_result = self.search_steam(game_name)
        if steam_result and steam_result.get('summary') and not steam_result['summary'].startswith('Game: '):
            return steam_result
        
        # Try GOG Database (unofficial but working)
        gog_result = self.search_gog_database(game_name)
        if gog_result and gog_result.get('summary') and not gog_result['summary'].startswith('Game: '):
            return gog_result
        
        # Try Metacritic (web scraping approach)
        metacritic_result = self.search_metacritic(game_name)
        if metacritic_result and metacritic_result.get('summary') and not metacritic_result['summary'].startswith('Game: '):
            return metacritic_result
        
        # Try RAWG API (10,000 requests/month free)
        rawg_result = self.search_rawg(game_name)
        if rawg_result and rawg_result.get('summary') and not rawg_result['summary'].startswith('Game: '):
            return rawg_result
        
        # Try Screenscraper.fr (free with registration)
        screenscraper_result = self.search_screenscraper(game_name)
        if screenscraper_result and screenscraper_result.get('summary') and not screenscraper_result['summary'].startswith('Game: '):
            return screenscraper_result
        
        # Try Google Images as final fallback
        google_result = self.search_google_images(game_name)
        if google_result and google_result.get('summary') and not google_result['summary'].startswith('Game: '):
            return google_result
        
        # If all fail, try Google search to find the correct game name
        correct_name = self.search_google_for_game_name(game_name)
        if correct_name and correct_name != game_name:
            print(f"Found correct name '{correct_name}' for deformed name '{game_name}'")
            # Try searching again with the correct name
            result = self.search_game(correct_name)
            if result:
                # Rename the .lnk file to the correct name
                self.rename_game_file(game_name, correct_name)
            return result
        
        # If all fail, create basic metadata
        return self.create_basic_metadata(game_name)
    
    def search_steam(self, game_name):
        """Search for a game using Steam API (free and unlimited)."""
        # Clean game name for better search results
        clean_name = self.clean_game_name_for_search(game_name)
        
        try:
            # Steam Store API search (completely free, no API key needed)
            params = {
                'term': clean_name,
                'category1': '998',  # Games
                'cc': 'us',
                'l': 'english'
            }
            
            response = requests.get(
                "https://store.steampowered.com/api/storesearch",
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('items') and len(data['items']) > 0:
                    # Get detailed info for the first result
                    steam_id = data['items'][0].get('id')
                    if steam_id:
                        return self.get_steam_game_details(steam_id, data['items'][0])
            
            return None
                
        except Exception as e:
            print(f"Error searching Steam for {game_name}: {e}")
            return None
    
    def get_steam_game_details(self, steam_id, basic_data):
        """Get detailed game information from Steam Store API."""
        try:
            # Get detailed game info
            params = {
                'appids': steam_id,
                'cc': 'us',
                'l': 'english'
            }
            
            response = requests.get(
                f"https://store.steampowered.com/api/appdetails",
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if str(steam_id) in data and data[str(steam_id)]['success']:
                    game_data = data[str(steam_id)]['data']
                    return self.convert_steam_to_metadata(game_data, basic_data)
            
            # Fallback to basic data if detailed request fails
            return self.convert_steam_to_metadata(basic_data)
                
        except Exception as e:
            print(f"Error getting Steam details for {steam_id}: {e}")
            return self.convert_steam_to_metadata(basic_data)
    
    def search_metacritic(self, game_name):
        """Search Metacritic for game ratings and metadata."""
        # Metacritic web scraping is unreliable due to anti-bot protection
        # For now, return None to skip Metacritic and rely on other sources
        return None
        
    def assign_basic_rating(self, game_name, genres):
        """Assign a basic rating based on game name and genres."""
        # Simple heuristic rating system
        rating = 7.0  # Base rating
        
        # Adjust based on popular game names
        popular_games = {
            'witcher': 9.5, 'skyrim': 9.5, 'fallout': 9.0, 'elder scrolls': 9.0,
            'dark souls': 9.0, 'bloodborne': 9.5, 'sekiro': 9.0,
            'zelda': 9.5, 'mario': 9.0, 'pokemon': 8.5,
            'halo': 8.5, 'gears': 8.0, 'mass effect': 9.0,
            'dragon age': 8.5, 'bioshock': 9.0, 'portal': 9.5,
            'half-life': 9.5, 'counter-strike': 8.5, 'dota': 8.5,
            'league of legends': 8.0, 'world of warcraft': 8.5,
            'minecraft': 8.5, 'terraria': 8.5, 'stardew valley': 8.5,
            'civilization': 8.5, 'total war': 8.0, 'xcom': 8.5,
            'doom': 8.5, 'quake': 8.0, 'wolfenstein': 8.0,
            'tomb raider': 8.0, 'uncharted': 8.5, 'god of war': 9.0,
            'spider-man': 8.5, 'batman': 8.5, 'assassin': 8.0,
            'call of duty': 7.5, 'battlefield': 7.5, 'fifa': 7.0,
            'nba': 7.0, 'madden': 7.0, 'nhl': 7.0
        }
        
        game_lower = game_name.lower()
        for keyword, score in popular_games.items():
            if keyword in game_lower:
                rating = score
                break
        
        # Adjust based on genres
        if genres:
            genre_lower = [g.lower() for g in genres]
            if 'rpg' in genre_lower:
                rating += 0.5
            if 'strategy' in genre_lower:
                rating += 0.3
            if 'indie' in genre_lower:
                rating += 0.2
            if 'action' in genre_lower:
                rating += 0.1
        
        # Cap rating between 5.0 and 10.0
        return max(5.0, min(10.0, rating))
        
    def is_game_match(self, search_name, result_name):
        """Check if a search result matches our game name."""
        # Simple fuzzy matching
        search_words = set(search_name.lower().split())
        result_words = set(result_name.lower().split())
        
        # Check if most words match
        common_words = search_words.intersection(result_words)
        return len(common_words) >= len(search_words) * 0.6
    
    def search_rawg(self, game_name):
        """Search for a game using RAWG API (10,000 requests/month free)."""
        # RAWG API requires a free API key - using a demo key for testing
        rawg_api_key = "c542e67aec3a4340908f9de9e86038af"  # Demo key from RAWG.io
        
        if rawg_api_key == "your_rawg_api_key_here":
            return None  # Skip if no API key provided
            
        clean_name = self.clean_game_name_for_search(game_name)
        
        try:
            params = {
                'key': rawg_api_key,
                'search': clean_name,
                'page_size': 1
            }
            
            response = requests.get(
                "https://api.rawg.io/api/games",
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    # Get detailed info for the first result
                    game_id = data['results'][0].get('id')
                    if game_id:
                        return self.get_rawg_game_details(game_id, data['results'][0])
                    else:
                        return self.convert_rawg_to_metadata(data['results'][0])
            
            return None
                
        except Exception as e:
            print(f"Error searching RAWG for {game_name}: {e}")
            return None
    
    def get_rawg_game_details(self, game_id, basic_data):
        """Get detailed game information from RAWG API."""
        try:
            params = {
                'key': "c542e67aec3a4340908f9de9e86038af"
            }
            
            response = requests.get(
                f"https://api.rawg.io/api/games/{game_id}",
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                detailed_data = response.json()
                return self.convert_rawg_to_metadata(detailed_data)
            
            # Fallback to basic data if detailed request fails
            return self.convert_rawg_to_metadata(basic_data)
                
        except Exception as e:
            print(f"Error getting RAWG details for {game_id}: {e}")
            return self.convert_rawg_to_metadata(basic_data)
    
    def search_google_images(self, game_name):
        """Search for game cover art using Google Images (fallback method)."""
        try:
            clean_name = self.clean_game_name_for_search(game_name)
            search_query = f"{clean_name} game cover art box art"
            
            # Use a simple web scraping approach for Google Images
            # Note: This is a basic implementation and may need adjustments
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # For now, return a basic result with a placeholder
            # In a production environment, you'd implement proper Google Images API or web scraping
            return {
                'id': None,
                'name': game_name,
                'cover': {'url': None},
                'rating': None,
                'rating_count': None,
                'summary': f"Game: {game_name}\n\nCover art not found in primary sources. Consider adding manually.",
                'genres': [],
                'platforms': ['PC'],
                'first_release_date': None,
                'developers': [],
                'publishers': [],
                'external_games': [],
                'screenshots': [],
                'high_res_cover': None
            }
                
        except Exception as e:
            print(f"Error searching Google Images for {game_name}: {e}")
            return None
    
    def search_google_for_game_name(self, deformed_name):
        """Search Google to find the correct game name from a deformed filename."""
        try:
            import requests
            from bs4 import BeautifulSoup
            import re
            
            # Search for the deformed name + "game" to find the real game
            search_query = f'"{deformed_name}" game'
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Use a simple search approach
            search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for game titles in search results
                # Common patterns for game titles
                game_patterns = [
                    r'([A-Z][a-zA-Z\s&:,\'-]+(?:Game|Edition|Remastered|Definitive|Special|Gold|Platinum|Ultimate|Complete|Collection|Bundle))',
                    r'([A-Z][a-zA-Z\s&:,\'-]+(?:II|III|IV|V|VI|VII|VIII|IX|X|\d+))',
                    r'([A-Z][a-zA-Z\s&:,\'-]+(?:of|the|and|in|on|at|for|with|from|to|by)\s+[A-Z][a-zA-Z\s&:,\'-]+)',
                ]
                
                # Look in search result titles and snippets
                for element in soup.find_all(['h3', 'span', 'div'], string=True):
                    text = element.get_text().strip()
                    
                    for pattern in game_patterns:
                        matches = re.findall(pattern, text)
                        for match in matches:
                            if isinstance(match, tuple):
                                match = match[0]
                            
                            # Clean up the match
                            clean_match = match.strip()
                            if len(clean_match) > 5 and len(clean_match) < 100:
                                # Check if it looks like a game title
                                if any(word in clean_match.lower() for word in ['game', 'edition', 'remastered', 'definitive', 'special', 'gold', 'platinum', 'ultimate', 'complete', 'collection', 'bundle']):
                                    return clean_match
                                # Or if it's significantly different from the deformed name
                                if clean_match.lower() != deformed_name.lower() and len(clean_match) > len(deformed_name) * 1.5:
                                    return clean_match
                
                return None
                
        except Exception as e:
            print(f"Error searching Google for {deformed_name}: {e}")
            return None
    
    def rename_game_file(self, old_name, new_name):
        """Rename a game's .lnk file to the correct name."""
        try:
            import os
            from pathlib import Path
            
            # This method would need access to the game directory
            # For now, just log the rename operation
            print(f"Would rename '{old_name}.lnk' to '{new_name}.lnk'")
            
            # In a full implementation, you'd:
            # 1. Find the .lnk file in the game directories
            # 2. Rename it to the correct name
            # 3. Update any database references
            
            return True
            
        except Exception as e:
            print(f"Error renaming game file from '{old_name}' to '{new_name}': {e}")
            return False
    
    def search_gog_database(self, game_name):
        """Search for a game using GOG's search API (unofficial but working)."""
        clean_name = self.clean_game_name_for_search(game_name)
        
        try:
            # Use GOG's search API (unofficial but functional)
            search_url = "https://www.gog.com/games/ajax/filtered"
            
            params = {
                'search': clean_name,
                'limit': 5,
                'page': 1,
                'sort': 'relevance'
            }
            
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'GameLauncher/1.0',
                'Referer': 'https://www.gog.com/'
            }
            
            response = requests.get(search_url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('products') and len(data['products']) > 0:
                    # Get the first result
                    product = data['products'][0]
                    return self.convert_gog_to_metadata(product)
            
            return None
                
        except Exception as e:
            print(f"Error searching GOG for {game_name}: {e}")
            return None
    
    def search_screenscraper(self, game_name):
        """Search for a game in Screenscraper.fr."""
        if not self.username or not self.password:
            return None
            
        # Clean game name for better search results
        clean_name = self.clean_game_name_for_search(game_name)
        
        try:
            # First, search for the game by name using jeuRecherche.php
            search_params = {
                'devid': self.username,
                'devpassword': self.password, 
                'softname': 'testlaunchapp',
                'output': 'json',
                'systemeid': '1',  # PC games
                'recherche': clean_name
            }
            
            search_response = requests.get(
                f"{self.base_url}/jeuRecherche.php",
                headers=self.headers,
                params=search_params,
                timeout=15
            )
            
            if search_response.status_code == 200:
                try:
                    search_data = search_response.json()
                    if search_data.get('response') and search_data['response'].get('jeux'):
                        # Get the first result
                        jeu = search_data['response']['jeux'][0]
                        jeu_id = jeu.get('id')
                        
                        if jeu_id:
                            # Now get detailed info using jeuInfos.php
                            info_params = {
                                'devid': self.username,
                                'devpassword': self.password,
                                'softname': 'testlaunchapp',
                                'output': 'json',
                                'id': jeu_id
                            }
                            
                            info_response = requests.get(
                                f"{self.base_url}/jeuInfos.php",
                                headers=self.headers,
                                params=info_params,
                                timeout=15
                            )
                            
                            if info_response.status_code == 200:
                                try:
                                    info_data = info_response.json()
                                    if info_data.get('response') and info_data['response'].get('jeu'):
                                        return self.convert_screenscraper_to_metadata(info_data['response']['jeu'])
                                except:
                                    print(f"Screenscraper info returned non-JSON response: {info_response.text[:100]}")
                                    return None
                except:
                    print(f"Screenscraper search returned non-JSON response: {search_response.text[:100]}")
                    return None
            
            return None
                
        except Exception as e:
            print(f"Error searching Screenscraper for {game_name}: {e}")
            return None
            
    def convert_rawg_to_metadata(self, rawg_data):
        """Convert RAWG API response to our metadata format."""
        return {
            'id': rawg_data.get('id'),
            'name': rawg_data.get('name', ''),
            'cover': {'url': rawg_data.get('background_image')},
            'rating': rawg_data.get('rating'),
            'rating_count': rawg_data.get('ratings_count'),
            'summary': rawg_data.get('description_raw', ''),
            'genres': [genre.get('name') for genre in rawg_data.get('genres', [])],
            'platforms': [platform.get('platform', {}).get('name') for platform in rawg_data.get('platforms', [])],
            'first_release_date': rawg_data.get('released'),
            'developers': [dev.get('name') for dev in rawg_data.get('developers', [])],
            'publishers': [pub.get('name') for pub in rawg_data.get('publishers', [])],
            'external_games': [],
            'screenshots': [screenshot.get('image') for screenshot in rawg_data.get('short_screenshots', [])]
        }
    
    def convert_gog_to_metadata(self, gog_data):
        """Convert GOG API response to our metadata format."""
        # Extract cover image URL
        cover_url = None
        if gog_data.get('image'):
            cover_url = gog_data['image']
        elif gog_data.get('gallery') and len(gog_data['gallery']) > 0:
            cover_url = gog_data['gallery'][0]
        
        # Extract genres
        genres = []
        if gog_data.get('genres'):
            genres = [genre.get('name', '') for genre in gog_data['genres']]
        
        # Extract developers and publishers
        developers = []
        publishers = []
        if gog_data.get('developers'):
            developers = [dev.get('name', '') for dev in gog_data['developers']]
        if gog_data.get('publishers'):
            publishers = [pub.get('name', '') for pub in gog_data['publishers']]
        
        # Extract release date
        release_date = None
        if gog_data.get('releaseDate'):
            release_date = gog_data['releaseDate']
        
        return {
            'id': gog_data.get('id'),
            'name': gog_data.get('title', ''),
            'cover': {'url': cover_url},
            'rating': gog_data.get('rating'),  # GOG rating if available
            'rating_count': None,  # GOG doesn't provide rating counts
            'summary': gog_data.get('description', ''),
            'genres': genres,
            'platforms': ['PC'],  # GOG is PC-focused
            'first_release_date': release_date,
            'developers': developers,
            'publishers': publishers,
            'external_games': [],
            'screenshots': gog_data.get('gallery', [])
        }
            
    def convert_steam_to_metadata(self, steam_data, basic_data=None):
        """Convert Steam API response to our metadata format."""
        # Handle both detailed data and basic search data
        if isinstance(steam_data, dict) and 'short_description' in steam_data:
            # Steam API doesn't provide review data, so we'll rely on Metacritic for ratings
            rating = None
            rating_count = None
            
            # Assign a basic rating based on game popularity/genre
            # This is a simple heuristic until we get real rating data
            rating = self.assign_basic_rating(steam_data.get('name', ''), steam_data.get('genres', []))
            rating_count = None
            
            # Detailed data from appdetails API
            return {
                'id': steam_data.get('steam_appid'),
                'name': steam_data.get('name', ''),
                'cover': {'url': steam_data.get('header_image')},
                'rating': rating,
                'rating_count': rating_count,
                'summary': steam_data.get('short_description', ''),
                'genres': [genre.get('description', '') for genre in steam_data.get('genres', [])],
                'platforms': ['PC'],
                'first_release_date': steam_data.get('release_date', {}).get('date'),
                'developers': steam_data.get('developers', []),
                'publishers': steam_data.get('publishers', []),
                'external_games': [],
                'screenshots': [],
                'high_res_cover': steam_data.get('header_image')  # High resolution cover
            }
        else:
            # Basic data from search API
            return {
                'id': steam_data.get('id'),
                'name': steam_data.get('name', ''),
                'cover': {'url': steam_data.get('tiny_image')},
                'rating': None,
                'rating_count': None,
                'summary': f"Steam game: {steam_data.get('name', '')}",
                'genres': [],
                'platforms': ['PC'],
                'first_release_date': None,
                'developers': [],
                'publishers': [],
                'external_games': [],
                'screenshots': []
            }
            
    def convert_screenscraper_to_metadata(self, screenscraper_data):
        """Convert Screenscraper.fr API response to our metadata format."""
        # Extract cover URL from media section
        cover_url = None
        if 'medias' in screenscraper_data:
            for media in screenscraper_data['medias']:
                if media.get('type') == 'ss' and media.get('region') == 'us':  # Screenshot/cover
                    cover_url = media.get('url')
                    break
        
        return {
            'id': screenscraper_data.get('id'),
            'name': screenscraper_data.get('nom', ''),
            'cover': {'url': cover_url},
            'rating': None,  # Screenscraper doesn't provide ratings
            'rating_count': None,
            'summary': screenscraper_data.get('synopsis', ''),
            'genres': [screenscraper_data.get('genre')] if screenscraper_data.get('genre') else [],
            'platforms': ['PC'],
            'first_release_date': screenscraper_data.get('dates', {}).get('us', ''),
            'developers': [screenscraper_data.get('developpeur')] if screenscraper_data.get('developpeur') else [],
            'publishers': [screenscraper_data.get('editeur')] if screenscraper_data.get('editeur') else [],
            'external_games': [],
            'screenshots': screenscraper_data.get('medias', [])
        }
            
    def create_basic_metadata(self, game_name):
        """Create basic metadata without API calls."""
        # Generate a simple cover art placeholder
        cover_path = self.create_placeholder_cover(game_name)
        
        return {
            'id': None,
            'name': game_name,
            'cover': {'url': None},
            'cover_path': cover_path,  # Add the placeholder path
            'rating': None,
            'rating_count': None,
            'summary': f"Game: {game_name}\n\nNo detailed information available. Install IGDB API credentials to get full metadata.",
            'genres': [],
            'platforms': ['PC'],
            'first_release_date': None,
            'developers': [],
            'publishers': [],
            'external_games': []
        }
        
    def create_placeholder_cover(self, game_name):
        """Create a placeholder cover art."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple placeholder image
            img = Image.new('RGB', (200, 250), color='#2d2d2d')
            draw = ImageDraw.Draw(img)
            
            # Try to use a font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Draw game name
            text = game_name[:20] + "..." if len(game_name) > 20 else game_name
            
            # Use older method for text positioning
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except AttributeError:
                # Fallback for older Pillow versions
                text_width = len(text) * 10  # Rough estimate
                text_height = 20
            
            x = (200 - text_width) // 2
            y = (250 - text_height) // 2
            
            draw.text((x, y), text, fill='white', font=font)
            
            # Save placeholder
            safe_name = self.safe_filename(game_name)
            placeholder_path = self.covers_dir / f"{safe_name}_placeholder.jpg"
            img.save(placeholder_path)
            
            return str(placeholder_path)
            
        except Exception as e:
            print(f"Error creating placeholder cover: {e}")
            return None
            
    def clean_game_name_for_search(self, name):
        """Clean game name for better search results."""
        # Remove common suffixes and clean up
        suffixes_to_remove = [
            ' (ModEngine)', ' (Protected)', ' (MCC Launcher)', ' (Startup)', ' (Pre-Launcher)',
            ' (Mod - Armoredcore6)', ' (Mod - Darksouls3)', ' (Mod - Eldenring)',
            ' (PS2)', ' (PSX)', ' (N64)', ' (GameCube)', ' (Wii)', ' (Dreamcast)',
            ' (Genesis)', ' (SNES)', ' (NES)', ' (GBA)', ' (NDS)', ' (PSP)',
            ' (MAME)', ' (C64)', ' (Amiga)', ' (Atari2600)',
            'Launch ', ' - ', ':', ';', '!', '?'
        ]
        
        clean_name = name
        for suffix in suffixes_to_remove:
            clean_name = clean_name.replace(suffix, ' ')
            
        # Remove extra spaces and trim
        clean_name = ' '.join(clean_name.split())
        
        return clean_name
        
    def download_cover_art(self, cover_url, game_name):
        """Download cover art for a game."""
        if not cover_url:
            return None
            
        # Create filename from game name
        safe_name = self.safe_filename(game_name)
        cover_path = self.covers_dir / f"{safe_name}.jpg"
        
        # Skip if already downloaded
        if cover_path.exists():
            return str(cover_path)
            
        try:
            # Handle different URL formats
            if cover_url.startswith('//'):
                cover_url = 'https:' + cover_url
            elif cover_url.startswith('/'):
                cover_url = 'https://www.screenscraper.fr' + cover_url
            elif not cover_url.startswith('http'):
                cover_url = 'https://www.screenscraper.fr' + cover_url
                
            response = requests.get(cover_url, timeout=30)
            response.raise_for_status()
            
            with open(cover_path, 'wb') as f:
                f.write(response.content)
                
            return str(cover_path)
            
        except Exception as e:
            print(f"Error downloading cover for {game_name}: {e}")
            return None
            
    def safe_filename(self, filename):
        """Create a safe filename from game name."""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
            
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
            
        return filename
        
    def get_steam_metadata(self, game_name):
        """Get Steam metadata (simplified - would need Steam API)."""
        # This is a placeholder. In production, you'd use Steam Web API
        return {
            'steam_id': None,
            'steam_genres': [],
            'steam_tags': []
        }
        
    def get_metacritic_score(self, game_name):
        """Get Metacritic score (simplified - would need web scraping)."""
        # This is a placeholder. In production, you'd scrape Metacritic
        return None
        
    def store_game_metadata(self, game_name, igdb_data, cover_path):
        """Store game metadata in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract data from IGDB response
        genres = []
        platforms = []
        developers = []
        publishers = []
        
        if igdb_data and isinstance(igdb_data, dict):
            try:
                # Handle genres - they might be strings or dicts
                genres = []
                for g in igdb_data.get('genres', []):
                    if isinstance(g, dict):
                        genres.append(g.get('name', ''))
                    else:
                        genres.append(str(g))
                
                # Handle platforms - they might be strings or dicts
                platforms = []
                for p in igdb_data.get('platforms', []):
                    if isinstance(p, dict):
                        platforms.append(p.get('name', ''))
                    else:
                        platforms.append(str(p))
                
                # Handle developers - they might be strings or dicts
                developers = []
                for d in igdb_data.get('developers', []):
                    if isinstance(d, dict):
                        developers.append(d.get('name', ''))
                    else:
                        developers.append(str(d))
                
                # Handle publishers - they might be strings or dicts
                publishers = []
                for p in igdb_data.get('publishers', []):
                    if isinstance(p, dict):
                        publishers.append(p.get('name', ''))
                    else:
                        publishers.append(str(p))
            except Exception as e:
                print(f"Error extracting data from igdb_data: {e}")
                genres = []
                platforms = []
                developers = []
                publishers = []
            
        # Get Steam and Metacritic data
        steam_data = self.get_steam_metadata(game_name)
        metacritic_score = self.get_metacritic_score(game_name)
        
        cursor.execute('''
            INSERT OR REPLACE INTO games 
            (name, igdb_id, cover_url, cover_path, rating, rating_count, summary,
             genres, platforms, release_date, developer, publisher, steam_id,
             metacritic_score, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            game_name,
            igdb_data.get('id') if igdb_data and isinstance(igdb_data, dict) else None,
            igdb_data.get('cover', {}).get('url') if igdb_data and isinstance(igdb_data, dict) else None,
            cover_path,
            igdb_data.get('rating') if igdb_data and isinstance(igdb_data, dict) else None,
            igdb_data.get('rating_count') if igdb_data and isinstance(igdb_data, dict) else None,
            igdb_data.get('summary') if igdb_data and isinstance(igdb_data, dict) else None,
            json.dumps(genres),
            json.dumps(platforms),
            igdb_data.get('first_release_date') if igdb_data and isinstance(igdb_data, dict) else None,
            json.dumps(developers),
            json.dumps(publishers),
            steam_data.get('steam_id'),
            metacritic_score,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
    def get_game_metadata(self, game_name):
        """Get metadata for a game (from cache or download)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we already have this game
        cursor.execute('SELECT * FROM games WHERE name = ?', (game_name,))
        row = cursor.fetchone()
        
        if row:
            conn.close()
            return self.row_to_dict(row)
            
        conn.close()
        
        # Download new metadata using resolved game name
        try:
            from game_name_resolver import GameNameResolver
            resolver = GameNameResolver()
            resolved_name = resolver.resolve_game_name(game_name)
            print(f"Resolved '{game_name}' to '{resolved_name}' for GameBrain search")
        except ImportError:
            resolved_name = game_name
            
        igdb_data = self.search_game(resolved_name)
        
        cover_path = None
        if igdb_data and igdb_data.get('cover') and igdb_data['cover'].get('url'):
            cover_path = self.download_cover_art(
                igdb_data['cover']['url'], 
                game_name
            )
        elif igdb_data and igdb_data.get('cover_path'):
            # Use placeholder cover if available
            cover_path = igdb_data['cover_path']
        
        # If no cover path yet, create a placeholder
        if not cover_path:
            cover_path = self.create_placeholder_cover(game_name)
            
        # Store in database
        self.store_game_metadata(game_name, igdb_data, cover_path)
        
        # Return the stored data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM games WHERE name = ?', (game_name,))
        row = cursor.fetchone()
        conn.close()
        
        return self.row_to_dict(row) if row else None
        
    def row_to_dict(self, row):
        """Convert database row to dictionary."""
        columns = [
            'id', 'name', 'igdb_id', 'cover_url', 'cover_path', 'rating', 
            'rating_count', 'summary', 'genres', 'platforms', 'release_date',
            'developer', 'publisher', 'steam_id', 'metacritic_score', 'last_updated'
        ]
        
        data = dict(zip(columns, row))
        
        # Parse JSON fields
        for field in ['genres', 'platforms', 'developer', 'publisher']:
            if data[field]:
                try:
                    data[field] = json.loads(data[field])
                except:
                    data[field] = []
            else:
                data[field] = []
                
        return data
        
    def batch_download_metadata(self, game_names, progress_callback=None):
        """Download metadata for multiple games."""
        results = []
        
        for i, game_name in enumerate(game_names):
            progress_msg = f"Processing {i+1}/{len(game_names)}: {game_name}"
            print(progress_msg)
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(progress_msg, i+1, len(game_names))
            
            try:
                metadata = self.get_game_metadata(game_name)
                results.append(metadata)
                
                # Rate limiting - be nice to Screenscraper.fr
                time.sleep(0.1)  # Much faster since it's unlimited
                
            except Exception as e:
                error_msg = f"Error processing {game_name}: {e}"
                print(error_msg)
                if progress_callback:
                    progress_callback(error_msg, i+1, len(game_names))
                results.append(None)
                
        return results


def main():
    """Test the metadata downloader."""
    downloader = GameMetadataDownloader()
    
    # Test with a few games
    test_games = [
        "SkyrimSE",
        "Stardew Valley", 
        "Elden Ring",
        "The Witcher 3"
    ]
    
    print("Testing metadata downloader...")
    results = downloader.batch_download_metadata(test_games)
    
    for result in results:
        if result:
            print(f"\nGame: {result['name']}")
            print(f"Rating: {result['rating']}")
            print(f"Genres: {', '.join(result['genres'])}")
            print(f"Cover: {result['cover_path']}")
        else:
            print("Failed to get metadata")


if __name__ == "__main__":
    main()
