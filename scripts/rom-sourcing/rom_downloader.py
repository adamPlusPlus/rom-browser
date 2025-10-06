#!/usr/bin/env python3
"""
ROM Batch Downloader
Python version of rom-download.sh
Downloads ROMs from ROM archives based on platform selection and download queue
Usage: python rom_downloader.py [platform] [subtype]
"""

import os
import sys
import json
import requests
import sqlite3
from pathlib import Path
import time
from datetime import datetime
import urllib.parse
import subprocess
import shutil
from typing import List, Dict, Optional, Tuple
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


class ROMDownloader:
    def __init__(self):
        # Configuration
        self.base_url_redump = "https://myrient.erista.me/files/Redump/"
        self.base_url_noin = "https://myrient.erista.me/files/No-Intro/"
        self.rom_archive_base_url = self.base_url_redump
        self.download_dir = Path("./downloads")
        self.queue_file = Path("./download_queue")
        self.log_file = Path("./download_log.txt")
        self.temp_dir = Path("./temp")
        
        # Available platforms and their subtypes
        self.platforms = {
            "Nintendo - Nintendo Entertainment System": "NES",
            "Nintendo - Super Nintendo Entertainment System": "SNES",
            "Nintendo - Nintendo 64": "N64",
            "Nintendo - Nintendo GameCube": "NGC",
            "Nintendo - Nintendo Wii": "WII",
            "Nintendo - Nintendo Wii U": "WIIU",
            "Nintendo - Nintendo Switch": "NSW",
            "Sony - PlayStation": "PS1",
            "Sony - PlayStation 2": "PS2",
            "Sony - PlayStation 3": "PS3",
            "Sony - PlayStation 4": "PS4",
            "Sony - PlayStation 5": "PS5",
            "Sony - PlayStation Portable": "PSP",
            "Sony - PlayStation Vita": "PSV",
            "Microsoft - Xbox": "XBOX",
            "Microsoft - Xbox 360": "X360",
            "Microsoft - Xbox One": "XONE",
            "Microsoft - Xbox Series X|S": "XSX",
            "Sega - Master System": "SMS",
            "Sega - Mega Drive - Genesis": "MD",
            "Sega - Sega CD": "SCD",
            "Sega - Sega 32X": "32X",
            "Sega - Sega Saturn": "SAT",
            "Sega - Dreamcast": "DC",
            "Atari - 2600": "A2600",
            "Atari - 5200": "A5200",
            "Atari - 7800": "A7800",
            "Atari - Jaguar": "JAG",
            "Atari - Lynx": "LYNX",
            "NEC - PC Engine - TurboGrafx-16": "PCE",
            "NEC - PC Engine CD - TurboGrafx-CD": "PCE-CD",
            "NEC - PC Engine SuperGrafx": "SGX",
            "NEC - PC-FX": "PCFX",
            "SNK - Neo Geo": "NEO",
            "SNK - Neo Geo CD": "NGCD",
            "SNK - Neo Geo Pocket": "NGP",
            "SNK - Neo Geo Pocket Color": "NGPC",
            "Bandai - WonderSwan": "WS",
            "Bandai - WonderSwan Color": "WSC",
            "Commodore - Amiga": "AMIGA",
            "Commodore - Commodore 64": "C64",
            "Commodore - Amiga CD32": "CD32",
            "Apple - Apple II": "APPLE2",
            "Apple - Macintosh": "MAC",
            "IBM - PC": "PC",
            "IBM - PC DOS": "DOS",
            "IBM - PC Windows": "WIN",
            "IBM - PC Linux": "LINUX",
            "IBM - PC macOS": "MACOS",
            "IBM - PC Android": "ANDROID",
            "IBM - PC iOS": "IOS",
            "IBM - PC Web": "WEB",
            "IBM - PC VR": "VR",
            "IBM - PC AR": "AR",
            "IBM - PC Cloud": "CLOUD",
            "IBM - PC Mobile": "MOBILE",
            "IBM - PC Handheld": "HANDHELD",
            "IBM - PC Console": "CONSOLE",
            "IBM - PC Arcade": "ARCADE",
            "IBM - PC Pinball": "PINBALL",
            "IBM - PC Casino": "CASINO",
            "IBM - PC Educational": "EDU",
            "IBM - PC Sports": "SPORTS",
            "IBM - PC Racing": "RACING",
            "IBM - PC Fighting": "FIGHTING",
            "IBM - PC Shooter": "SHOOTER",
            "IBM - PC Adventure": "ADV",
            "IBM - PC RPG": "RPG",
            "IBM - PC Strategy": "STRAT",
            "IBM - PC Simulation": "SIM",
            "IBM - PC Puzzle": "PUZZLE",
            "IBM - PC Platformer": "PLAT",
            "IBM - PC Action": "ACTION",
            "IBM - PC Horror": "HORROR",
            "IBM - PC Comedy": "COMEDY",
            "IBM - PC Drama": "DRAMA",
            "IBM - PC Sci-Fi": "SCIFI",
            "IBM - PC Fantasy": "FANTASY",
            "IBM - PC Historical": "HIST",
            "IBM - PC Military": "MIL",
            "IBM - PC Western": "WESTERN",
            "IBM - PC Crime": "CRIME",
            "IBM - PC Mystery": "MYSTERY",
            "IBM - PC Thriller": "THRILLER",
            "IBM - PC Romance": "ROMANCE",
            "IBM - PC Musical": "MUSICAL",
            "IBM - PC Documentary": "DOC",
            "IBM - PC Animation": "ANIM",
            "IBM - PC Family": "FAMILY",
            "IBM - PC Children": "CHILDREN",
            "IBM - PC Teen": "TEEN",
            "IBM - PC Adult": "ADULT",
            "IBM - PC Mature": "MATURE",
            "IBM - PC Everyone": "EVERYONE",
            "IBM - PC Everyone 10+": "E10+",
            "IBM - PC Teen 13+": "T13+",
            "IBM - PC Mature 17+": "M17+",
            "IBM - PC Adults Only 18+": "AO18+",
            "IBM - PC Rating Pending": "RP",
            "IBM - PC Not Rated": "NR",
            "IBM - PC Unrated": "UR",
            "IBM - PC Unknown": "UNK",
            "IBM - PC Other": "OTHER"
        }
        
        # Download statistics
        self.download_stats = {
            'total_files': 0,
            'downloaded_files': 0,
            'failed_files': 0,
            'skipped_files': 0,
            'total_size': 0,
            'downloaded_size': 0
        }
        
        # Create directories
        self.download_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize log file
        self.log_message(f"ROM Download Session Started: {datetime.now()}")
    
    def log_message(self, message: str):
        """Log message to file and stdout."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        print(log_entry)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")
    
    def show_platform_menu(self):
        """Display platform selection menu."""
        self.log_message(f"{Colors.CYAN}Available Platforms:{Colors.NC}")
        self.log_message(f"{Colors.YELLOW}Enter platform name or number:{Colors.NC}")
        print()
        
        platforms_list = list(self.platforms.keys())
        for i, platform in enumerate(platforms_list, 1):
            print(f"{Colors.BLUE}{i:2d}.{Colors.NC} {platform}")
        print()
    
    def get_platform_choice(self) -> Optional[str]:
        """Get platform choice from user."""
        platforms_list = list(self.platforms.keys())
        
        while True:
            choice = input(f"{Colors.CYAN}Enter platform name or number: {Colors.NC}").strip()
            
            if not choice:
                return None
            
            # Try to parse as number
            try:
                num_choice = int(choice)
                if 1 <= num_choice <= len(platforms_list):
                    return platforms_list[num_choice - 1]
                else:
                    print(f"{Colors.RED}Invalid number. Please enter a number between 1 and {len(platforms_list)}{Colors.NC}")
                    continue
            except ValueError:
                pass
            
            # Try to find by name (case-insensitive)
            choice_lower = choice.lower()
            for platform in platforms_list:
                if choice_lower in platform.lower():
                    return platform
            
            # Try to find by abbreviation
            for platform, abbrev in self.platforms.items():
                if choice_lower == abbrev.lower():
                    return platform
            
            print(f"{Colors.RED}Platform not found. Please try again.{Colors.NC}")
    
    def select_dataset(self) -> str:
        """Select dataset (Redump or No-Intro)."""
        print(f"\n{Colors.CYAN}Select Dataset:{Colors.NC}")
        print("1. Redump")
        print("2. No-Intro")
        
        while True:
            choice = input(f"{Colors.CYAN}Enter choice (1-2): {Colors.NC}").strip()
            
            if choice == '1':
                self.rom_archive_base_url = self.base_url_redump
                return "Redump"
            elif choice == '2':
                self.rom_archive_base_url = self.base_url_noin
                return "No-Intro"
            else:
                print(f"{Colors.RED}Invalid choice. Please enter 1 or 2.{Colors.NC}")
    
    def download_index(self, url: str) -> Optional[str]:
        """Download and save index page."""
        try:
            self.log_message(f"{Colors.CYAN}Downloading index from {url}...{Colors.NC}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            index_file = self.temp_dir / "platform_index.html"
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            self.log_message(f"{Colors.GREEN}Index downloaded successfully{Colors.NC}")
            return str(index_file)
            
        except Exception as e:
            self.log_message(f"{Colors.RED}Failed to download index: {e}{Colors.NC}")
            return None
    
    def parse_platform_index(self, index_file: str) -> List[str]:
        """Parse platform index and extract ROM files."""
        rom_files = []
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple HTML parsing - look for href attributes pointing to ROM files
            import re
            
            # Find all href attributes
            href_pattern = r'href="([^"]+)"'
            hrefs = re.findall(href_pattern, content)
            
            # ROM file extensions
            rom_extensions = {'.zip', '.7z', '.rar', '.iso', '.bin', '.cue', '.img', '.mdf', '.mds'}
            
            for href in hrefs:
                # Skip directories and non-ROM files
                if href.endswith('/') or href.startswith('http'):
                    continue
                
                # Check if it's a ROM file
                file_path = Path(href)
                if file_path.suffix.lower() in rom_extensions:
                    decoded_href = urllib.parse.unquote(href)
                    rom_files.append(decoded_href)
            
            rom_files.sort()
            
        except Exception as e:
            self.log_message(f"{Colors.RED}Error parsing index: {e}{Colors.NC}")
        
        return rom_files
    
    def get_file_size(self, url: str) -> int:
        """Get file size from URL."""
        try:
            response = requests.head(url, timeout=10)
            content_length = response.headers.get('content-length')
            if content_length:
                return int(content_length)
        except Exception:
            pass
        return 0
    
    def download_file(self, url: str, filename: str) -> bool:
        """Download a single file."""
        try:
            file_path = self.download_dir / filename
            
            # Check if file already exists
            if file_path.exists():
                self.log_message(f"{Colors.YELLOW}Skipping existing file: {filename}{Colors.NC}")
                self.download_stats['skipped_files'] += 1
                return True
            
            # Get file size for progress tracking
            file_size = self.get_file_size(url)
            self.download_stats['total_size'] += file_size
            
            self.log_message(f"{Colors.CYAN}Downloading: {filename} ({file_size:,} bytes){Colors.NC}")
            
            # Download file
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            downloaded_size = 0
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Show progress for large files
                        if file_size > 0 and downloaded_size % (1024 * 1024) == 0:  # Every MB
                            progress = (downloaded_size / file_size) * 100
                            print(f"\r{Colors.CYAN}Progress: {progress:.1f}% ({downloaded_size:,}/{file_size:,} bytes){Colors.NC}", end='', flush=True)
            
            if file_size > 0:
                print()  # New line after progress
            
            self.download_stats['downloaded_files'] += 1
            self.download_stats['downloaded_size'] += downloaded_size
            
            self.log_message(f"{Colors.GREEN}Downloaded: {filename}{Colors.NC}")
            return True
            
        except Exception as e:
            self.log_message(f"{Colors.RED}Failed to download {filename}: {e}{Colors.NC}")
            self.download_stats['failed_files'] += 1
            return False
    
    def download_platform_roms(self, platform: str, max_files: Optional[int] = None):
        """Download all ROMs for a platform."""
        platform_url = f"{self.rom_archive_base_url}{urllib.parse.quote(platform)}/"
        
        # Download platform index
        index_file = self.download_index(platform_url)
        if not index_file:
            return
        
        # Parse ROM files
        rom_files = self.parse_platform_index(index_file)
        
        if not rom_files:
            self.log_message(f"{Colors.YELLOW}No ROM files found for platform: {platform}{Colors.NC}")
            return
        
        # Limit files if specified
        if max_files:
            rom_files = rom_files[:max_files]
        
        self.download_stats['total_files'] = len(rom_files)
        
        self.log_message(f"{Colors.CYAN}Found {len(rom_files)} ROM files for {platform}{Colors.NC}")
        
        # Download files
        for i, rom_file in enumerate(rom_files, 1):
            file_url = f"{platform_url}{urllib.parse.quote(rom_file)}"
            
            self.log_message(f"{Colors.CYAN}Downloading file {i}/{len(rom_files)}: {rom_file}{Colors.NC}")
            
            if self.download_file(file_url, rom_file):
                # Small delay to be respectful to the server
                time.sleep(0.5)
            else:
                # Longer delay on failure
                time.sleep(2)
    
    def download_from_queue(self):
        """Download files from the download queue."""
        if not self.queue_file.exists():
            self.log_message(f"{Colors.YELLOW}No download queue file found{Colors.NC}")
            return
        
        try:
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                queue_items = [line.strip() for line in f if line.strip()]
            
            if not queue_items:
                self.log_message(f"{Colors.YELLOW}Download queue is empty{Colors.NC}")
                return
            
            self.download_stats['total_files'] = len(queue_items)
            
            self.log_message(f"{Colors.CYAN}Downloading {len(queue_items)} files from queue{Colors.NC}")
            
            # Download files from queue
            for i, url in enumerate(queue_items, 1):
                filename = url.split('/')[-1]
                decoded_filename = urllib.parse.unquote(filename)
                
                self.log_message(f"{Colors.CYAN}Downloading file {i}/{len(queue_items)}: {decoded_filename}{Colors.NC}")
                
                if self.download_file(url, decoded_filename):
                    time.sleep(0.5)
                else:
                    time.sleep(2)
            
            # Clear queue after successful download
            self.queue_file.unlink()
            self.log_message(f"{Colors.GREEN}Download queue cleared{Colors.NC}")
            
        except Exception as e:
            self.log_message(f"{Colors.RED}Error processing download queue: {e}{Colors.NC}")
    
    def show_download_stats(self):
        """Show download statistics."""
        stats = self.download_stats
        
        print(f"\n{Colors.CYAN}Download Statistics:{Colors.NC}")
        print("=" * 40)
        print(f"Total files: {stats['total_files']}")
        print(f"Downloaded: {stats['downloaded_files']}")
        print(f"Failed: {stats['failed_files']}")
        print(f"Skipped: {stats['skipped_files']}")
        
        if stats['total_size'] > 0:
            print(f"Total size: {stats['total_size']:,} bytes ({stats['total_size'] / (1024*1024*1024):.2f} GB)")
            print(f"Downloaded: {stats['downloaded_size']:,} bytes ({stats['downloaded_size'] / (1024*1024*1024):.2f} GB)")
        
        success_rate = (stats['downloaded_files'] / stats['total_files'] * 100) if stats['total_files'] > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
    
    def main_menu(self):
        """Main menu loop."""
        while True:
            print(f"\n{Colors.CYAN}ROM Batch Downloader{Colors.NC}")
            print("=" * 30)
            print("1. Download by platform")
            print("2. Download from queue")
            print("3. Switch dataset")
            print("4. Show statistics")
            print("5. Help")
            print("6. Quit")
            
            choice = input(f"\n{Colors.CYAN}Enter choice: {Colors.NC}").strip()
            
            if choice == '1':
                self.download_by_platform()
            elif choice == '2':
                self.download_from_queue()
            elif choice == '3':
                dataset = self.select_dataset()
                self.log_message(f"{Colors.GREEN}Switched to {dataset} dataset{Colors.NC}")
            elif choice == '4':
                self.show_download_stats()
            elif choice == '5':
                self.show_help()
            elif choice == '6':
                break
            else:
                print(f"{Colors.RED}Invalid choice{Colors.NC}")
    
    def download_by_platform(self):
        """Download ROMs by platform selection."""
        self.show_platform_menu()
        
        platform = self.get_platform_choice()
        if not platform:
            return
        
        # Ask for file limit
        max_files_input = input(f"{Colors.CYAN}Maximum files to download (Enter for all): {Colors.NC}").strip()
        max_files = None
        
        if max_files_input:
            try:
                max_files = int(max_files_input)
                if max_files <= 0:
                    print(f"{Colors.RED}Invalid number{Colors.NC}")
                    return
            except ValueError:
                print(f"{Colors.RED}Invalid number{Colors.NC}")
                return
        
        # Confirm download
        print(f"\n{Colors.YELLOW}About to download ROMs for: {platform}{Colors.NC}")
        if max_files:
            print(f"{Colors.YELLOW}Maximum files: {max_files}{Colors.NC}")
        
        confirm = input(f"{Colors.CYAN}Continue? (y/N): {Colors.NC}").strip().lower()
        if confirm not in ['y', 'yes']:
            return
        
        # Download ROMs
        self.download_platform_roms(platform, max_files)
    
    def show_help(self):
        """Show help information."""
        help_text = f"""
{Colors.CYAN}ROM Batch Downloader Help{Colors.NC}
===============================

