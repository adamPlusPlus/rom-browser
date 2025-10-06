#!/usr/bin/env python3
"""
ROM Browser - Interactive CLI browser for ROM archives
Python version of rom-browse.sh
Supports multiple ROM sources including Myrient.erista.me
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


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


class ROMBrowser:
    def __init__(self):
        # Configuration
        self.base_url_redump = "https://myrient.erista.me/files/Redump/"
        self.base_url_noin = "https://myrient.erista.me/files/No-Intro/"
        self.temp_dir = Path("./temp")
        self.downloads_dir = Path("../downloads")
        self.log_file = Path("./rom-browse.log")
        self.queue_file = Path("./download_queue")
        self.page_size = 50
        self.filter_file = Path("../config/rom-filter.txt")
        self.history_file = Path("./rom-browse-history.txt")
        
        # Current state
        self.current_url = self.base_url_redump
        self.current_dataset = "Redump"
        self.history = []
        self.download_queue = []
        
        # Create directories
        self.temp_dir.mkdir(exist_ok=True)
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Load state
        self.load_history()
        self.load_download_queue()
        
    def log(self, message: str):
        """Log message to file and stderr."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(message, file=sys.stderr)
    
    def load_history(self):
        """Load browsing history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = [line.strip() for line in f if line.strip()]
            except Exception as e:
                self.log(f"{Colors.YELLOW}Warning: Could not load history: {e}{Colors.NC}")
                self.history = []
        else:
            self.history = []
    
    def save_history(self):
        """Save browsing history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                for entry in self.history:
                    f.write(f"{entry}\n")
        except Exception as e:
            self.log(f"{Colors.YELLOW}Warning: Could not save history: {e}{Colors.NC}")
    
    def load_download_queue(self):
        """Load download queue from file."""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    self.download_queue = [line.strip() for line in f if line.strip()]
            except Exception as e:
                self.log(f"{Colors.YELLOW}Warning: Could not load download queue: {e}{Colors.NC}")
                self.download_queue = []
        else:
            self.download_queue = []
    
    def save_download_queue(self):
        """Save download queue to file."""
        try:
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                for item in self.download_queue:
                    f.write(f"{item}\n")
        except Exception as e:
            self.log(f"{Colors.YELLOW}Warning: Could not save download queue: {e}{Colors.NC}")
    
    def add_to_history(self, url: str):
        """Add URL to browsing history."""
        if url not in self.history:
            self.history.append(url)
            # Keep only last 100 entries
            if len(self.history) > 100:
                self.history = self.history[-100:]
            self.save_history()
    
    def download_index(self, url: str) -> Optional[str]:
        """Download and parse index page."""
        try:
            self.log(f"{Colors.CYAN}Downloading index from {url}...{Colors.NC}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            index_file = self.temp_dir / "index.html"
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            self.log(f"{Colors.GREEN}Index downloaded successfully{Colors.NC}")
            return str(index_file)
            
        except Exception as e:
            self.log(f"{Colors.RED}Failed to download index: {e}{Colors.NC}")
            return None
    
    def parse_index(self, index_file: str) -> Tuple[List[str], List[str]]:
        """Parse index file and extract directories and files."""
        directories = []
        files = []
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple HTML parsing - look for href attributes
            import re
            
            # Find all href attributes
            href_pattern = r'href="([^"]+)"'
            hrefs = re.findall(href_pattern, content)
            
            for href in hrefs:
                # Skip parent directory and absolute URLs
                if href in ['../', '..'] or href.startswith('http'):
                    continue
                
                # Skip query parameters
                if '?' in href:
                    continue
                
                # Decode URL
                decoded_href = urllib.parse.unquote(href)
                
                if href.endswith('/'):
                    # Directory
                    dir_name = decoded_href.rstrip('/')
                    if dir_name and dir_name not in directories:
                        directories.append(dir_name)
                else:
                    # File
                    if decoded_href and decoded_href not in files:
                        files.append(decoded_href)
            
            # Sort both lists
            directories.sort()
            files.sort()
            
        except Exception as e:
            self.log(f"{Colors.RED}Error parsing index: {e}{Colors.NC}")
        
        return directories, files
    
    def apply_filters(self, items: List[str]) -> List[str]:
        """Apply filters to items list."""
        if not self.filter_file.exists():
            return items
        
        try:
            with open(self.filter_file, 'r', encoding='utf-8') as f:
                filter_lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
            
            filtered_items = items.copy()
            
            for filter_line in filter_lines:
                filtered_items = [item for item in filtered_items if filter_line.lower() not in item.lower()]
            
            return filtered_items
            
        except Exception as e:
            self.log(f"{Colors.YELLOW}Warning: Could not apply filters: {e}{Colors.NC}")
            return items
    
    def display_items(self, items: List[str], item_type: str, page: int = 1):
        """Display items with pagination."""
        if not items:
            print(f"{Colors.YELLOW}No {item_type} found{Colors.NC}")
            return
        
        total_items = len(items)
        total_pages = (total_items + self.page_size - 1) // self.page_size
        
        start_idx = (page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_items)
        
        print(f"\n{Colors.CYAN}{item_type.title()} (Page {page}/{total_pages}) - Items {start_idx + 1}-{end_idx} of {total_items}{Colors.NC}")
        print("=" * 60)
        
        for i, item in enumerate(items[start_idx:end_idx], start=start_idx + 1):
            print(f"{i:3d}. {item}")
        
        print("=" * 60)
    
    def get_user_choice(self, max_choice: int) -> Optional[int]:
        """Get user choice from input."""
        try:
            choice = input(f"\n{Colors.CYAN}Enter choice (1-{max_choice}) or command: {Colors.NC}").strip()
            
            if not choice:
                return None
            
            # Check for commands
            if choice.lower() in ['q', 'quit', 'exit']:
                return -1
            elif choice.lower() in ['h', 'help']:
                self.show_help()
                return None
            elif choice.lower() in ['b', 'back']:
                return -2
            elif choice.lower() in ['f', 'filter']:
                self.manage_filters()
                return None
            elif choice.lower() in ['d', 'download']:
                self.show_download_queue()
                return None
            
            # Try to parse as number
            try:
                num_choice = int(choice)
                if 1 <= num_choice <= max_choice:
                    return num_choice
                else:
                    print(f"{Colors.RED}Invalid choice. Please enter a number between 1 and {max_choice}{Colors.NC}")
                    return None
            except ValueError:
                print(f"{Colors.RED}Invalid input. Please enter a number or command{Colors.NC}")
                return None
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Operation cancelled{Colors.NC}")
            return -1
        except EOFError:
            return -1
    
    def show_help(self):
        """Show help information."""
        help_text = f"""
{Colors.CYAN}ROM Browser Help{Colors.NC}
================

{Colors.GREEN}Navigation:{Colors.NC}
  • Enter a number to select an item
  • 'b' or 'back' - Go back to previous directory
  • 'q' or 'quit' - Exit the browser

{Colors.GREEN}Commands:{Colors.NC}
  • 'h' or 'help' - Show this help
  • 'f' or 'filter' - Manage filters
  • 'd' or 'download' - Show download queue

{Colors.GREEN}Filtering:{Colors.NC}
  • Filters are applied automatically
  • Edit {self.filter_file} to modify filters
  • Use 'f' command to manage filters interactively

{Colors.GREEN}Download Queue:{Colors.NC}
  • Items are added to queue for batch download
  • Use 'd' command to view and manage queue
"""
        print(help_text)
    
    def manage_filters(self):
        """Manage filter file."""
        print(f"\n{Colors.CYAN}Filter Management{Colors.NC}")
        print("1. View current filters")
        print("2. Add new filter")
        print("3. Edit filter file")
        print("4. Back")
        
        choice = input(f"{Colors.CYAN}Enter choice: {Colors.NC}").strip()
        
        if choice == '1':
            self.view_filters()
        elif choice == '2':
            self.add_filter()
        elif choice == '3':
            self.edit_filters()
        elif choice == '4':
            return
        else:
            print(f"{Colors.RED}Invalid choice{Colors.NC}")
    
    def view_filters(self):
        """View current filters."""
        if not self.filter_file.exists():
            print(f"{Colors.YELLOW}No filter file found{Colors.NC}")
            return
        
        try:
            with open(self.filter_file, 'r', encoding='utf-8') as f:
                filters = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
            
            if not filters:
                print(f"{Colors.YELLOW}No active filters{Colors.NC}")
                return
            
            print(f"\n{Colors.CYAN}Current filters:{Colors.NC}")
            for i, filter_line in enumerate(filters, 1):
                print(f"{i:2d}. {filter_line}")
                
        except Exception as e:
            print(f"{Colors.RED}Error reading filters: {e}{Colors.NC}")
    
    def add_filter(self):
        """Add a new filter."""
        filter_text = input(f"{Colors.CYAN}Enter filter text: {Colors.NC}").strip()
        
        if not filter_text:
            print(f"{Colors.RED}Filter text cannot be empty{Colors.NC}")
            return
        
        try:
            # Check if filter already exists
            if self.filter_file.exists():
                with open(self.filter_file, 'r', encoding='utf-8') as f:
                    existing_filters = [line.strip() for line in f]
                
                if filter_text in existing_filters:
                    print(f"{Colors.YELLOW}Filter already exists{Colors.NC}")
                    return
            
            # Add filter
            with open(self.filter_file, 'a', encoding='utf-8') as f:
                f.write(f"{filter_text}\n")
            
            print(f"{Colors.GREEN}Filter added: '{filter_text}'{Colors.NC}")
            
        except Exception as e:
            print(f"{Colors.RED}Error adding filter: {e}{Colors.NC}")
    
    def edit_filters(self):
        """Edit filter file with external editor."""
        editors = ['notepad', 'vim', 'nano', 'code', 'subl']
        
        editor = None
        for ed in editors:
            if shutil.which(ed):
                editor = ed
                break
        
        if not editor:
            print(f"{Colors.YELLOW}No text editor found. Please edit {self.filter_file} manually{Colors.NC}")
            return
        
        try:
            subprocess.run([editor, str(self.filter_file)], check=True)
            print(f"{Colors.GREEN}Filter file edited{Colors.NC}")
        except Exception as e:
            print(f"{Colors.RED}Error opening editor: {e}{Colors.NC}")
    
    def show_download_queue(self):
        """Show current download queue."""
        if not self.download_queue:
            print(f"{Colors.YELLOW}Download queue is empty{Colors.NC}")
            return
        
        print(f"\n{Colors.CYAN}Download Queue ({len(self.download_queue)} items){Colors.NC}")
        print("=" * 50)
        
        for i, item in enumerate(self.download_queue, 1):
            print(f"{i:3d}. {item}")
        
        print("=" * 50)
        print("Commands: 'c' - clear queue, 's' - save queue, 'b' - back")
        
        choice = input(f"{Colors.CYAN}Enter command: {Colors.NC}").strip().lower()
        
        if choice == 'c':
            self.download_queue.clear()
            self.save_download_queue()
            print(f"{Colors.GREEN}Queue cleared{Colors.NC}")
        elif choice == 's':
            self.save_download_queue()
            print(f"{Colors.GREEN}Queue saved{Colors.NC}")
        elif choice == 'b':
            return
        else:
            print(f"{Colors.RED}Invalid command{Colors.NC}")
    
    def add_to_queue(self, item: str):
        """Add item to download queue."""
        if item not in self.download_queue:
            self.download_queue.append(item)
            self.save_download_queue()
            print(f"{Colors.GREEN}Added to queue: {item}{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}Item already in queue: {item}{Colors.NC}")
    
    def browse_directory(self, url: str):
        """Browse a directory interactively."""
        self.add_to_history(url)
        
        while True:
            # Download and parse index
            index_file = self.download_index(url)
            if not index_file:
                return False
            
            directories, files = self.parse_index(index_file)
            
            # Apply filters
            directories = self.apply_filters(directories)
            files = self.apply_filters(files)
            
            # Display current location
            print(f"\n{Colors.CYAN}Current location: {url}{Colors.NC}")
            print(f"{Colors.CYAN}Dataset: {self.current_dataset}{Colors.NC}")
            
            # Display directories
            if directories:
                self.display_items(directories, "Directories")
                
                choice = self.get_user_choice(len(directories))
                
                if choice == -1:  # Quit
                    return False
                elif choice == -2:  # Back
                    return True
                elif choice is None:  # Invalid input
                    continue
                else:
                    # Navigate to selected directory
                    selected_dir = directories[choice - 1]
                    new_url = f"{url}{urllib.parse.quote(selected_dir)}/"
                    
                    if not self.browse_directory(new_url):
                        return False
                    continue
            
            # Display files
            if files:
                self.display_items(files, "Files")
                
                choice = self.get_user_choice(len(files))
                
                if choice == -1:  # Quit
                    return False
                elif choice == -2:  # Back
                    return True
                elif choice is None:  # Invalid input
                    continue
                else:
                    # Handle file selection
                    selected_file = files[choice - 1]
                    self.handle_file_selection(url, selected_file)
                    continue
            
            # No items found
            print(f"{Colors.YELLOW}No items found in this directory{Colors.NC}")
            return True
    
    def handle_file_selection(self, base_url: str, filename: str):
        """Handle file selection."""
        file_url = f"{base_url}{urllib.parse.quote(filename)}"
        
        print(f"\n{Colors.CYAN}File selected: {filename}{Colors.NC}")
        print("1. Add to download queue")
        print("2. Show URL")
        print("3. Copy URL to clipboard")
        print("4. Back")
        
        choice = input(f"{Colors.CYAN}Enter choice: {Colors.NC}").strip()
        
        if choice == '1':
            self.add_to_queue(file_url)
        elif choice == '2':
            print(f"{Colors.GREEN}URL: {file_url}{Colors.NC}")
        elif choice == '3':
            self.copy_to_clipboard(file_url)
        elif choice == '4':
            return
        else:
            print(f"{Colors.RED}Invalid choice{Colors.NC}")
    
    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        try:
            if sys.platform == "win32":
                subprocess.run(['clip'], input=text, text=True, check=True)
            elif sys.platform == "darwin":
                subprocess.run(['pbcopy'], input=text, text=True, check=True)
            else:
                subprocess.run(['xclip', '-selection', 'clipboard'], input=text, text=True, check=True)
            
            print(f"{Colors.GREEN}URL copied to clipboard{Colors.NC}")
            
        except Exception as e:
            print(f"{Colors.RED}Failed to copy to clipboard: {e}{Colors.NC}")
    
    def switch_dataset(self):
        """Switch between Redump and No-Intro datasets."""
        print(f"\n{Colors.CYAN}Current dataset: {self.current_dataset}{Colors.NC}")
        print("1. Redump")
        print("2. No-Intro")
        print("3. Back")
        
        choice = input(f"{Colors.CYAN}Enter choice: {Colors.NC}").strip()
        
        if choice == '1':
            self.current_dataset = "Redump"
            self.current_url = self.base_url_redump
            print(f"{Colors.GREEN}Switched to Redump dataset{Colors.NC}")
        elif choice == '2':
            self.current_dataset = "No-Intro"
            self.current_url = self.base_url_noin
            print(f"{Colors.GREEN}Switched to No-Intro dataset{Colors.NC}")
        elif choice == '3':
            return
        else:
            print(f"{Colors.RED}Invalid choice{Colors.NC}")
    
    def main_menu(self):
        """Main menu loop."""
        while True:
            print(f"\n{Colors.CYAN}ROM Browser - {self.current_dataset} Dataset{Colors.NC}")
            print("=" * 40)
            print("1. Browse ROMs")
            print("2. Switch dataset")
            print("3. Manage filters")
            print("4. View download queue")
            print("5. Help")
            print("6. Quit")
            
            choice = input(f"\n{Colors.CYAN}Enter choice: {Colors.NC}").strip()
            
            if choice == '1':
                if not self.browse_directory(self.current_url):
                    break
            elif choice == '2':
                self.switch_dataset()
            elif choice == '3':
                self.manage_filters()
            elif choice == '4':
                self.show_download_queue()
            elif choice == '5':
                self.show_help()
            elif choice == '6':
                break
            else:
                print(f"{Colors.RED}Invalid choice{Colors.NC}")
    
    def run(self):
        """Run the ROM browser."""
        try:
            print(f"{Colors.GREEN}ROM Browser - Python Version{Colors.NC}")
            print(f"{Colors.GREEN}Starting interactive ROM browser...{Colors.NC}")
            
            self.main_menu()
            
            print(f"\n{Colors.GREEN}ROM Browser session ended{Colors.NC}")
            print(f"{Colors.CYAN}Download queue saved to: {self.queue_file}{Colors.NC}")
            print(f"{Colors.CYAN}History saved to: {self.history_file}{Colors.NC}")
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}ROM Browser interrupted by user{Colors.NC}")
        except Exception as e:
            self.log(f"{Colors.RED}Fatal error: {e}{Colors.NC}")
            print(f"{Colors.RED}Fatal error: {e}{Colors.NC}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Interactive ROM browser')
    parser.add_argument('--dataset', choices=['redump', 'no-intro'], 
                       help='Start with specific dataset')
    parser.add_argument('--url', help='Start with specific URL')
    
    args = parser.parse_args()
    
    browser = ROMBrowser()
    
    # Apply command line arguments
    if args.dataset:
        if args.dataset == 'redump':
            browser.current_dataset = "Redump"
            browser.current_url = browser.base_url_redump
        else:
            browser.current_dataset = "No-Intro"
            browser.current_url = browser.base_url_noin
    
    if args.url:
        browser.current_url = args.url
    
    browser.run()


if __name__ == "__main__":
    main()
