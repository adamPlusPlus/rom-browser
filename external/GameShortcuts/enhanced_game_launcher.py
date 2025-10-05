#!/usr/bin/env python3
"""
Enhanced Game Launcher with Metadata Viewer
Displays game collection with cover art and detailed metadata.
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
import threading
import json
from datetime import datetime
import win32com.client
from PIL import Image, ImageTk
import sqlite3
from io import StringIO
from metadata_downloader import GameMetadataDownloader
from custom_ratings_manager import CustomRatingsManager
from config_manager import ConfigManager


class LogWindow:
    """A pop-up/minimizable log window for displaying program activity."""
    
    def __init__(self, parent):
        self.parent = parent
        self.log_window = None
        self.log_text = None
        self.is_minimized = False
        
    def create_log_window(self):
        """Create the log window."""
        if self.log_window and self.log_window.winfo_exists():
            self.log_window.lift()
            return
            
        self.log_window = tk.Toplevel(self.parent)
        self.log_window.title("Game Launcher Logs")
        self.log_window.geometry("800x400")
        self.log_window.configure(bg='#1e1e1e')
        
        # Make it stay on top
        self.log_window.attributes('-topmost', True)
        
        # Create frame for controls
        control_frame = tk.Frame(self.log_window, bg='#1e1e1e')
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Minimize/Maximize button
        self.minimize_btn = tk.Button(
            control_frame, 
            text="📦 Minimize", 
            command=self.toggle_minimize,
            bg='#404040', 
            fg='white',
            font=('Arial', 10)
        )
        self.minimize_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        clear_btn = tk.Button(
            control_frame, 
            text="[DELETE] Clear", 
            command=self.clear_logs,
            bg='#404040', 
            fg='white',
            font=('Arial', 10)
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_cb = tk.Checkbutton(
            control_frame,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            bg='#1e1e1e',
            fg='white',
            selectcolor='#404040',
            font=('Arial', 10)
        )
        auto_scroll_cb.pack(side=tk.RIGHT, padx=5)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(
            self.log_window,
            bg='#2d2d2d',
            fg='#00ff00',
            font=('Consolas', 9),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Handle window close
        self.log_window.protocol("WM_DELETE_WINDOW", self.hide_window)
        
    def log(self, message):
        """Add a message to the log."""
        if not self.log_text:
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message)
        
        # Auto-scroll if enabled
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
            
        self.log_text.config(state=tk.DISABLED)
        
    def clear_logs(self):
        """Clear all logs."""
        if self.log_text:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)
            
    def toggle_minimize(self):
        """Toggle between minimized and normal state."""
        if not self.log_window:
            return
            
        if self.is_minimized:
            self.log_window.geometry("800x400")
            self.minimize_btn.config(text="📦 Minimize")
            self.is_minimized = False
        else:
            self.log_window.geometry("800x50")
            self.minimize_btn.config(text="📈 Maximize")
            self.is_minimized = True
            
    def hide_window(self):
        """Hide the log window."""
        if self.log_window:
            self.log_window.withdraw()
            
    def show_window(self):
        """Show the log window."""
        if self.log_window:
            self.log_window.deiconify()
            self.log_window.lift()
        else:
            self.create_log_window()


class EnhancedGameLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Game Collection Launcher")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#1e1e1e')
        
        # Initialize log window
        self.log_window = LogWindow(root)
        
        # Game directories
        self.game_dirs = [
            r"E:\Desktop\Games",
            r"E:\Desktop\ROMs"
        ]
        
        # Current games list
        self.games = []
        self.filtered_games = []
        self.favorites = set()
        
        # Sorting state
        self.sort_column = None
        self.sort_reverse = False
        
        # Current selected game
        self.selected_game = None
        
        # Metadata database
        self.db_path = Path("games.db")
        
        # Custom ratings manager
        self.custom_ratings_manager = CustomRatingsManager()
        
        # Configuration manager
        self.config_manager = ConfigManager()
        
        # Load favorites
        self.load_favorites()
        
        # GUI elements
        self.setup_ui()
        
        # Maximize window on startup
        self.root.state('zoomed')  # Windows
        try:
            self.root.attributes('-zoomed', True)  # Linux
        except:
            pass
        
        self.load_games()
        
    def setup_ui(self):
        """Setup the enhanced user interface."""
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors from config
        colors = self.config_manager.config["appearance"]["colors"]
        game_list_colors = self.config_manager.config["appearance"]["game_list"]
        
        style.configure('Treeview', 
                       background=colors["secondary_background"], 
                       foreground=colors["foreground"], 
                       fieldbackground=colors["secondary_background"])
        style.configure('Treeview.Heading', 
                       background=colors["border"], 
                       foreground=colors["foreground"])
        
        # Configure custom rating styling from config
        style.configure('custom_rating.Treeview', 
                       background=colors["secondary_background"], 
                       foreground=game_list_colors["custom_rating_color"], 
                       fieldbackground=colors["secondary_background"])
        style.configure('default_rating.Treeview', 
                       background=colors["secondary_background"], 
                       foreground=game_list_colors["rating_color"], 
                       fieldbackground=colors["secondary_background"])
        
        # Map the tags to actual styling
        style.map('custom_rating.Treeview',
                 foreground=[('selected', game_list_colors["custom_rating_color"]), 
                           ('!selected', game_list_colors["custom_rating_color"])])
        style.map('default_rating.Treeview',
                 foreground=[('selected', game_list_colors["rating_color"]), 
                           ('!selected', game_list_colors["rating_color"])])
        
        
        # Main frame
        main_frame = tk.Frame(self.root, bg=colors["background"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left panel (games list)
        left_panel = tk.Frame(main_frame, bg=colors["background"], width=800)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Right panel (metadata viewer)
        right_panel = tk.Frame(main_frame, bg=colors["background"], width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        # Setup left panel
        self.setup_left_panel(left_panel)
        
        # Setup right panel
        self.setup_right_panel(right_panel)
        
    def toggle_log_window(self):
        """Toggle the log window visibility."""
        if self.log_window.log_window and self.log_window.log_window.winfo_exists():
            self.log_window.show_window()
        else:
            self.log_window.create_log_window()
            
    def log(self, message):
        """Log a message to the log window."""
        self.log_window.log(message)
        
    def setup_left_panel(self, parent):
        """Setup the games list panel."""
        colors = self.config_manager.config["appearance"]["colors"]
        game_list_colors = self.config_manager.config["appearance"]["game_list"]
        
        # Header frame
        header_frame = tk.Frame(parent, bg=colors["background"])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Title
        title_label = tk.Label(header_frame, text="[GAME] Game Collection", 
                              font=('Segoe UI', 24, 'bold'), 
                              fg=colors["accent"], bg=colors["background"])
        title_label.pack(side=tk.LEFT)
        
        # Controls frame
        controls_frame = tk.Frame(header_frame, bg=colors["background"])
        controls_frame.pack(side=tk.RIGHT)
        
        # Refresh button
        refresh_btn = tk.Button(controls_frame, text="[REFRESH] Refresh", 
                               command=self.load_games,
                               bg=colors["accent"], fg=colors["foreground"], font=('Segoe UI', 10),
                               relief=tk.FLAT, padx=15, pady=5)
        refresh_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Download metadata button
        metadata_btn = tk.Button(controls_frame, text="📥 Download Metadata", 
                                command=self.download_metadata,
                                bg=colors["success"], fg=colors["foreground"], font=('Segoe UI', 10),
                                relief=tk.FLAT, padx=15, pady=5)
        metadata_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Log window button
        log_btn = tk.Button(controls_frame, text="[INFO] Show Logs", 
                           command=self.toggle_log_window,
                           bg=colors["border"], fg=colors["foreground"], font=('Segoe UI', 10),
                           relief=tk.FLAT, padx=15, pady=5)
        log_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Search and filter frame
        search_frame = tk.Frame(parent, bg=colors["background"])
        search_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_games)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=('Segoe UI', 12), width=50,
                               bg=colors["secondary_background"], 
                               fg=colors["foreground"], 
                               insertbackground=colors["foreground"],
                               relief=tk.FLAT, bd=5)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Search label
        search_label = tk.Label(search_frame, text="[SEARCH] Search:", 
                               font=('Segoe UI', 12), 
                               fg=colors["foreground"], 
                               bg=colors["background"])
        search_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Filter buttons
        filter_frame = tk.Frame(search_frame, bg=colors["background"])
        filter_frame.pack(side=tk.RIGHT)
        
        self.filter_var = tk.StringVar(value="All")
        self.filter_var.trace('w', self.filter_games)
        
        filter_buttons = [
            ("All", "All"),
            ("PC Games", "PC Game"),
            ("ROMs", "ROM"),
            ("Mods", "Mod"),
            ("Favorites", "Favorites")
        ]
        
        for text, value in filter_buttons:
            btn = tk.Radiobutton(filter_frame, text=text, variable=self.filter_var,
                                value=value, command=self.filter_games,
                                bg=colors["background"], 
                                fg=colors["foreground"], 
                                selectcolor=colors["accent"],
                                font=('Segoe UI', 10))
            btn.pack(side=tk.LEFT, padx=5)
        
        # Stats frame
        stats_frame = tk.Frame(parent, bg=colors["background"])
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_label = tk.Label(stats_frame, text="", 
                                    font=('Segoe UI', 11), 
                                    fg=colors["secondary_foreground"], 
                                    bg=colors["background"])
        self.stats_label.pack()
        
        # Filter section
        filter_frame = tk.Frame(parent, bg='#2e3440')
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Search box
        tk.Label(filter_frame, text="Search:", bg='#2e3440', fg='#d8dee9').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = tk.Entry(filter_frame, textvariable=self.search_var, bg='#3b4252', fg='#d8dee9', width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # Tag filter
        tk.Label(filter_frame, text="Filter by tags:", bg='#2e3440', fg='#d8dee9').pack(side=tk.LEFT)
        self.tag_filter_var = tk.StringVar()
        self.tag_filter_var.trace('w', self.on_tag_filter_change)
        tag_filter_entry = tk.Entry(filter_frame, textvariable=self.tag_filter_var, bg='#3b4252', fg='#d8dee9', width=20)
        tag_filter_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Clear filters button
        clear_btn = tk.Button(filter_frame, text="Clear Filters", command=self.clear_filters, 
                            bg='#4c566a', fg='#d8dee9', relief=tk.FLAT)
        clear_btn.pack(side=tk.RIGHT)
        
        # Games frame
        games_frame = tk.Frame(parent, bg=colors["background"])
        games_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for games list
        columns = ('Favorite', 'Name', 'Type', 'Rating', 'Tags', 'Last Played', 'Path')
        self.games_tree = ttk.Treeview(games_frame, columns=columns, show='headings', height=25)
        
        # Configure Treeview tags for custom styling - single custom color
        self.games_tree.tag_configure('default', foreground=game_list_colors["rating_color"])
        self.games_tree.tag_configure('custom', foreground=game_list_colors["custom_rating_color"])
        
        # Configure columns with sorting
        self.games_tree.heading('Favorite', text='⭐', command=lambda: self.sort_by_column('Favorite'))
        self.games_tree.heading('Name', text='Game Name', command=lambda: self.sort_by_column('Name'))
        self.games_tree.heading('Type', text='Type', command=lambda: self.sort_by_column('Type'))
        self.games_tree.heading('Rating', text='Rating', command=lambda: self.sort_by_column('Rating'))
        self.games_tree.heading('Tags', text='Tags', command=lambda: self.sort_by_column('Tags'))
        self.games_tree.heading('Last Played', text='Last Played', command=lambda: self.sort_by_column('Last Played'))
        self.games_tree.heading('Path', text='Path', command=lambda: self.sort_by_column('Path'))
        
        self.games_tree.column('Favorite', width=50, anchor='center')
        self.games_tree.column('Name', width=300)
        self.games_tree.column('Type', width=80)
        self.games_tree.column('Rating', width=80)
        self.games_tree.column('Tags', width=150)
        self.games_tree.column('Last Played', width=100)
        self.games_tree.column('Path', width=300)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(games_frame, orient=tk.VERTICAL, command=self.games_tree.yview)
        self.games_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.games_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.games_tree.bind('<Double-1>', self.launch_game)
        self.games_tree.bind('<Return>', self.launch_game)
        self.games_tree.bind('<Button-1>', self.on_tree_click)
        self.games_tree.bind('<Button-3>', self.show_context_menu)  # Right-click
        self.games_tree.bind('<<TreeviewSelect>>', self.on_game_select)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(parent, textvariable=self.status_var,
                             font=('Segoe UI', 10), fg='#888888', bg='#1e1e1e',
                             anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(15, 0))
        
    def setup_right_panel(self, parent):
        """Setup the metadata viewer panel."""
        # Title
        title_label = tk.Label(parent, text="[INFO] Game Details", 
                              font=('Segoe UI', 18, 'bold'), 
                              fg='#00d4ff', bg='#1e1e1e')
        title_label.pack(pady=(0, 20))
        
        # Cover art frame
        cover_frame = tk.Frame(parent, bg='#1e1e1e')
        cover_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Cover art label
        self.cover_label = tk.Label(cover_frame, text="No game selected", 
                                   font=('Segoe UI', 12), fg='#cccccc', bg='#1e1e1e',
                                   padx=10, pady=10)
        self.cover_label.pack()
        
        # Metadata frame
        metadata_frame = tk.Frame(parent, bg='#1e1e1e')
        metadata_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable text widget for metadata
        text_frame = tk.Frame(metadata_frame, bg='#1e1e1e')
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.metadata_text = tk.Text(text_frame, 
                                    font=('Segoe UI', 10), 
                                    bg='#2d2d2d', fg='white',
                                    wrap=tk.WORD, state=tk.DISABLED,
                                    height=20)
        
        metadata_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.metadata_text.yview)
        self.metadata_text.configure(yscrollcommand=metadata_scrollbar.set)
        
        self.metadata_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        metadata_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def load_favorites(self):
        """Load favorites from file."""
        try:
            with open('favorites.json', 'r') as f:
                self.favorites = set(json.load(f))
        except FileNotFoundError:
            self.favorites = set()
            
    def save_favorites(self):
        """Save favorites to file."""
        with open('favorites.json', 'w') as f:
            json.dump(list(self.favorites), f)
            
    def load_games(self):
        """Load all games from the configured directories."""
        print("Starting to load games...")
        self.status_var.set("Loading games...")
        self.root.update()
        
        self.games = []
        
        for game_dir in self.game_dirs:
            self.log(f"[FOLDER] Checking directory: {game_dir}")
            print(f"[FOLDER] Checking directory: {game_dir}")
            if os.path.exists(game_dir):
                self.log(f"Directory exists, loading games...")
                print(f"Directory exists, loading games...")
                self.load_games_from_directory(game_dir)
            else:
                self.log(f"[ERROR] Directory does not exist: {game_dir}")
                print(f"[ERROR] Directory does not exist: {game_dir}")
        
        self.log(f"Total games loaded: {len(self.games)}")
        print(f"Total games loaded: {len(self.games)}")
        self.filtered_games = self.games.copy()
        self.update_games_display()
        self.update_stats()
        
        self.status_var.set(f"Loaded {len(self.games)} games")
        self.log(f"Game loading complete")
        print(f"Game loading complete")
        
    def load_games_from_directory(self, directory):
        """Load games from a specific directory."""
        self.log(f"[SEARCH] Scanning directory: {directory}")
        print(f"[SEARCH] Scanning directory: {directory}")
        game_path = Path(directory)
        shortcut_count = 0
        
        for shortcut_file in game_path.glob("*.lnk"):
            try:
                # Get shortcut target
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(str(shortcut_file))
                target_path = shortcut.Targetpath
                
                # Determine game type
                game_type = self.get_game_type(shortcut_file.name, target_path)
                
                # Get game name - use directory name for PC games, .lnk name for others
                if game_type == "PC Game":
                    # For PC games, use the directory name of the target executable
                    target_dir = Path(target_path).parent.name
                    game_name = self.clean_game_name(target_dir)
                else:
                    # For ROMs and other types, use the .lnk filename
                    game_name = self.clean_game_name(shortcut_file.stem)
                
                # Get last played time (file modification time)
                last_played = datetime.fromtimestamp(shortcut_file.stat().st_mtime).strftime("%Y-%m-%d")
                
                # Get rating from database
                rating = self.get_game_rating(game_name)
                tags = self.get_game_tags(game_name)
                
                self.games.append({
                    'name': game_name,
                    'type': game_type,
                    'path': str(shortcut_file),
                    'target': target_path,
                    'directory': directory,
                    'last_played': last_played,
                    'full_name': game_name,  # Use the corrected game name
                    'rating': rating,
                    'tags': tags
                })
                
                shortcut_count += 1
                self.log(f"  Loaded: {game_name} ({game_type}) - Rating: {rating}")
                print(f"  Loaded: {game_name} ({game_type}) - Rating: {rating}")
                
            except Exception as e:
                self.log(f"[ERROR] Error reading shortcut {shortcut_file}: {e}")
                print(f"[ERROR] Error reading shortcut {shortcut_file}: {e}")
        
        self.log(f"Found {shortcut_count} shortcuts in {directory}")
        print(f"Found {shortcut_count} shortcuts in {directory}")
                
    def get_game_tags(self, game_name):
        """Get game tags from database and custom manager."""
        if not self.db_path.exists():
            return []
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Try to find by exact name first
            cursor.execute('SELECT genres FROM games WHERE name = ?', (game_name,))
            result = cursor.fetchone()
            
            if not result:
                # Try to find by original name (before resolution)
                cursor.execute('SELECT name, genres FROM games')
                all_games = cursor.fetchall()
                
                for db_name, genres in all_games:
                    try:
                        from game_name_resolver import GameNameResolver
                        resolver = GameNameResolver()
                        resolved_name = resolver.resolve_game_name(db_name)
                        if resolved_name == game_name:
                            result = (genres,)
                            break
                    except ImportError:
                        pass
            
            conn.close()
            
            downloaded_tags = []
            if result and result[0]:
                # Parse genres from database - handle both JSON and comma-separated formats
                genres_str = result[0]
                try:
                    # Try to parse as JSON first
                    import json
                    downloaded_tags = json.loads(genres_str)
                except (json.JSONDecodeError, TypeError):
                    # Fall back to comma-separated parsing
                    downloaded_tags = [tag.strip() for tag in genres_str.split(',') if tag.strip()]
            
            # Check for custom tags override
            final_tags = self.custom_ratings_manager.get_final_tags(game_name, downloaded_tags)
            return final_tags
        except:
            return []
    
    def get_game_rating(self, game_name):
        if not self.db_path.exists():
            return None
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Try to find by exact name first
            cursor.execute('SELECT rating FROM games WHERE name = ?', (game_name,))
            result = cursor.fetchone()
            
            if not result:
                # Try to find by original name (before resolution)
                # Look for games that might match when resolved
                cursor.execute('SELECT name, rating FROM games')
                all_games = cursor.fetchall()
                
                for db_name, rating in all_games:
                    try:
                        from game_name_resolver import GameNameResolver
                        resolver = GameNameResolver()
                        resolved_name = resolver.resolve_game_name(db_name)
                        if resolved_name == game_name:
                            result = (rating,)
                            break
                    except ImportError:
                        pass
            
            conn.close()
            
            downloaded_rating = result[0] if result else None
            
            # Check for custom rating override
            final_rating = self.custom_ratings_manager.get_final_rating(game_name, downloaded_rating)
            return final_rating
        except:
            return None
            
    def get_game_type(self, shortcut_name, target_path):
        """Determine the type of game based on shortcut name and target."""
        name_lower = shortcut_name.lower()
        target_lower = target_path.lower()
        
        if 'launch ' in name_lower:
            return "DOSBox"
        elif '(modengine)' in name_lower or '(mod -' in name_lower:
            return "Mod"
        elif '(protected)' in name_lower:
            return "Protected"
        elif '(mcc launcher)' in name_lower:
            return "MCC"
        elif '(startup)' in name_lower:
            return "Startup"
        elif '(pre-launcher)' in name_lower:
            return "Pre-Launcher"
        elif any(console in name_lower for console in ['ps2', 'psx', 'n64', 'gamecube', 'wii', 'dreamcast', 'genesis', 'snes', 'nes', 'gba', 'nds', 'psp', 'mame', 'c64', 'amiga', 'atari']):
            return "ROM"
        elif target_lower.endswith('.bat'):
            return "Batch"
        else:
            return "PC Game"
            
    def clean_game_name(self, name):
        """Clean up game name for display using the game name resolver."""
        try:
            from game_name_resolver import GameNameResolver
            resolver = GameNameResolver()
            return resolver.resolve_game_name(name)
        except ImportError:
            # Fallback to original method if resolver not available
            return self._clean_game_name_fallback(name)
            
    def _clean_game_name_fallback(self, name):
        """Fallback game name cleaning method."""
        # Remove common suffixes and clean up
        suffixes_to_remove = [
            ' (ModEngine)', ' (Protected)', ' (MCC Launcher)', ' (Startup)', ' (Pre-Launcher)',
            ' (Mod - Armoredcore6)', ' (Mod - Darksouls3)', ' (Mod - Eldenring)',
            ' (PS2)', ' (PSX)', ' (N64)', ' (GameCube)', ' (Wii)', ' (Dreamcast)',
            ' (Genesis)', ' (SNES)', ' (NES)', ' (GBA)', ' (NDS)', ' (PSP)',
            ' (MAME)', ' (C64)', ' (Amiga)', ' (Atari2600)',
            'Launch ', ' - ', ':', ';', '!', '?'
        ]

        cleaned_name = name
        for suffix in suffixes_to_remove:
            cleaned_name = cleaned_name.replace(suffix, ' ')

        # Clean up extra spaces and common prefixes
        cleaned_name = cleaned_name.replace('Launch ', '').strip()
        cleaned_name = ' '.join(cleaned_name.split())  # Remove extra spaces

        return cleaned_name.strip()
        
    def filter_games(self, *args):
        """Filter games based on search term and filter."""
        search_term = self.search_var.get().lower()
        filter_type = self.filter_var.get()
        
        filtered = self.games.copy()
        
        # Apply search filter
        if search_term:
            filtered = [
                game for game in filtered
                if search_term in game['name'].lower() or 
                   search_term in game['type'].lower()
            ]
            
        # Apply type filter
        if filter_type == "Favorites":
            filtered = [game for game in filtered if game['full_name'] in self.favorites]
        elif filter_type != "All":
            filtered = [game for game in filtered if game['type'] == filter_type]
            
        self.filtered_games = filtered
        
        # Reapply current sorting if any
        if self.sort_column:
            self.sort_by_column(self.sort_column)
        else:
            self.update_games_display()
            
        self.update_stats()
        
    def on_search_change(self, *args):
        """Handle search text changes."""
        self.apply_filters()
    
    def on_tag_filter_change(self, *args):
        """Handle tag filter changes."""
        self.apply_filters()
    
    def clear_filters(self):
        """Clear all filters."""
        self.search_var.set("")
        self.tag_filter_var.set("")
    
    def apply_filters(self):
        """Apply search and tag filters to games."""
        search_text = self.search_var.get().lower()
        tag_filter = self.tag_filter_var.get().lower()
        
        self.filtered_games = []
        
        for game in self.games:
            # Search filter
            if search_text and search_text not in game['name'].lower():
                continue
            
            # Tag filter - more flexible matching
            if tag_filter:
                game_tags = [tag.lower() for tag in game['tags']]
                filter_tags = [tag.strip().lower() for tag in tag_filter.split(',') if tag.strip()]
                
                # Check if any filter tag is contained in any game tag (partial matching)
                tag_match = False
                for filter_tag in filter_tags:
                    for game_tag in game_tags:
                        if filter_tag in game_tag or game_tag in filter_tag:
                            tag_match = True
                            break
                    if tag_match:
                        break
                
                if not tag_match:
                    continue
            
            self.filtered_games.append(game)
        
        self.update_games_display()
        self.update_stats()
    
    def update_games_display(self):
        """Update the games treeview display."""
        # Clear existing items
        for item in self.games_tree.get_children():
            self.games_tree.delete(item)
            
        # Add filtered games
        for game in self.filtered_games:
            favorite_star = "⭐" if game['full_name'] in self.favorites else ""
            
            # Format rating with custom color indication
            has_custom_rating = self.custom_ratings_manager.has_custom_rating(game['name'])
            if has_custom_rating:
                # Use a special character to indicate custom rating
                rating_text = f"★{game['rating']:.1f}" if game['rating'] is not None else "★N/A"
            else:
                rating_text = f"{game['rating']:.1f}" if game['rating'] is not None else "N/A"
            
            # Format tags with custom color indication
            has_custom_tags = self.custom_ratings_manager.has_custom_tags(game['name'])
            if has_custom_tags:
                # Use a special character to indicate custom tags
                tags_text = f"★{', '.join(game['tags'])}" if game['tags'] else "★"
            else:
                tags_text = ", ".join(game['tags']) if game['tags'] else ""
            
            item = self.games_tree.insert('', tk.END, values=(
                favorite_star,
                game['name'],
                game['type'],
                rating_text,
                tags_text,
                game['last_played'],
                game['path']
            ))
            
            # Apply custom styling if any customization exists
            if has_custom_rating or has_custom_tags:
                self.games_tree.item(item, tags=('custom',))
            else:
                self.games_tree.item(item, tags=('default',))
            
    def update_stats(self):
        """Update the statistics display."""
        total_games = len(self.games)
        filtered_games = len(self.filtered_games)
        
        # Count by type
        type_counts = {}
        for game in self.filtered_games:
            game_type = game['type']
            type_counts[game_type] = type_counts.get(game_type, 0) + 1
            
        stats_text = f"Showing {filtered_games} of {total_games} games"
        if type_counts:
            stats_text += " | " + " | ".join([f"{t}: {c}" for t, c in sorted(type_counts.items())])
            
        self.stats_label.config(text=stats_text)
        
    def sort_by_column(self, column):
        """Sort games by the specified column."""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
            
        # Sort the filtered games
        if column == 'Favorite':
            self.filtered_games.sort(key=lambda x: x['full_name'] in self.favorites, reverse=self.sort_reverse)
        elif column == 'Name':
            self.filtered_games.sort(key=lambda x: x['name'].lower(), reverse=self.sort_reverse)
        elif column == 'Type':
            self.filtered_games.sort(key=lambda x: x['type'], reverse=self.sort_reverse)
        elif column == 'Rating':
            self.filtered_games.sort(key=lambda x: x['rating'] or 0, reverse=self.sort_reverse)
        elif column == 'Last Played':
            self.filtered_games.sort(key=lambda x: x['last_played'], reverse=self.sort_reverse)
        elif column == 'Path':
            self.filtered_games.sort(key=lambda x: x['path'], reverse=self.sort_reverse)
            
        # Update the display
        self.update_games_display()
        
        # Update column headers to show sort direction
        self.update_column_headers()
        
    def update_column_headers(self):
        """Update column headers to show sort direction."""
        columns = ['Favorite', 'Name', 'Type', 'Rating', 'Last Played', 'Path']
        headers = ['⭐', 'Game Name', 'Type', 'Rating', 'Last Played', 'Path']
        
        for i, (col, header) in enumerate(zip(columns, headers)):
            if col == self.sort_column:
                if self.sort_reverse:
                    header += ' ↓'
                else:
                    header += ' ↑'
            self.games_tree.heading(col, text=header)
        
    def on_tree_click(self, event):
        """Handle tree click events."""
        item = self.games_tree.identify('item', event.x, event.y)
        column = self.games_tree.identify('column', event.x, event.y)
        
        if item and column == '#1':  # Favorite column
            self.toggle_favorite(item)
        elif item and column == '#4':  # Rating column
            self.edit_rating(item)
        elif item and column == '#5':  # Tags column
            self.edit_tags(item)
    
    def edit_rating(self, item):
        """Edit the rating for a game."""
        # Get game name from the tree item
        values = self.games_tree.item(item, 'values')
        if not values or len(values) < 2:
            return
        
        game_name = values[1]  # Name is in column 1
        current_rating = values[3] if len(values) > 3 else "N/A"  # Rating is in column 3
        
        # Show input dialog
        from tkinter import simpledialog
        new_rating = simpledialog.askfloat(
            "Edit Rating",
            f"Enter new rating for '{game_name}' (0-10):",
            initialvalue=current_rating if current_rating != "N/A" else 7.0,
            minvalue=0.0,
            maxvalue=10.0
        )
        
        if new_rating is not None:
            # Set custom rating
            if self.custom_ratings_manager.set_custom_rating(game_name, new_rating):
                self.log(f"Set custom rating for '{game_name}': {new_rating}")
                print(f"Set custom rating for '{game_name}': {new_rating}")
                
                # Update the rating immediately in the tree view
                self.games_tree.set(item, 'Rating', f"{new_rating:.1f}")
                
                # Update the game data for consistency
                for game in self.games:
                    if game['name'] == game_name:
                        game['rating'] = new_rating
                        break
                
                # Apply custom styling to show it's a custom rating
                self.refresh_games_display()
            else:
                self.log(f"Failed to set rating for '{game_name}'")
                print(f"Failed to set rating for '{game_name}'")
    
    def edit_tags(self, item):
        """Edit the tags for a game."""
        # Get game name from the tree item
        values = self.games_tree.item(item, 'values')
        if not values or len(values) < 2:
            return
        
        game_name = values[1]  # Name is in column 1
        current_tags = values[4] if len(values) > 4 else ""  # Tags is in column 4
        
        # Show input dialog
        from tkinter import simpledialog
        new_tags = simpledialog.askstring(
            "Edit Tags",
            f"Enter tags for '{game_name}' (comma-separated):",
            initialvalue=current_tags
        )
        
        if new_tags is not None:
            # Set custom tags
            if self.custom_ratings_manager.set_custom_tags(game_name, new_tags):
                self.log(f"Set custom tags for '{game_name}': {new_tags}")
                print(f"Set custom tags for '{game_name}': {new_tags}")
                
                # Update the tags immediately in the tree view
                self.games_tree.set(item, 'Tags', new_tags)
                
                # Update the game data for consistency
                for game in self.games:
                    if game['name'] == game_name:
                        game['tags'] = self.custom_ratings_manager.get_final_tags(game_name, game['tags'])
                        break
                
                # Apply custom styling to show it's custom tags
                self.refresh_games_display()
            else:
                self.log(f"Failed to set tags for '{game_name}'")
                print(f"Failed to set tags for '{game_name}'")
    
    def refresh_games_display(self):
        """Refresh the games display to show updated ratings."""
        # Clear current display
        for item in self.games_tree.get_children():
            self.games_tree.delete(item)
        
        # Re-populate with updated ratings
        for game in self.filtered_games:
            favorite_star = "⭐" if game['full_name'] in self.favorites else ""
            
            # Format rating with custom color indication
            has_custom_rating = self.custom_ratings_manager.has_custom_rating(game['name'])
            if has_custom_rating:
                # Use a special character to indicate custom rating
                rating_text = f"★{game['rating']:.1f}" if game['rating'] is not None else "★N/A"
            else:
                rating_text = f"{game['rating']:.1f}" if game['rating'] is not None else "N/A"
            
            # Format tags with custom color indication
            has_custom_tags = self.custom_ratings_manager.has_custom_tags(game['name'])
            if has_custom_tags:
                # Use a special character to indicate custom tags
                tags_text = f"★{', '.join(game['tags'])}" if game['tags'] else "★"
            else:
                tags_text = ", ".join(game['tags']) if game['tags'] else ""
            
            item = self.games_tree.insert('', tk.END, values=(
                favorite_star,
                game['name'],
                game['type'],
                rating_text,
                tags_text,
                game['last_played'],
                game['path']
            ))
            
            # Apply custom styling if any customization exists
            if has_custom_rating or has_custom_tags:
                self.games_tree.item(item, tags=('custom',))
            else:
                self.games_tree.item(item, tags=('default',))
    
            
    def on_game_select(self, event):
        """Handle game selection."""
        self.log("Game selection event triggered")
        print("Game selection event triggered")
        selection = self.games_tree.selection()
        if not selection:
            self.log("[ERROR] No selection")
            print("[ERROR] No selection")
            return
            
        item = self.games_tree.item(selection[0])
        game_name = item['values'][1]  # Name column
        self.log(f"Selected game: {game_name}")
        print(f"Selected game: {game_name}")
        
        # Find the game
        game = None
        for g in self.filtered_games:
            if g['name'] == game_name:
                game = g
                break
                
        if game:
            print(f"Game found: {game}")
            self.selected_game = game
            self.display_game_metadata(game)
        else:
            print(f"[ERROR] Could not find game: {game_name}")
            
    def display_game_metadata(self, game):
        """Display metadata for the selected game."""
        self.log(f"Displaying metadata for: {game['name']}")
        print(f"Displaying metadata for: {game['name']}")
        # Load metadata from database
        metadata = self.get_game_metadata_from_db(game['name'])
        self.log(f"Metadata loaded: {metadata is not None}")
        print(f"Metadata loaded: {metadata}")
        
        # Display cover art
        self.log("Displaying cover art...")
        print("Displaying cover art...")
        self.display_cover_art(game['name'], metadata)
        
        # Display metadata text
        self.log("Displaying metadata text...")
        print("Displaying metadata text...")
        self.display_metadata_text(game, metadata)
        self.log("Metadata display complete")
        print("Metadata display complete")
        
    def add_gradient_overlay(self, image):
        """Add a gradient overlay to fade the bottom 1/4 of the image."""
        try:
            from PIL import Image, ImageDraw
            
            # Convert to RGBA if not already
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Create gradient overlay
            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Calculate gradient area (bottom 1/4 of image)
            width, height = image.size
            gradient_start = int(height * 0.75)  # Start gradient at 3/4 down
            
            # Create gradient from transparent to semi-transparent
            for y in range(gradient_start, height):
                # Calculate alpha value (0 to 128)
                alpha = int(128 * (y - gradient_start) / (height - gradient_start))
                # Draw horizontal line with calculated alpha
                draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
            
            # Composite the gradient onto the image
            image = Image.alpha_composite(image, overlay)
            
            # Convert back to RGB for Tkinter compatibility
            return image.convert('RGB')
            
        except Exception as e:
            print(f"Error adding gradient overlay: {e}")
            return image
        
    def get_game_metadata_from_db(self, game_name):
        """Get game metadata from database."""
        if not self.db_path.exists():
            return None
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Try to find by exact name first
            cursor.execute('SELECT * FROM games WHERE name = ?', (game_name,))
            row = cursor.fetchone()
            
            if not row:
                # Try to find by original name (before resolution)
                # Look for games that might match when resolved
                cursor.execute('SELECT * FROM games')
                all_games = cursor.fetchall()
                
                for game_row in all_games:
                    original_name = game_row[1]  # name column
                    try:
                        from game_name_resolver import GameNameResolver
                        resolver = GameNameResolver()
                        resolved_name = resolver.resolve_game_name(original_name)
                        if resolved_name == game_name:
                            row = game_row
                            print(f"[SEARCH] Found metadata for '{game_name}' using original name '{original_name}'")
                            break
                    except ImportError:
                        pass
            
            conn.close()
            
            if row:
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
        except:
            pass
            
        return None
        
    def display_cover_art(self, game_name, metadata):
        """Display cover art for the game."""
        cover_path = None
        
        if metadata and metadata.get('cover_path'):
            cover_path = Path(metadata['cover_path'])
            if cover_path.exists():
                try:
                    # Load image and resize maintaining aspect ratio
                    image = Image.open(cover_path)
                    
                    # Calculate new size maintaining aspect ratio, max height 250px
                    original_width, original_height = image.size
                    aspect_ratio = original_width / original_height
                    new_height = 250
                    new_width = int(new_height * aspect_ratio)
                    
                    image = image.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Add opacity gradient overlay
                    image = self.add_gradient_overlay(image)
                    
                    photo = ImageTk.PhotoImage(image)
                    
                    self.cover_label.config(image=photo, text="")
                    self.cover_label.image = photo  # Keep a reference
                    return
                except Exception as e:
                    print(f"Error loading cover art: {e}")
        
        # Check for placeholder cover using original game name
        safe_name = self.safe_filename(game_name)
        placeholder_path = Path("covers") / f"{safe_name}_placeholder.jpg"
        if placeholder_path.exists():
            try:
                image = Image.open(placeholder_path)
                
                # Calculate new size maintaining aspect ratio, max height 250px
                original_width, original_height = image.size
                aspect_ratio = original_width / original_height
                new_height = 250
                new_width = int(new_height * aspect_ratio)
                
                image = image.resize((new_width, new_height), Image.LANCZOS)
                
                # Add opacity gradient overlay
                image = self.add_gradient_overlay(image)
                
                photo = ImageTk.PhotoImage(image)
                
                self.cover_label.config(image=photo, text="")
                self.cover_label.image = photo
                return
            except Exception as e:
                print(f"Error loading placeholder: {e}")
        
        # No cover art available
        clean_name = self.clean_game_name(game_name)
        self.cover_label.config(image="", text=f"No cover art\nfor {clean_name}")
        
    def safe_filename(self, filename):
        """Create a safe filename from game name."""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Convert spaces to underscores to match database entries
        filename = filename.replace(' ', '_')
            
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
            
        return filename
        
    def display_metadata_text(self, game, metadata):
        """Display metadata text for the game."""
        self.metadata_text.config(state=tk.NORMAL)
        self.metadata_text.delete(1.0, tk.END)
        
        # Get cleaned game name
        clean_name = self.clean_game_name(game['name'])
        
        # Format metadata
        text = f"[GAME] {clean_name}\n"
        text += "=" * 50 + "\n\n"
        
        # Game type and path info
        text += f"[TARGET] Type: {game['type']}\n"
        text += f"📁 Path: {game['path']}\n"
        text += f"📅 Last Played: {game['last_played']}\n\n"
        
        if metadata and metadata.get('cover_url'):
            # Show better summary
            summary = metadata['summary']
            if summary and "No detailed information available" in summary:
                text += f"📝 Description:\n"
                text += f"This is {clean_name}, a {game['type'].lower()}.\n\n"
                text += f"💡 Tip: Configure IGDB API credentials to get detailed game information, ratings, and real cover art.\n\n"
            elif summary:
                text += f"📝 Description:\n{summary}\n\n"
            else:
                text += f"📝 Description:\n"
                text += f"This is {clean_name}, a {game['type'].lower()}.\n\n"
                text += f"💡 Tip: Configure IGDB API credentials to get detailed game information, ratings, and real cover art.\n\n"
        else:
            text += f"📝 Description:\n"
            text += f"This is {clean_name}, a {game['type'].lower()}.\n\n"
            text += f"💡 Tip: Configure IGDB API credentials to get detailed game information, ratings, and real cover art.\n\n"
        
        # Show available metadata
        if metadata:
            if metadata.get('rating'):
                text += f"⭐ IGDB Rating: {metadata['rating']:.1f}/100"
                if metadata.get('rating_count'):
                    text += f" ({metadata['rating_count']} votes)\n"
                else:
                    text += "\n"
                    
            if metadata.get('genres') and metadata['genres']:
                text += f"[TAG] Genres: {', '.join(metadata['genres'])}\n"
                
            if metadata.get('platforms') and metadata['platforms']:
                text += f"[PC] Platforms: {', '.join(metadata['platforms'])}\n"
                
            if metadata.get('developer') and metadata['developer']:
                text += f"👨‍💻 Developer: {', '.join(metadata['developer'])}\n"
                
            if metadata.get('publisher') and metadata['publisher']:
                text += f"🏢 Publisher: {', '.join(metadata['publisher'])}\n"
                
            if metadata.get('release_date'):
                try:
                    release_date = datetime.fromtimestamp(metadata['release_date']).strftime("%Y-%m-%d")
                    text += f"📅 Release Date: {release_date}\n"
                except:
                    pass
                    
            if metadata.get('steam_id'):
                text += f"\n🔗 Steam ID: {metadata['steam_id']}\n"
        
        # Add action buttons info
        text += f"\n[GAME] Actions:\n"
        text += f"• Double-click to launch game\n"
        text += f"• Right-click for context menu (Launch, Trailer, Uninstall)\n"
        text += f"• Click star to add to favorites\n"
            
        self.metadata_text.insert(tk.END, text)
        self.metadata_text.config(state=tk.DISABLED)
        
    def toggle_favorite(self, item):
        """Toggle favorite status of a game."""
        values = self.games_tree.item(item)['values']
        game_name = values[1]  # Name column
        
        # Find the game
        game = None
        for g in self.filtered_games:
            if g['name'] == game_name:
                game = g
                break
                
        if game:
            if game['full_name'] in self.favorites:
                self.favorites.remove(game['full_name'])
            else:
                self.favorites.add(game['full_name'])
                
            self.save_favorites()
            self.update_games_display()
            
    def download_metadata(self):
        """Download metadata for all games."""
        if not self.games:
            messagebox.showwarning("Warning", "No games loaded!")
            return
            
        self.log("🚀 Starting metadata download for all games...")
        self.status_var.set("Downloading metadata...")
        
        # Run in background thread
        thread = threading.Thread(target=self._download_metadata_thread)
        thread.daemon = True
        thread.start()
        
    def _download_metadata_thread(self):
        """Background thread for downloading metadata."""
        try:
            from game_name_resolver import GameNameResolver
            
            self.log("Initializing metadata downloader...")
            downloader = GameMetadataDownloader()
            game_names = [game['name'] for game in self.games]
            
            self.log(f"Downloading metadata for {len(game_names)} games...")
            self.status_var.set("Downloading metadata...")
            
            # Define progress callback
            def progress_callback(message, current, total):
                self.log(f"[{current}/{total}] {message}")
                self.status_var.set(f"Downloading metadata... {current}/{total}")
            
            results = downloader.batch_download_metadata(game_names, progress_callback)
            successful_downloads = len([r for r in results if r])
            
            self.log(f"Downloaded metadata for {successful_downloads}/{len(game_names)} games")
            self.status_var.set(f"Downloaded metadata for {successful_downloads} games")
            
            # Refresh the display
            self.log("Refreshing game display...")
            self.load_games()
            
        except Exception as e:
            self.log(f"[ERROR] Error downloading metadata: {e}")
            self.status_var.set(f"Error downloading metadata: {e}")
            
    def launch_game(self, event=None):
        """Launch the selected game."""
        selection = self.games_tree.selection()
        if not selection:
            return
            
        item = self.games_tree.item(selection[0])
        game_name = item['values'][1]  # Name column
        
        # Find the game
        game = None
        for g in self.filtered_games:
            if g['name'] == game_name:
                game = g
                break
                
        if not game:
            messagebox.showerror("Error", "Game not found!")
            return
            
        try:
            self.log(f"🚀 Launching game: {game['name']}")
            self.status_var.set(f"Launching {game['name']}...")
            self.root.update()
            
            # Launch the shortcut
            subprocess.Popen([game['path']], shell=True)
            
            self.log(f"Launched: {game['name']}")
            self.status_var.set(f"Launched {game['name']}")
            
        except Exception as e:
            self.log(f"[ERROR] Failed to launch {game['name']}: {e}")
            messagebox.showerror("Error", f"Failed to launch {game['name']}: {e}")
            self.status_var.set("Launch failed")
            
    def show_context_menu(self, event):
        """Show right-click context menu."""
        # Select the item under the cursor
        item = self.games_tree.identify('item', event.x, event.y)
        if item:
            self.games_tree.selection_set(item)
            
            # Get the selected game
            values = self.games_tree.item(item)['values']
            game_name = values[1]  # Name column
            
            # Find the game
            game = None
            for g in self.filtered_games:
                if g['name'] == game_name:
                    game = g
                    break
                    
            if game:
                self.create_context_menu(event, game)
                
    def create_context_menu(self, event, game):
        """Create and show context menu for the selected game."""
        context_menu = tk.Menu(self.root, tearoff=0, bg='#2d2d2d', fg='white', 
                              activebackground='#0078d4', activeforeground='white')
        
        # Launch game
        context_menu.add_command(label="🚀 Launch Game", 
                                command=lambda: self.launch_game_from_context(game))
        
        # Look up trailer
        context_menu.add_command(label="🎬 Look Up Trailer", 
                                command=lambda: self.lookup_trailer(game))
        
        # Add separator
        context_menu.add_separator()
        
        # Uninstall (only for PC games)
        if game['type'] == 'PC Game':
            context_menu.add_command(label="[DELETE] Uninstall Game", 
                                    command=lambda: self.uninstall_game(game))
        
        # Show menu at cursor position
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def launch_game_from_context(self, game):
        """Launch game from context menu."""
        try:
            self.log(f"🚀 Launching game: {game['name']}")
            self.status_var.set(f"Launching {game['name']}...")
            self.root.update()
            
            # Launch the shortcut
            subprocess.Popen([game['path']], shell=True)
            
            self.log(f"Launched: {game['name']}")
            self.status_var.set(f"Launched {game['name']}")
            
        except Exception as e:
            self.log(f"[ERROR] Failed to launch {game['name']}: {e}")
            messagebox.showerror("Error", f"Failed to launch {game['name']}: {e}")
            self.status_var.set("Launch failed")
            
    def lookup_trailer(self, game):
        """Look up game trailer on YouTube."""
        try:
            # Clean game name for YouTube search
            search_query = f"{game['name']} trailer"
            
            # URL encode the search query
            import urllib.parse
            encoded_query = urllib.parse.quote(search_query)
            
            # Open YouTube search in default browser
            youtube_url = f"https://www.youtube.com/results?search_query={encoded_query}"
            
            import webbrowser
            webbrowser.open(youtube_url)
            
            self.status_var.set(f"Opened YouTube search for {game['name']}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open YouTube: {e}")
            
    def uninstall_game(self, game):
        """Uninstall a PC game by deleting its directory."""
        if game['type'] != 'PC Game':
            messagebox.showwarning("Warning", "Only PC games can be uninstalled through this launcher.")
            return
            
        # Confirm uninstall
        result = messagebox.askyesno(
            "Confirm Uninstall", 
            f"Are you sure you want to uninstall '{game['name']}'?\n\n"
            f"This will delete the game directory and all its files.\n"
            f"This action cannot be undone.",
            icon='warning'
        )
        
        if not result:
            return
            
        try:
            # Find the game directory
            game_dir = self.find_game_directory(game)
            
            if not game_dir:
                messagebox.showerror("Error", "Could not find game directory.")
                return
                
            # Double-check with user
            result2 = messagebox.askyesno(
                "Final Confirmation",
                f"Delete directory: {game_dir}\n\n"
                f"Are you absolutely sure?",
                icon='error'
            )
            
            if not result2:
                return
                
            # Delete the directory
            import shutil
            shutil.rmtree(game_dir)
            
            # Remove the shortcut
            shortcut_path = Path(game['path'])
            if shortcut_path.exists():
                shortcut_path.unlink()
                
            # Refresh the game list
            self.load_games()
            
            self.status_var.set(f"Uninstalled {game['name']}")
            messagebox.showinfo("Success", f"Successfully uninstalled {game['name']}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to uninstall {game['name']}: {e}")
            
    def find_game_directory(self, game):
        """Find the game directory for uninstalling."""
        try:
            # Get shortcut target
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(game['path'])
            target_path = Path(shortcut.Targetpath)
            
            # For most games, the directory is the parent of the executable
            game_dir = target_path.parent
            
            # Check if this looks like a game directory
            if self.is_game_directory(game_dir):
                return game_dir
                
            # Try going up one more level for some games
            parent_dir = game_dir.parent
            if self.is_game_directory(parent_dir):
                return parent_dir
                
            # If we can't find a clear game directory, return the executable's directory
            return game_dir
            
        except Exception as e:
            print(f"Error finding game directory: {e}")
            return None
            
    def is_game_directory(self, directory):
        """Check if a directory looks like a game directory."""
        try:
            dir_path = Path(directory)
            
            # Check for common game files
            game_indicators = [
                '*.exe', '*.dll', 'data', 'assets', 'content', 'bin', 'game',
                '*.pak', '*.vpk', '*.bik', '*.wad', '*.dat'
            ]
            
            file_count = 0
            for pattern in game_indicators:
                files = list(dir_path.glob(pattern))
                file_count += len(files)
                
            # If we find several game-related files, it's likely a game directory
            return file_count > 3
            
        except:
            return False


def main():
    root = tk.Tk()
    app = EnhancedGameLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
