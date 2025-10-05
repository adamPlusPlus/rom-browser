#!/usr/bin/env python3
"""
Script to create shortcuts for all executables in subdirectories of a target directory.
"""

import os
import sys
import argparse
from pathlib import Path
import win32com.client


def find_executables(target_dir, exclude_patterns=None):
    """Find all executable files in subdirectories of the target directory."""
    executables = []
    target_path = Path(target_dir)
    
    if not target_path.exists():
        print(f"Error: Target directory '{target_dir}' does not exist.")
        return executables
    
    if not target_path.is_dir():
        print(f"Error: '{target_dir}' is not a directory.")
        return executables
    
    # Common executable extensions
    exe_extensions = {'.exe', '.bat', '.cmd', '.msi', '.com'}
    
    # Default exclude patterns for common non-game executables
    if exclude_patterns is None:
        exclude_patterns = [
            'unins000.exe',  # Uninstaller
            'unins001.exe',  # Uninstaller
            'unins002.exe',  # Uninstaller
            'UnityCrashHandler',  # Unity crash handlers (any version)
            'dxwebsetup.exe',  # DirectX installer
            'QuickSFV.EXE',  # File verification tool
            'CrashReportClient.exe',  # Crash reporting
            'EpicWebHelper.exe',  # Epic launcher helper
            'createdump.exe',  # Debug dump tool
            'msiexec.exe',  # Windows installer
            'RemoveProtos.exe',  # Game cleanup tool
            'Language Selector.exe',  # Language selection tool
            'CrashSender',  # Crash reporting tools
            'UWP_Helper',  # Windows Store helper
            'HV_ASUSclient.exe',  # Hardware-specific client
        ]
    
    print(f"Scanning '{target_dir}' for executables...")
    
    for root, dirs, files in os.walk(target_path):
        for file in files:
            file_path = Path(root) / file
            
            # Check if it's an executable
            if file_path.suffix.lower() not in exe_extensions:
                continue
            
            # Check exclude patterns
            should_exclude = False
            file_name = file_path.name.lower()
            
            for pattern in exclude_patterns:
                pattern_lower = pattern.lower()
                # Check if pattern matches the filename (supports partial matches)
                if pattern_lower in file_name:
                    should_exclude = True
                    break
            
            if should_exclude:
                print(f"Excluded: {file_path}")
                continue
            
            executables.append(file_path)
            print(f"Found: {file_path}")
    
    return executables


def create_shortcut(target_path, shortcut_path, description=""):
    """Create a Windows shortcut (.lnk file) pointing to the target executable."""
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.Targetpath = str(target_path)
        shortcut.WorkingDirectory = str(target_path.parent)
        shortcut.Description = description or f"Shortcut to {target_path.name}"
        shortcut.save()
        return True
    except Exception as e:
        print(f"Error creating shortcut for {target_path.name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Create shortcuts for all executables in target directories')
    parser.add_argument('--targets', '-t', nargs='+', 
                       default=[r"D:\Games", r"E:\Game", r"F:\Program Files", 
                               r"F:\Frontends\Steam\steamapps\common", r"E:\SteamLibrary\steamapps\common"],
                       help='Target directories to scan for executables')
    parser.add_argument('--output', '-o', default=r"E:\Desktop\Games", 
                       help='Output directory for shortcuts (default: E:\\Desktop\\Games)')
    parser.add_argument('--include-all', '-a', action='store_true',
                       help='Include all executables (including uninstallers, crash handlers, etc.)')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Show what would be created without actually creating shortcuts')
    
    args = parser.parse_args()
    
    print("Game Shortcut Creator")
    print("=" * 50)
    print(f"Target directories: {', '.join(args.targets)}")
    print(f"Shortcuts directory: {args.output}")
    if args.dry_run:
        print("DRY RUN MODE - No shortcuts will be created")
    print()
    
    # Validate target directories
    valid_targets = []
    for target_dir in args.targets:
        target_path = Path(target_dir)
        if not target_path.exists():
            print(f"Warning: Target directory '{target_dir}' does not exist. Skipping.")
            continue
        if not target_path.is_dir():
            print(f"Warning: '{target_dir}' is not a directory. Skipping.")
            continue
        valid_targets.append(target_dir)
    
    if not valid_targets:
        print("Error: No valid target directories found.")
        return 1
    
    # Create shortcuts directory if it doesn't exist
    shortcuts_path = Path(args.output)
    if not args.dry_run:
        try:
            shortcuts_path.mkdir(parents=True, exist_ok=True)
            print(f"Created shortcuts directory: {shortcuts_path}")
        except Exception as e:
            print(f"Error creating shortcuts directory: {e}")
            return 1
    
    # Find all executables from all target directories
    exclude_patterns = None if args.include_all else None
    all_executables = []
    
    for target_dir in valid_targets:
        print(f"\nScanning: {target_dir}")
        executables = find_executables(target_dir, exclude_patterns)
        all_executables.extend(executables)
    
    if not all_executables:
        print("No executables found in any target directory.")
        return 0
    
    print(f"\nFound {len(all_executables)} total executables across all directories.")
    
    if args.dry_run:
        print("\nShortcuts that would be created:")
        for exe_path in all_executables:
            shortcut_name = exe_path.stem + ".lnk"
            print(f"  {shortcut_name} -> {exe_path}")
        return 0
    
    print("\nCreating shortcuts...")
    
    # Create shortcuts
    successful_shortcuts = 0
    skipped_shortcuts = 0
    failed_shortcuts = 0
    
    for exe_path in all_executables:
        # Create shortcut name (remove extension and add .lnk)
        shortcut_name = exe_path.stem + ".lnk"
        shortcut_path = shortcuts_path / shortcut_name
        
        # Skip if shortcut already exists
        if shortcut_path.exists():
            print(f"Shortcut already exists: {shortcut_name}")
            skipped_shortcuts += 1
            continue
        
        if create_shortcut(exe_path, shortcut_path):
            print(f"Created: {shortcut_name}")
            successful_shortcuts += 1
        else:
            print(f"Failed: {shortcut_name}")
            failed_shortcuts += 1
    
    print(f"\nSummary:")
    print(f"Total executables found: {len(all_executables)}")
    print(f"Shortcuts created successfully: {successful_shortcuts}")
    print(f"Shortcuts skipped (already exist): {skipped_shortcuts}")
    print(f"Shortcuts failed: {failed_shortcuts}")
    print(f"Shortcuts location: {shortcuts_path}")
    
    return 0 if failed_shortcuts == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
