#!/usr/bin/env python3
"""
Custom Ratings and Tags Manager
Handles user-defined ratings and tags that override downloaded data.
"""

import json
from pathlib import Path

class CustomRatingsManager:
    def __init__(self, data_file="custom_ratings.json"):
        self.data_file = Path(data_file)
        self.custom_data = self.load_data()
    
    def load_data(self):
        """Load custom ratings and tags from file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure backward compatibility
                    if isinstance(data, dict) and all(isinstance(v, (int, float)) for v in data.values()):
                        # Old format - convert to new format
                        new_data = {}
                        for game_name, rating in data.items():
                            new_data[game_name] = {"rating": rating, "tags": []}
                        return new_data
                    return data
            except Exception as e:
                print(f"Error loading custom data: {e}")
                return {}
        return {}
    
    def save_data(self):
        """Save custom ratings and tags to file."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving custom data: {e}")
            return False
    
    def set_custom_rating(self, game_name, rating):
        """Set a custom rating for a game."""
        try:
            # Validate rating (0-10)
            rating = float(rating)
            if 0 <= rating <= 10:
                if game_name not in self.custom_data:
                    self.custom_data[game_name] = {"rating": None, "tags": []}
                self.custom_data[game_name]["rating"] = rating
                self.save_data()
                return True
            else:
                print(f"Rating must be between 0 and 10, got {rating}")
                return False
        except ValueError:
            print(f"Invalid rating format: {rating}")
            return False
    
    def get_custom_rating(self, game_name):
        """Get custom rating for a game, or None if not set."""
        if game_name in self.custom_data:
            return self.custom_data[game_name].get("rating")
        return None
    
    def remove_custom_rating(self, game_name):
        """Remove custom rating for a game."""
        if game_name in self.custom_data:
            self.custom_data[game_name]["rating"] = None
            # If no tags either, remove the game entirely
            if not self.custom_data[game_name].get("tags"):
                del self.custom_data[game_name]
            self.save_data()
            return True
        return False
    
    def has_custom_rating(self, game_name):
        """Check if a game has a custom rating."""
        return (game_name in self.custom_data and 
                self.custom_data[game_name].get("rating") is not None)
    
    def get_final_rating(self, game_name, downloaded_rating):
        """Get the final rating (custom if exists, otherwise downloaded)."""
        custom_rating = self.get_custom_rating(game_name)
        if custom_rating is not None:
            return custom_rating
        return downloaded_rating
    
    def set_custom_tags(self, game_name, tags):
        """Set custom tags for a game."""
        if game_name not in self.custom_data:
            self.custom_data[game_name] = {"rating": None, "tags": []}
        
        # Ensure tags is a list
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        elif not isinstance(tags, list):
            tags = []
        
        self.custom_data[game_name]["tags"] = tags
        self.save_data()
        return True
    
    def get_custom_tags(self, game_name):
        """Get custom tags for a game."""
        if game_name in self.custom_data:
            return self.custom_data[game_name].get("tags", [])
        return []
    
    def add_custom_tag(self, game_name, tag):
        """Add a single tag to a game."""
        if game_name not in self.custom_data:
            self.custom_data[game_name] = {"rating": None, "tags": []}
        
        tags = self.custom_data[game_name].get("tags", [])
        if tag not in tags:
            tags.append(tag)
            self.custom_data[game_name]["tags"] = tags
            self.save_data()
        return True
    
    def remove_custom_tag(self, game_name, tag):
        """Remove a single tag from a game."""
        if game_name in self.custom_data:
            tags = self.custom_data[game_name].get("tags", [])
            if tag in tags:
                tags.remove(tag)
                self.custom_data[game_name]["tags"] = tags
                # If no rating and no tags, remove the game entirely
                if not tags and self.custom_data[game_name].get("rating") is None:
                    del self.custom_data[game_name]
                self.save_data()
        return True
    
    def has_custom_tags(self, game_name):
        """Check if a game has custom tags."""
        return (game_name in self.custom_data and 
                bool(self.custom_data[game_name].get("tags")))
    
    def get_final_tags(self, game_name, downloaded_tags):
        """Get the final tags (custom if exists, otherwise downloaded)."""
        custom_tags = self.get_custom_tags(game_name)
        if custom_tags:
            return custom_tags
        return downloaded_tags or []
    
    def get_all_custom_data(self):
        """Get all custom data."""
        return self.custom_data.copy()
    
    def get_all_custom_ratings(self):
        """Get all custom ratings (for backward compatibility)."""
        ratings = {}
        for game_name, data in self.custom_data.items():
            if data.get("rating") is not None:
                ratings[game_name] = data["rating"]
        return ratings
    
    def get_all_custom_tags(self):
        """Get all custom tags."""
        tags = {}
        for game_name, data in self.custom_data.items():
            if data.get("tags"):
                tags[game_name] = data["tags"]
        return tags
    
    def get_all_unique_tags(self):
        """Get all unique tags across all games."""
        all_tags = set()
        for data in self.custom_data.values():
            all_tags.update(data.get("tags", []))
        return sorted(list(all_tags))

if __name__ == "__main__":
    # Test the custom ratings and tags manager
    manager = CustomRatingsManager()
    
    # Test setting a rating
    manager.set_custom_rating("Test Game", 8.5)
    print(f"Custom rating for Test Game: {manager.get_custom_rating('Test Game')}")
    
    # Test setting tags
    manager.set_custom_tags("Test Game", ["RPG", "Fantasy", "Single Player"])
    print(f"Custom tags for Test Game: {manager.get_custom_tags('Test Game')}")
    
    # Test final rating logic
    final_rating = manager.get_final_rating("Test Game", 7.0)
    print(f"Final rating for Test Game: {final_rating}")
    
    # Test final tags logic
    final_tags = manager.get_final_tags("Test Game", ["Action", "Multiplayer"])
    print(f"Final tags for Test Game: {final_tags}")
    
    # Test with no custom data
    final_rating = manager.get_final_rating("Another Game", 6.5)
    final_tags = manager.get_final_tags("Another Game", ["Strategy"])
    print(f"Final rating for Another Game: {final_rating}")
    print(f"Final tags for Another Game: {final_tags}")
    
    # Test unique tags
    manager.set_custom_tags("Game 2", ["RPG", "Sci-Fi"])
    print(f"All unique tags: {manager.get_all_unique_tags()}")
