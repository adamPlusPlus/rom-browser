#!/usr/bin/env python3
"""
Game Collection Launcher - Enhanced Version
A modern GUI application with better visuals and features.
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import threading
import json
from datetime import datetime
import win32com.client


class ModernGameLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Collection Launcher")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e1e')
        
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
        
        # Load favorites
        self.load_favorites()
        
        # GUI elements
        self.setup_ui()
        self.load_games()
        
    def setup_ui(self):
        """Setup the modern user interface."""
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Treeview', background='#2d2d2d', foreground='white', fieldbackground='#2d2d2d')
        style.configure('Treeview.Heading', background='#404040', foreground='white')
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header frame
        header_frame = tk.Frame(main_frame, bg='#1e1e1e')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Title
        title_label = tk.Label(header_frame, text="🎮 Game Collection", 
                              font=('Segoe UI', 28, 'bold'), 
                              fg='#00d4ff', bg='#1e1e1e')
        title_label.pack(side=tk.LEFT)
        
        # Controls frame
        controls_frame = tk.Frame(header_frame, bg='#1e1e1e')
        controls_frame.pack(side=tk.RIGHT)
        
        # Refresh button
        refresh_btn = tk.Button(controls_frame, text="🔄 Refresh", 
                               command=self.load_games,
                               bg='#0078d4', fg='white', font=('Segoe UI', 10),
                               relief=tk.FLAT, padx=15, pady=5)
        refresh_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Settings button
        settings_btn = tk.Button(controls_frame, text="⚙️ Settings", 
                                command=self.open_settings,
                                bg='#6c757d', fg='white', font=('Segoe UI', 10),
                                relief=tk.FLAT, padx=15, pady=5)
        settings_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Search and filter frame
        search_frame = tk.Frame(main_frame, bg='#1e1e1e')
        search_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_games)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=('Segoe UI', 12), width=60,
                               bg='#2d2d2d', fg='white', insertbackground='white',
                               relief=tk.FLAT, bd=5)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Search label
        search_label = tk.Label(search_frame, text="🔍 Search:", 
                               font=('Segoe UI', 12), fg='#ffffff', bg='#1e1e1e')
        search_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Filter buttons
        filter_frame = tk.Frame(search_frame, bg='#1e1e1e')
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
                                bg='#1e1e1e', fg='white', selectcolor='#0078d4',
                                font=('Segoe UI', 10))
            btn.pack(side=tk.LEFT, padx=5)
        
        # Stats frame
        stats_frame = tk.Frame(main_frame, bg='#1e1e1e')
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_label = tk.Label(stats_frame, text="", 
                                    font=('Segoe UI', 11), fg='#cccccc', bg='#1e1e1e')
        self.stats_label.pack()
        
        # Games frame
        games_frame = tk.Frame(main_frame, bg='#1e1e1e')
        games_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for games list
        columns = ('Favorite', 'Name', 'Type', 'Last Played', 'Path')
        self.games_tree = ttk.Treeview(games_frame, columns=columns, show='headings', height=25)
        
        # Configure columns with sorting
        self.games_tree.heading('Favorite', text='⭐', command=lambda: self.sort_by_column('Favorite'))
        self.games_tree.heading('Name', text='Game Name', command=lambda: self.sort_by_column('Name'))
        self.games_tree.heading('Type', text='Type', command=lambda: self.sort_by_column('Type'))
        self.games_tree.heading('Last Played', text='Last Played', command=lambda: self.sort_by_column('Last Played'))
        self.games_tree.heading('Path', text='Path', command=lambda: self.sort_by_column('Path'))
        
        self.games_tree.column('Favorite', width=50, anchor='center')
        self.games_tree.column('Name', width=350)
        self.games_tree.column('Type', width=100)
        self.games_tree.column('Last Played', width=120)
        self.games_tree.column('Path', width=500)
        
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
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(main_frame, textvariable=self.status_var,
                             font=('Segoe UI', 10), fg='#888888', bg='#1e1e1e',
                             anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(15, 0))
        
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
        self.status_var.set("Loading games...")
        self.root.update()
        
        self.games = []
        
        for game_dir in self.game_dirs:
            if os.path.exists(game_dir):
                self.load_games_from_directory(game_dir)
        
        self.filtered_games = self.games.copy()
        self.update_games_display()
        self.update_stats()
        
        self.status_var.set(f"Loaded {len(self.games)} games")
        
    def load_games_from_directory(self, directory):
        """Load games from a specific directory."""
        game_path = Path(directory)
        
        for shortcut_file in game_path.glob("*.lnk"):
            try:
                # Get shortcut target
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(str(shortcut_file))
                target_path = shortcut.Targetpath
                
                # Determine game type
                game_type = self.get_game_type(shortcut_file.name, target_path)
                
                # Clean up game name
                game_name = self.clean_game_name(shortcut_file.stem)
                
                # Get last played time (file modification time)
                last_played = datetime.fromtimestamp(shortcut_file.stat().st_mtime).strftime("%Y-%m-%d")
                
                self.games.append({
                    'name': game_name,
                    'type': game_type,
                    'path': str(shortcut_file),
                    'target': target_path,
                    'directory': directory,
                    'last_played': last_played,
                    'full_name': shortcut_file.stem
                })
                
            except Exception as e:
                print(f"Error reading shortcut {shortcut_file}: {e}")
                
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
        """Clean up game name for display."""
        # Remove common suffixes
        suffixes_to_remove = [
            ' (ModEngine)', ' (Protected)', ' (MCC Launcher)', ' (Startup)', ' (Pre-Launcher)',
            ' (Mod - Armoredcore6)', ' (Mod - Darksouls3)', ' (Mod - Eldenring)',
            ' (PS2)', ' (PSX)', ' (N64)', ' (GameCube)', ' (Wii)', ' (Dreamcast)',
            ' (Genesis)', ' (SNES)', ' (NES)', ' (GBA)', ' (NDS)', ' (PSP)',
            ' (MAME)', ' (C64)', ' (Amiga)', ' (Atari2600)'
        ]
        
        cleaned_name = name
        for suffix in suffixes_to_remove:
            cleaned_name = cleaned_name.replace(suffix, '')
            
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
        
    def update_games_display(self):
        """Update the games treeview display."""
        # Clear existing items
        for item in self.games_tree.get_children():
            self.games_tree.delete(item)
            
        # Add filtered games
        for game in self.filtered_games:
            favorite_star = "⭐" if game['full_name'] in self.favorites else ""
            self.games_tree.insert('', tk.END, values=(
                favorite_star,
                game['name'],
                game['type'],
                game['last_played'],
                game['path']
            ))
            
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
        columns = ['Favorite', 'Name', 'Type', 'Last Played', 'Path']
        headers = ['⭐', 'Game Name', 'Type', 'Last Played', 'Path']
        
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
            
    def launch_game(self, event=None):
        """Launch the selected game."""
        selection = self.games_tree.selection()
        if not selection:
            return
            
        item = self.games_tree.item(selection[0])
        game_name = item['values'][1]  # Name column
        
        # Find the game in our list
        game = None
        for g in self.filtered_games:
            if g['name'] == game_name:
                game = g
                break
                
        if not game:
            messagebox.showerror("Error", "Game not found!")
            return
            
        try:
            self.status_var.set(f"Launching {game['name']}...")
            self.root.update()
            
            # Launch the shortcut
            subprocess.Popen([game['path']], shell=True)
            
            self.status_var.set(f"Launched {game['name']}")
            
        except Exception as e:
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
            context_menu.add_command(label="🗑️ Uninstall Game", 
                                    command=lambda: self.uninstall_game(game))
        
        # Show menu at cursor position
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def launch_game_from_context(self, game):
        """Launch game from context menu."""
        try:
            self.status_var.set(f"Launching {game['name']}...")
            self.root.update()
            
            # Launch the shortcut
            subprocess.Popen([game['path']], shell=True)
            
            self.status_var.set(f"Launched {game['name']}")
            
        except Exception as e:
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
            
    def open_settings(self):
        """Open settings dialog."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        settings_window.configure(bg='#1e1e1e')
        
        # Settings content
        tk.Label(settings_window, text="Game Directories", 
                font=('Segoe UI', 16, 'bold'), fg='white', bg='#1e1e1e').pack(pady=20)
        
        for i, game_dir in enumerate(self.game_dirs):
            frame = tk.Frame(settings_window, bg='#1e1e1e')
            frame.pack(fill=tk.X, padx=20, pady=5)
            
            tk.Label(frame, text=f"Directory {i+1}:", 
                    font=('Segoe UI', 10), fg='white', bg='#1e1e1e').pack(side=tk.LEFT)
            
            tk.Label(frame, text=game_dir, 
                    font=('Segoe UI', 10), fg='#cccccc', bg='#1e1e1e').pack(side=tk.LEFT, padx=(10, 0))


def main():
    root = tk.Tk()
    app = ModernGameLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
