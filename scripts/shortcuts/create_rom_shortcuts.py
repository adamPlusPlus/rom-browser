#!/usr/bin/env python3
"""
ROM Shortcut Creator
Creates shortcuts for ROM files that launch directly through their associated emulators.
"""

import os
import sys
import argparse
from pathlib import Path
import win32com.client


def read_rom_config(config_file):
    """Read ROM directories and emulator mappings from configuration file."""
    rom_mappings = {}
    output_dir = r"E:\Desktop\ROMs"  # Default output directory
    
    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found.")
        return rom_mappings, output_dir
    
    with open(config_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Handle output directory setting
            if line.startswith('OUTPUT_DIR = '):
                output_dir = line.split('=', 1)[1].strip()
                continue
            
            # Handle ROM directory = emulator mapping
            if ' = ' in line:
                rom_dir, emulator_path = line.split(' = ', 1)
                rom_dir = rom_dir.strip()
                emulator_path = emulator_path.strip()
                
                if os.path.exists(rom_dir) and os.path.exists(emulator_path):
                    rom_mappings[rom_dir] = emulator_path
                else:
                    if not os.path.exists(rom_dir):
                        print(f"Warning: ROM directory '{rom_dir}' (line {line_num}) does not exist. Skipping.")
                    if not os.path.exists(emulator_path):
                        print(f"Warning: Emulator path '{emulator_path}' (line {line_num}) does not exist. Skipping.")
    
    return rom_mappings, output_dir


def find_rom_files(rom_dir):
    """Find all ROM files in the specified directory."""
    rom_extensions = {
        '.iso', '.bin', '.cue', '.img', '.mdf', '.mds',  # CD/DVD images
        '.rom', '.nes', '.smc', '.sfc', '.gb', '.gbc', '.gba',  # Cartridge ROMs
        '.nds', '.3ds', '.cia', '.cci',  # Nintendo handheld
        '.psp', '.cso', '.pbp',  # PSP
        '.v64', '.z64', '.n64',  # N64
        '.gcm', '.gcz', '.wbfs', '.wad',  # GameCube/Wii
        '.chd', '.gdi', '.cdi',  # Dreamcast
        '.smd', '.gen', '.md',  # Genesis
        '.zip', '.7z', '.rar',  # Compressed ROMs
        '.d64', '.t64', '.tap',  # Commodore 64
        '.adf', '.ipf', '.hdf',  # Amiga
        '.a26', '.bin',  # Atari 2600
    }
    
    rom_files = []
    rom_path = Path(rom_dir)
    
    if not rom_path.exists():
        return rom_files
    
    for root, dirs, files in os.walk(rom_path):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in rom_extensions:
                rom_files.append(file_path)
    
    return rom_files


def get_emulator_args(emulator_path, rom_file):
    """Get command line arguments for different emulators."""
    emulator_name = Path(emulator_path).name.lower()
    
    if 'pcsx2' in emulator_name:
        return f'"{emulator_path}" --fullscreen --nogui "{rom_file}"'
    elif 'epsxe' in emulator_name:
        return f'"{emulator_path}" -nogui -loadbin "{rom_file}"'
    elif 'project64' in emulator_name:
        return f'"{emulator_path}" "{rom_file}"'
    elif 'dolphin' in emulator_name:
        return f'"{emulator_path}" -e "{rom_file}"'
    elif 'flycast' in emulator_name:
        return f'"{emulator_path}" "{rom_file}"'
    elif 'fusion' in emulator_name:
        return f'"{emulator_path}" "{rom_file}"'
    elif 'snes9x' in emulator_name:
        return f'"{emulator_path}" "{rom_file}"'
    elif 'nestopia' in emulator_name:
        return f'"{emulator_path}" "{rom_file}"'
    elif 'visualboyadvance' in emulator_name:
        return f'"{emulator_path}" "{rom_file}"'
    elif 'desmume' in emulator_name:
        return f'"{emulator_path}" "{rom_file}"'
    elif 'ppsspp' in emulator_name:
        return f'"{emulator_path}" "{rom_file}"'
    elif 'mame' in emulator_name:
        # For MAME, we need to extract the ROM name from the file
        rom_name = rom_file.stem
        return f'"{emulator_path}" "{rom_name}"'
    elif 'x64' in emulator_name:  # VICE C64 emulator
        return f'"{emulator_path}" "{rom_file}"'
    elif 'winuae' in emulator_name:
        return f'"{emulator_path}" -f "{rom_file}"'
    elif 'stella' in emulator_name:
        return f'"{emulator_path}" "{rom_file}"'
    else:
        # Default: just pass the ROM file as argument
        return f'"{emulator_path}" "{rom_file}"'


def create_rom_shortcut(emulator_path, rom_file, shortcut_path):
    """Create a Windows shortcut that launches a ROM through its emulator."""
    try:
        # Create a batch file that launches the emulator with the ROM
        batch_content = f'@echo off\n{get_emulator_args(emulator_path, rom_file)}\n'
        
        # Create the batch file
        batch_file = shortcut_path.with_suffix('.bat')
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # Create shortcut to the batch file
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.Targetpath = str(batch_file)
        shortcut.WorkingDirectory = str(rom_file.parent)
        shortcut.Description = f"Launch {rom_file.name} via {Path(emulator_path).name}"
        shortcut.save()
        
        return True
    except Exception as e:
        print(f"Error creating shortcut for {rom_file.name}: {e}")
        return False


def get_rom_shortcut_name(rom_file, rom_dir):
    """Generate a better name for the ROM shortcut."""
    # Get the console/system name from the ROM directory
    system_name = Path(rom_dir).name
    
    # Clean up the ROM filename
    rom_name = rom_file.stem
    
    # Remove common prefixes/suffixes
    rom_name = rom_name.replace('(USA)', '').replace('(EUR)', '').replace('(JPN)', '')
    rom_name = rom_name.replace('[USA]', '').replace('[EUR]', '').replace('[JPN]', '')
    rom_name = rom_name.strip()
    
    return f"{rom_name} ({system_name})"


def main():
    parser = argparse.ArgumentParser(description='Create shortcuts for ROM files using emulators')
    parser.add_argument('--config', '-c', default='rom_directories.conf',
                       help='Configuration file path (default: rom_directories.conf)')
    parser.add_argument('--clean', action='store_true',
                       help='Clean old shortcuts that no longer point to existing ROMs')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Show what would be created without actually creating shortcuts')
    
    args = parser.parse_args()
    
    print("ROM Shortcut Creator")
    print("=" * 50)
    print(f"Configuration file: {args.config}")
    if args.dry_run:
        print("DRY RUN MODE - No shortcuts will be created")
    print()
    
    # Read configuration
    rom_mappings, output_dir = read_rom_config(args.config)
    
    if not rom_mappings:
        print("No valid ROM directory mappings found in configuration file.")
        return 1
    
    print(f"Found {len(rom_mappings)} ROM directory mappings:")
    for rom_dir, emulator_path in rom_mappings.items():
        print(f"  {rom_dir} -> {emulator_path}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    if not args.dry_run:
        output_path.mkdir(parents=True, exist_ok=True)
        print(f"Created output directory: {output_path}")
    
    # Find all ROM files from all directories
    all_roms = []
    empty_directories = []
    
    for rom_dir, emulator_path in rom_mappings.items():
        print(f"Scanning: {rom_dir}")
        rom_files = find_rom_files(rom_dir)
        if rom_files:
            all_roms.extend([(rom_file, emulator_path) for rom_file in rom_files])
            print(f"  Found {len(rom_files)} ROM files")
        else:
            empty_directories.append(rom_dir)
            print(f"  No ROM files found")
    
    # Report empty directories
    if empty_directories:
        print(f"\nDirectories with no ROM files found:")
        for directory in empty_directories:
            print(f"  {directory}")
        print()
    
    if not all_roms:
        print("No ROM files found in any directory.")
        return 0
    
    print(f"Total ROM files found: {len(all_roms)}")
    
    if args.dry_run:
        print("\nShortcuts that would be created:")
        for rom_file, emulator_path in all_roms:
            shortcut_name = get_rom_shortcut_name(rom_file, rom_file.parent) + ".lnk"
            print(f"  {shortcut_name} -> {rom_file} (via {Path(emulator_path).name})")
        return 0
    
    print("\nCreating shortcuts...")
    
    # Create shortcuts
    successful_shortcuts = 0
    skipped_shortcuts = 0
    failed_shortcuts = 0
    
    for rom_file, emulator_path in all_roms:
        # Create shortcut name
        shortcut_name = get_rom_shortcut_name(rom_file, rom_file.parent) + ".lnk"
        shortcut_path = output_path / shortcut_name
        
        # Skip if shortcut already exists
        if shortcut_path.exists():
            print(f"Shortcut already exists: {shortcut_name}")
            skipped_shortcuts += 1
            continue
        
        if create_rom_shortcut(emulator_path, rom_file, shortcut_path):
            print(f"Created: {shortcut_name}")
            successful_shortcuts += 1
        else:
            print(f"Failed: {shortcut_name}")
            failed_shortcuts += 1
    
    print(f"\nSummary:")
    print(f"Total ROM files found: {len(all_roms)}")
    print(f"Shortcuts created successfully: {successful_shortcuts}")
    print(f"Shortcuts skipped (already exist): {skipped_shortcuts}")
    print(f"Shortcuts failed: {failed_shortcuts}")
    print(f"Shortcuts location: {output_path}")
    
    return 0 if failed_shortcuts == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
