#!/usr/bin/env python3
"""
Application Configuration Manager
Handles loading and applying configuration settings for the game launcher.
"""

import json
import tkinter as tk
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file="app_config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.get_default_config()
        return self.get_default_config()
    
    def get_default_config(self):
        """Get default configuration."""
        return {
            "appearance": {
                "theme": "dark",
                "colors": {
                    "background": "#1e1e1e",
                    "foreground": "#ffffff",
                    "secondary_background": "#2d2d2d",
                    "secondary_foreground": "#cccccc",
                    "accent": "#0078d4",
                    "accent_hover": "#106ebe",
                    "success": "#107c10",
                    "warning": "#ff8c00",
                    "error": "#d13438",
                    "border": "#404040",
                    "selection": "#0078d4",
                    "selection_background": "#1a4a6b"
                },
                "fonts": {
                    "default": {"family": "Segoe UI", "size": 9, "weight": "normal"},
                    "heading": {"family": "Segoe UI", "size": 10, "weight": "bold"},
                    "small": {"family": "Segoe UI", "size": 8, "weight": "normal"},
                    "large": {"family": "Segoe UI", "size": 12, "weight": "normal"}
                },
                "game_list": {
                    "row_height": 20,
                    "alternating_colors": True,
                    "alternating_color": "#252525",
                    "hover_color": "#3a3a3a",
                    "selected_color": "#0078d4",
                    "rating_color": "#b0b0b0",
                    "custom_rating_color": "#ffd700",
                    "favorite_color": "#ffd700"
                }
            },
            "behavior": {
                "auto_refresh_ratings": True,
                "confirm_rating_changes": False,
                "rating_precision": 1,
                "default_rating": 7.0,
                "rating_range": {"min": 0.0, "max": 10.0}
            }
        }
    
    def get_color(self, path):
        """Get a color value from the config."""
        keys = path.split('.')
        value = self.config
        for key in keys:
            value = value.get(key, {})
        return value
    
    def get_font(self, font_type="default"):
        """Get a font configuration."""
        font_config = self.config["appearance"]["fonts"].get(font_type, self.config["appearance"]["fonts"]["default"])
        return (font_config["family"], font_config["size"], font_config["weight"])
    
    def apply_theme(self, root):
        """Apply the theme to the root window."""
        colors = self.config["appearance"]["colors"]
        
        # Configure root window
        root.configure(bg=colors["background"])
        
        # Configure ttk styles
        style = tk.ttk.Style()
        style.theme_use('clam')
        
        # Configure Treeview
        style.configure("Treeview",
                       background=colors["secondary_background"],
                       foreground=colors["foreground"],
                       fieldbackground=colors["secondary_background"],
                       borderwidth=0,
                       font=self.get_font("default"))
        
        style.configure("Treeview.Heading",
                       background=colors["accent"],
                       foreground=colors["foreground"],
                       font=self.get_font("heading"),
                       borderwidth=1)
        
        style.map("Treeview",
                 background=[('selected', colors["selection_background"])],
                 foreground=[('selected', colors["foreground"])])
        
        # Configure buttons
        style.configure("TButton",
                       background=colors["secondary_background"],
                       foreground=colors["foreground"],
                       borderwidth=1,
                       font=self.get_font("default"))
        
        style.map("TButton",
                 background=[('active', colors["accent_hover"]),
                           ('pressed', colors["accent"])])
        
        # Configure entry fields
        style.configure("TEntry",
                       fieldbackground=colors["secondary_background"],
                       foreground=colors["foreground"],
                       borderwidth=1,
                       font=self.get_font("default"))
        
        return style

if __name__ == "__main__":
    # Test the config manager
    config = ConfigManager()
    print("Config loaded successfully")
    print(f"Background color: {config.get_color('appearance.colors.background')}")
    print(f"Default font: {config.get_font('default')}")
    print(f"Rating color: {config.get_color('appearance.game_list.rating_color')}")