{Colors.GREEN}Features:{Colors.NC}
  • Download ROMs by platform selection
  • Download from download queue
  • Support for Redump and No-Intro datasets
  • Progress tracking and statistics
  • Automatic retry on failures

{Colors.GREEN}Usage:{Colors.NC}
  • Select option 1 to download by platform
  • Select option 2 to download from queue
  • Use option 3 to switch between datasets

{Colors.GREEN}Platform Selection:{Colors.NC}
  • Enter platform name (e.g., "PlayStation 2")
  • Enter platform abbreviation (e.g., "PS2")
  • Enter platform number from the list

{Colors.GREEN}Download Queue:{Colors.NC}
  • Files are added to queue by the ROM browser
  • Queue file: {self.queue_file}
  • Queue is automatically cleared after download

{Colors.GREEN}File Storage:{Colors.NC}
  • Downloaded files are saved to: {self.download_dir}
  • Existing files are automatically skipped
  • Download log: {self.log_file}
"""
        print(help_text)
    
    def run(self):
        """Run the ROM downloader."""
        try:
            print(f"{Colors.GREEN}ROM Batch Downloader - Python Version{Colors.NC}")
            print(f"{Colors.GREEN}Starting ROM downloader...{Colors.NC}")
            
            self.main_menu()
            
            self.show_download_stats()
            print(f"\n{Colors.GREEN}ROM Downloader session ended{Colors.NC}")
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}ROM Downloader interrupted by user{Colors.NC}")
            self.show_download_stats()
        except Exception as e:
            self.log_message(f"{Colors.RED}Fatal error: {e}{Colors.NC}")
            print(f"{Colors.RED}Fatal error: {e}{Colors.NC}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='ROM Batch Downloader')
    parser.add_argument('--platform', help='Platform to download')
    parser.add_argument('--dataset', choices=['redump', 'no-intro'], 
                       default='redump', help='Dataset to use')
    parser.add_argument('--max-files', type=int, help='Maximum files to download')
    parser.add_argument('--queue', action='store_true', help='Download from queue only')
    
    args = parser.parse_args()
    
    downloader = ROMDownloader()
    
    # Apply command line arguments
    if args.dataset == 'no-intro':
        downloader.rom_archive_base_url = downloader.base_url_noin
    
    if args.queue:
        # Download from queue only
        downloader.download_from_queue()
        downloader.show_download_stats()
    elif args.platform:
        # Download specific platform
        downloader.download_platform_roms(args.platform, args.max_files)
        downloader.show_download_stats()
    else:
        # Interactive mode
        downloader.run()


if __name__ == "__main__":
    main()
