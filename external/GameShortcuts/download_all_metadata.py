#!/usr/bin/env python3
"""
Quick metadata downloader for all games
"""

from metadata_downloader import GameMetadataDownloader
import os
from pathlib import Path

def main():
    # Game directories
    game_dirs = [
        r"E:\Desktop\Games",
        r"E:\Desktop\ROMs"
    ]
    
    # Load all game names
    game_names = []
    for game_dir in game_dirs:
        if os.path.exists(game_dir):
            for shortcut_file in Path(game_dir).glob("*.lnk"):
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
    
    print(f"Found {len(game_names)} games to process")
    
    # Download metadata
    downloader = GameMetadataDownloader()
    results = downloader.batch_download_metadata(game_names)
    
    print(f"Processed {len([r for r in results if r])} games successfully")

if __name__ == "__main__":
    main()
