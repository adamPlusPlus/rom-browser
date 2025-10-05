#!/usr/bin/env python3
"""
Launcher script for the Rust Game Launcher
This script ensures the Rust frontend runs from the correct directory.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    # Change to the Rust project directory
    rust_dir = script_dir / "game_launcher_rust"
    
    if not rust_dir.exists():
        print("Error: Rust project directory not found!")
        print(f"Expected: {rust_dir}")
        return 1
    
    # Change to the Rust directory
    os.chdir(rust_dir)
    
    print("Starting Rust Game Launcher...")
    print(f"Working directory: {os.getcwd()}")
    
    try:
        # Run cargo run
        result = subprocess.run(["cargo", "run"], check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error running cargo: {e}")
        return e.returncode
    except FileNotFoundError:
        print("Error: Rust/Cargo not found!")
        print("Please install Rust from https://rustup.rs/")
        return 1

if __name__ == "__main__":
    sys.exit(main())
