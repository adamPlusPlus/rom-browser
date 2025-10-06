#!/usr/bin/env python3
"""
Smart Metadata Downloader
Downloads metadata in batches to respect API limits and maximize coverage.
"""

import os
import sqlite3
from pathlib import Path
from metadata_downloader import GameMetadataDownloader
import time
from datetime import datetime, timedelta

class SmartMetadataDownloader:
    def __init__(self):
        self.downloader = GameMetadataDownloader()
        self.db_path = Path("games.db")
        
    def get_games_without_metadata(self):
        """Get games that don't have real metadata yet."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get games that either don't exist in DB or have placeholder metadata
        cursor.execute('''
            SELECT name FROM games 
            WHERE rating IS NULL AND (summary IS NULL OR summary LIKE "%No detailed information available%")
        ''')
        
        games = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return games
    
    def get_all_game_names(self):
        """Get all game names from shortcuts directory."""
        game_names = []
        game_dir = Path("E:/Desktop/Games")
        
        if game_dir.exists():
            for shortcut_file in game_dir.glob("*.lnk"):
                game_name = shortcut_file.stem
                # Clean up game name
                suffixes_to_remove = [
                    ' (ModEngine)', ' (Protected)', ' (MCC Launcher)', ' (Startup)', ' (Pre-Launcher)',
                    ' (Mod - Armoredcore6)', ' (Mod - Darksouls3)', ' (Mod - Eldenring)',
                    ' (PS2)', ' (PSX)', ' (N64)', ' (GameCube)', ' (Wii)', ' (Dreamcast)',
                    ' (Genesis)', ' (SNES)', ' (NES)', ' (GBA)', ' (NDS)', ' (PSP)',
                    ' (MAME)', ' (C64)', ' (Amiga)', ' (Atari2600)'
                ]
                
                cleaned_name = game_name
                for suffix in suffixes_to_remove:
                    cleaned_name = cleaned_name.replace(suffix, '')
                    
                game_names.append(cleaned_name.strip())
        
        return game_names
    
    def download_batch(self, game_names, batch_size=40):
        """Download metadata for a batch of games."""
        print(f"🎯 Processing batch of {len(game_names)} games...")
        
        results = []
        for i, game_name in enumerate(game_names):
            print(f"Processing {i+1}/{len(game_names)}: {game_name}")
            
            try:
                metadata = self.downloader.get_game_metadata(game_name)
                results.append(metadata)
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing {game_name}: {e}")
                results.append(None)
                
        successful = len([r for r in results if r and (r.get('rating') is not None or (r.get('summary') and not r['summary'].startswith('Game: ')))])
        print(f"✅ Successfully downloaded metadata for {successful}/{len(game_names)} games")
        
        return results
    
    def smart_download(self):
        """Smart download that respects API limits."""
        print("🚀 Starting smart metadata download...")
        
        # Get all games
        all_games = self.get_all_game_names()
        print(f"📊 Found {len(all_games)} total games")
        
        # Get games without metadata
        games_without_metadata = self.get_games_without_metadata()
        print(f"📋 Found {len(games_without_metadata)} games without metadata")
        
        # If we have games without metadata, process them
        if games_without_metadata:
            print(f"🎯 Processing {len(games_without_metadata)} games without metadata...")
            self.download_batch(games_without_metadata)
        else:
            print("✅ All games already have metadata!")
        
        # Show final statistics
        self.show_statistics()
    
    def show_statistics(self):
        """Show current metadata statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM games')
        total_games = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM games WHERE rating IS NOT NULL OR (summary IS NOT NULL AND summary NOT LIKE "%No detailed information available%")')
        games_with_metadata = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 Final Statistics:")
        print(f"   Total games: {total_games}")
        print(f"   Games with metadata: {games_with_metadata}")
        print(f"   Coverage: {(games_with_metadata/total_games)*100:.1f}%")
        
        if games_with_metadata < total_games:
            remaining = total_games - games_with_metadata
            print(f"\n⏰ Remaining games: {remaining}")
            print(f"   Next batch can be processed tomorrow (API limit resets daily)")
            print(f"   Estimated days to complete: {(remaining/40)+1:.0f}")

def main():
    downloader = SmartMetadataDownloader()
    downloader.smart_download()

if __name__ == "__main__":
    main()
