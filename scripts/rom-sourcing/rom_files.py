#!/usr/bin/env python3
"""
Myrient /files interactive browser
Python version of rom-files.sh
- Start at https://myrient.erista.me/files/
- Navigate folders, filter by typing, select by number
- For files: print URL, copy URL to clipboard, or download
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
import re


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


class ROMFilesBrowser:
    def __init__(self):
        # Configuration
        self.root_url = "https://myrient.erista.me/files/"
        self.temp_dir = Path("./temp")
        self.download_dir = Path("./downloads")
        self.log_file = Path("./mbrowse_log.txt")
        
        # Current state
        self.current_url = self.root_url
        self.history = []
        
        # Create directories
        self.temp_dir.mkdir(exist_ok=True)
        self.download_dir.mkdir(exist_ok=True)
        
        # Load history
        self.load_history()
    
    def log(self, message: str):
        """Log message to file and stderr."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        print(message, file=sys.stderr)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")
    
    def load_history(self):
        """Load browsing history from file."""
        history_file = Path("./mbrowse_history.txt")
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.history = [line.strip() for line in f if line.strip()]
            except Exception as e:
                self.log(f"{Colors.YELLOW}Warning: Could not load history: {e}{Colors.NC}")
                self.history = []
        else:
            self.history = []
    
    def save_history(self):
        """Save browsing history to file."""
        history_file = Path("./mbrowse_history.txt")
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                for entry in self.history:
                    f.write(f"{entry}\n")
        except Exception as e:
            self.log(f"{Colors.YELLOW}Warning: Could not save history: {e}{Colors.NC}")
    
    def add_to_history(self, url: str):
        """Add URL to browsing history."""
        if url not in self.history:
            self.history.append(url)
            # Keep only last 50 entries
            if len(self.history) > 50:
                self.history = self.history[-50:]
            self.save_history()
    
    def urlencode(self, text: str) -> str:
        """Minimal URL encoding for common characters."""
        # Replace common characters with URL encoding
        replacements = {
            '%': '%25',
            ' ': '%20',
            '(': '%28',
            ')': '%29',
            '+': '%2B',
            '&': '%26',
            "'": '%27',
            ',': '%2C',
            '[': '%5B',
            ']': '%5D'
        }
        
        result = text
        for char, encoded in replacements.items():
            result = result.replace(char, encoded)
        
        return result
    
    def urldecode_display(self, text: str) -> str:
        """Decode URL-encoded characters for display."""
        # Replace URL encoding with readable characters
        replacements = {
            '%20': ' ',
            '%28': '(',
            '%29': ')',
            '%2B': '+',
            '%26': '&',
            '%27': "'",
            '%2C': ',',
            '%5B': '[',
            '%5D': ']',
            '%5b': '[',
            '%5d': ']'
        }
        
        result = text
        for encoded, char in replacements.items():
            result = result.replace(encoded, char)
        
        return result
    
    def download_index(self, url: str) -> Optional[str]:
        """Download and save index page."""
        try:
            self.log(f"{Colors.CYAN}Downloading index from {url}...{Colors.NC}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Myrient CLI)',
                'Accept-Encoding': 'gzip, deflate'
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
    
    def list_dirs_links(self, index_file: str) -> List[Tuple[str, str]]:
        """Extract directories from index file."""
        directories = []
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all href attributes pointing to directories
            href_pattern = r'href="([^"]+/)"'
            matches = re.findall(href_pattern, content)
            
            for href in matches:
                # Skip parent directory and absolute URLs
                if href in ['../', '..'] or href.startswith('http'):
                    continue
                
                # Skip query parameters
                if '?' in href:
                    continue
                
                # Skip navigation links
                skip_patterns = ['contact', 'donate', 'faq', 'upload', 'discord', 'telegram', 'hshop', 'home']
                if any(pattern in href.lower() for pattern in skip_patterns):
                    continue
                
                # Clean href
                clean_href = href.rstrip('/')
                
                # Try to get title attribute for display name
                display_name = clean_href
                
                # Look for title attribute in the same line
                title_pattern = rf'href="{re.escape(href)}"[^>]*title="([^"]*)"'
                title_match = re.search(title_pattern, content)
                if title_match:
                    display_name = title_match.group(1)
                
                # Decode URL for display
                display_name = self.urldecode_display(display_name)
                
                directories.append((display_name, href))
            
            # Sort by display name
            directories.sort(key=lambda x: x[0].lower())
            
        except Exception as e:
            self.log(f"{Colors.RED}Error parsing directories: {e}{Colors.NC}")
        
        return directories
    
    def list_files_links(self, index_file: str) -> List[Tuple[str, str]]:
        """Extract files from index file."""
        files = []
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all href attributes pointing to files (not directories)
            href_pattern = r'href="([^"]+)"'
            matches = re.findall(href_pattern, content)
            
            for href in matches:
                # Skip directories and absolute URLs
                if href.endswith('/') or href.startswith('http'):
                    continue
                
                # Skip query parameters
                if '?' in href:
                    continue
                
                # Skip navigation links
                skip_patterns = ['contact', 'donate', 'faq', 'upload', 'discord', 'telegram', 'hshop', 'home', 'Parent directory']
                if any(pattern in href.lower() for pattern in skip_patterns):
                    continue
                
                # Decode URL for display
                display_name = self.urldecode_display(href)
                
                files.append((display_name, href))
            
            # Sort by display name
            files.sort(key=lambda x: x[0].lower())
            
        except Exception as e:
            self.log(f"{Colors.RED}Error parsing files: {e}{Colors.NC}")
        
        return files
    
    def print_numbered_data(self, data: List[Tuple[str, str]], limit: int = 500):
        """Print numbered data with limit."""
        for i, (display_name, href) in enumerate(data[:limit], 1):
            print(f"{i:2d}. {display_name}")
    
    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to clipboard."""
        try:
            if sys.platform == "win32":
                subprocess.run(['clip'], input=text, text=True, check=True)
            elif sys.platform == "darwin":
                subprocess.run(['pbcopy'], input=text, text=True, check=True)
            else:
                subprocess.run(['xclip', '-selection', 'clipboard'], input=text, text=True, check=True)
            
            return True
            
        except Exception as e:
            self.log(f"{Colors.RED}Failed to copy to clipboard: {e}{Colors.NC}")
            return False
    
    def download_file(self, url: str, filename: str) -> bool:
        """Download a file."""
        try:
            file_path = self.download_dir / filename
            
            # Check if file already exists
            if file_path.exists():
                self.log(f"{Colors.YELLOW}File already exists: {filename}{Colors.NC}")
                return True
            
            self.log(f"{Colors.CYAN}Downloading: {filename}{Colors.NC}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Myrient CLI)'
            }
            
            response = requests.get(url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.log(f"{Colors.GREEN}Downloaded: {filename}{Colors.NC}")
            return True
            
        except Exception as e:
            self.log(f"{Colors.RED}Failed to download {filename}: {e}{Colors.NC}")
            return False
    
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
                return -3
            
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
{Colors.CYAN}Myrient Files Browser Help{Colors.NC}
===============================

{Colors.GREEN}Navigation:{Colors.NC}
  • Enter a number to select an item
  • 'b' or 'back' - Go back to previous directory
  • 'q' or 'quit' - Exit the browser

{Colors.GREEN}Commands:{Colors.NC}
  • 'h' or 'help' - Show this help
  • 'f' or 'filter' - Filter items by typing

{Colors.GREEN}File Operations:{Colors.NC}
  • For files: print URL, copy URL to clipboard, or download
  • Files are saved to: {self.download_dir}
  • Existing files are automatically skipped

{Colors.GREEN}History:{Colors.NC}
  • Browsing history is automatically saved
  • Use 'b' command to navigate back
"""
        print(help_text)
    
    def filter_items(self, items: List[Tuple[str, str]], filter_text: str) -> List[Tuple[str, str]]:
        """Filter items by text."""
        if not filter_text:
            return items
        
        filter_lower = filter_text.lower()
        filtered = []
        
        for display_name, href in items:
            if filter_lower in display_name.lower():
                filtered.append((display_name, href))
        
        return filtered
    
    def browse_directory(self, url: str):
        """Browse a directory interactively."""
        self.add_to_history(url)
        
        while True:
            # Download and parse index
            index_file = self.download_index(url)
            if not index_file:
                return False
            
            directories = self.list_dirs_links(index_file)
            files = self.list_files_links(index_file)
            
            # Display current location
            print(f"\n{Colors.CYAN}Current location: {url}{Colors.NC}")
            
            # Display directories
            if directories:
                print(f"\n{Colors.CYAN}Directories ({len(directories)}):{Colors.NC}")
                print("=" * 50)
                self.print_numbered_data(directories)
                
                choice = self.get_user_choice(len(directories))
                
                if choice == -1:  # Quit
                    return False
                elif choice == -2:  # Back
                    return True
                elif choice == -3:  # Filter
                    filter_text = input(f"{Colors.CYAN}Enter filter text: {Colors.NC}").strip()
                    filtered_dirs = self.filter_items(directories, filter_text)
                    if filtered_dirs:
                        print(f"\n{Colors.CYAN}Filtered directories ({len(filtered_dirs)}):{Colors.NC}")
                        print("=" * 50)
                        self.print_numbered_data(filtered_dirs)
                        
                        choice = self.get_user_choice(len(filtered_dirs))
                        if choice and choice > 0:
                            selected_dir = filtered_dirs[choice - 1]
                            new_url = f"{url}{self.urlencode(selected_dir[1])}"
                            
                            if not self.browse_directory(new_url):
                                return False
                            continue
                    else:
                        print(f"{Colors.YELLOW}No directories match filter{Colors.NC}")
                        continue
                elif choice is None:  # Invalid input
                    continue
                else:
                    # Navigate to selected directory
                    selected_dir = directories[choice - 1]
                    new_url = f"{url}{self.urlencode(selected_dir[1])}"
                    
                    if not self.browse_directory(new_url):
                        return False
                    continue
            
            # Display files
            if files:
                print(f"\n{Colors.CYAN}Files ({len(files)}):{Colors.NC}")
                print("=" * 50)
                self.print_numbered_data(files)
                
                choice = self.get_user_choice(len(files))
                
                if choice == -1:  # Quit
                    return False
                elif choice == -2:  # Back
                    return True
                elif choice == -3:  # Filter
                    filter_text = input(f"{Colors.CYAN}Enter filter text: {Colors.NC}").strip()
                    filtered_files = self.filter_items(files, filter_text)
                    if filtered_files:
                        print(f"\n{Colors.CYAN}Filtered files ({len(filtered_files)}):{Colors.NC}")
                        print("=" * 50)
                        self.print_numbered_data(filtered_files)
                        
                        choice = self.get_user_choice(len(filtered_files))
                        if choice and choice > 0:
                            selected_file = filtered_files[choice - 1]
                            self.handle_file_selection(url, selected_file)
                            continue
                    else:
                        print(f"{Colors.YELLOW}No files match filter{Colors.NC}")
                        continue
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
    
    def handle_file_selection(self, base_url: str, file_info: Tuple[str, str]):
        """Handle file selection."""
        display_name, href = file_info
        file_url = f"{base_url}{self.urlencode(href)}"
        
        print(f"\n{Colors.CYAN}File selected: {display_name}{Colors.NC}")
        print("1. Show URL")
        print("2. Copy URL to clipboard")
        print("3. Download file")
        print("4. Back")
        
        choice = input(f"{Colors.CYAN}Enter choice: {Colors.NC}").strip()
        
        if choice == '1':
            print(f"{Colors.GREEN}URL: {file_url}{Colors.NC}")
        elif choice == '2':
            if self.copy_to_clipboard(file_url):
                print(f"{Colors.GREEN}URL copied to clipboard{Colors.NC}")
            else:
                print(f"{Colors.RED}Failed to copy URL{Colors.NC}")
        elif choice == '3':
            self.download_file(file_url, display_name)
        elif choice == '4':
            return
        else:
            print(f"{Colors.RED}Invalid choice{Colors.NC}")
    
    def main_menu(self):
        """Main menu loop."""
        while True:
            print(f"\n{Colors.CYAN}Myrient Files Browser{Colors.NC}")
            print("=" * 30)
            print("1. Browse files")
            print("2. Go to specific URL")
            print("3. Show history")
            print("4. Help")
            print("5. Quit")
            
            choice = input(f"\n{Colors.CYAN}Enter choice: {Colors.NC}").strip()
            
            if choice == '1':
                if not self.browse_directory(self.current_url):
                    break
            elif choice == '2':
                url = input(f"{Colors.CYAN}Enter URL: {Colors.NC}").strip()
                if url:
                    if not url.startswith('http'):
                        url = f"https://myrient.erista.me/files/{url}"
                    self.current_url = url
                    if not self.browse_directory(url):
                        break
            elif choice == '3':
                self.show_history()
            elif choice == '4':
                self.show_help()
            elif choice == '5':
                break
            else:
                print(f"{Colors.RED}Invalid choice{Colors.NC}")
    
    def show_history(self):
        """Show browsing history."""
        if not self.history:
            print(f"{Colors.YELLOW}No browsing history{Colors.NC}")
            return
        
        print(f"\n{Colors.CYAN}Browsing History ({len(self.history)} entries):{Colors.NC}")
        print("=" * 50)
        
        for i, url in enumerate(self.history, 1):
            print(f"{i:2d}. {url}")
        
        print("=" * 50)
        print("Enter number to navigate to that URL, or 'b' to go back")
        
        choice = input(f"{Colors.CYAN}Enter choice: {Colors.NC}").strip()
        
        if choice.lower() == 'b':
            return
        
        try:
            num_choice = int(choice)
            if 1 <= num_choice <= len(self.history):
                selected_url = self.history[num_choice - 1]
                self.current_url = selected_url
                if not self.browse_directory(selected_url):
                    return
            else:
                print(f"{Colors.RED}Invalid number{Colors.NC}")
        except ValueError:
            print(f"{Colors.RED}Invalid input{Colors.NC}")
    
    def run(self):
        """Run the files browser."""
        try:
            print(f"{Colors.GREEN}Myrient Files Browser - Python Version{Colors.NC}")
            print(f"{Colors.GREEN}Starting interactive file browser...{Colors.NC}")
            
            self.main_menu()
            
            print(f"\n{Colors.GREEN}Files Browser session ended{Colors.NC}")
            print(f"{Colors.CYAN}History saved{Colors.NC}")
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Files Browser interrupted by user{Colors.NC}")
        except Exception as e:
            self.log(f"{Colors.RED}Fatal error: {e}{Colors.NC}")
            print(f"{Colors.RED}Fatal error: {e}{Colors.NC}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Myrient Files Browser')
    parser.add_argument('--url', help='Start with specific URL')
    parser.add_argument('--download', help='Download specific file URL')
    
    args = parser.parse_args()
    
    browser = ROMFilesBrowser()
    
    # Apply command line arguments
    if args.download:
        # Download specific file
        filename = args.download.split('/')[-1]
        browser.download_file(args.download, filename)
        return
    
    if args.url:
        browser.current_url = args.url
    
    browser.run()


if __name__ == "__main__":
    main()
