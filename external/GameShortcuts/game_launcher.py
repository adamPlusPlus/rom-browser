#!/usr/bin/env python3
"""
Game Collection Launcher
A GUI application that displays all generated game shortcuts as a collection.
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import threading
from PIL import Image, ImageTk
import win32com.client


class GameLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Collection Launcher")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')
        
        # Game directories
        self.game_dirs = [
            r"E:\Desktop\Games",
            r"E:\Desktop\ROMs"
        ]
        
        # Current games list
        self.games = []
        self.filtered_games = []
        
        # Sorting state
        self.sort_column = None
        self.sort_reverse = False
        
        # GUI elements
        self.setup_ui()
        self.load_games()
        
    def setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Game Collection", 
                              font=('Arial', 24, 'bold'), 
                              fg='#ffffff', bg='#2b2b2b')
        title_label.pack(pady=(0, 20))
        
        # Search frame
        search_frame = tk.Frame(main_frame, bg='#2b2b2b')
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_games)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=('Arial', 12), width=50)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Search label
        search_label = tk.Label(search_frame, text="Search games:", 
                               font=('Arial', 12), fg='#ffffff', bg='#2b2b2b')
        search_label.pack(side=tk.LEFT)
        
        # Refresh button
        refresh_btn = tk.Button(search_frame, text="Refresh", 
                               command=self.load_games,
                               bg='#4CAF50', fg='white', font=('Arial', 10))
        refresh_btn.pack(side=tk.RIGHT)
        
        # Stats frame
        stats_frame = tk.Frame(main_frame, bg='#2b2b2b')
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_label = tk.Label(stats_frame, text="", 
                                    font=('Arial', 10), fg='#cccccc', bg='#2b2b2b')
        self.stats_label.pack()
        
        # Games frame with scrollbar
        games_frame = tk.Frame(main_frame, bg='#2b2b2b')
        games_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for games list
        columns = ('Name', 'Type', 'Path')
        self.games_tree = ttk.Treeview(games_frame, columns=columns, show='headings', height=20)
        
        # Configure columns with sorting
        self.games_tree.heading('Name', text='Game Name', command=lambda: self.sort_by_column('Name'))
        self.games_tree.heading('Type', text='Type', command=lambda: self.sort_by_column('Type'))
        self.games_tree.heading('Path', text='Path', command=lambda: self.sort_by_column('Path'))
        
        self.games_tree.column('Name', width=400)
        self.games_tree.column('Type', width=100)
        self.games_tree.column('Path', width=600)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(games_frame, orient=tk.VERTICAL, command=self.games_tree.yview)
        self.games_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.games_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to launch game
        self.games_tree.bind('<Double-1>', self.launch_game)
        self.games_tree.bind('<Return>', self.launch_game)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(main_frame, textvariable=self.status_var,
                             font=('Arial', 10), fg='#cccccc', bg='#2b2b2b',
                             anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
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
                
                self.games.append({
                    'name': game_name,
                    'type': game_type,
                    'path': str(shortcut_file),
                    'target': target_path,
                    'directory': directory
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
        """Filter games based on search term."""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            self.filtered_games = self.games.copy()
        else:
            self.filtered_games = [
                game for game in self.games
                if search_term in game['name'].lower() or 
                   search_term in game['type'].lower()
            ]
            
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
            self.games_tree.insert('', tk.END, values=(
                game['name'],
                game['type'],
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
        if column == 'Name':
            self.filtered_games.sort(key=lambda x: x['name'].lower(), reverse=self.sort_reverse)
        elif column == 'Type':
            self.filtered_games.sort(key=lambda x: x['type'], reverse=self.sort_reverse)
        elif column == 'Path':
            self.filtered_games.sort(key=lambda x: x['path'], reverse=self.sort_reverse)
            
        # Update the display
        self.update_games_display()
        
        # Update column headers to show sort direction
        self.update_column_headers()
        
    def update_column_headers(self):
        """Update column headers to show sort direction."""
        columns = ['Name', 'Type', 'Path']
        headers = ['Game Name', 'Type', 'Path']
        
        for i, (col, header) in enumerate(zip(columns, headers)):
            if col == self.sort_column:
                if self.sort_reverse:
                    header += ' ↓'
                else:
                    header += ' ↑'
            self.games_tree.heading(col, text=header)
        
    def launch_game(self, event=None):
        """Launch the selected game."""
        selection = self.games_tree.selection()
        if not selection:
            return
            
        item = self.games_tree.item(selection[0])
        game_name = item['values'][0]
        
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


def main():
    root = tk.Tk()
    app = GameLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
