#!/usr/bin/env python3
"""
Game Shortcut Creator with Configuration File Support
Reads game directories from a config file and creates shortcuts.
"""

import os
import sys
import argparse
from pathlib import Path
import win32com.client


def read_config(config_file):
    """Read game directories from configuration file."""
    directories = []
    output_dir = r"E:\Desktop\Games"  # Default output directory
    
    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found.")
        return directories, output_dir
    
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
            
            # Add directory to list
            if os.path.exists(line):
                directories.append(line)
            else:
                print(f"Warning: Directory '{line}' (line {line_num}) does not exist. Skipping.")
    
    return directories, output_dir


def find_executables(target_dir):
    """Find all executable files in subdirectories of the target directory."""
    target_path = Path(target_dir)
    
    if not target_path.exists():
        return []
    
    if not target_path.is_dir():
        return []
    
    # Common executable extensions
    exe_extensions = {'.exe', '.bat', '.cmd', '.msi', '.com'}
    
    # Exclude patterns for common non-game executables
    exclude_patterns = [
        'unins000.exe', 'unins001.exe', 'unins002.exe',  # Uninstallers
        'UnityCrashHandler',  # Unity crash handlers
        'dxwebsetup.exe', 'DXSETUP.exe',  # DirectX installer
        'QuickSFV.EXE',  # File verification tool
        'CrashReportClient.exe', 'crashpad_handler.exe',  # Crash reporting
        'EpicWebHelper.exe',  # Epic launcher helper
        'createdump.exe',  # Debug dump tool
        'msiexec.exe',  # Windows installer
        'RemoveProtos.exe',  # Game cleanup tool
        'Language Selector.exe',  # Language selection tool
        'CrashSender',  # Crash reporting tools
        'UWP_Helper',  # Windows Store helper
        'HV_ASUSclient.exe',  # Hardware-specific client
        'vcredist', 'vc_redist',  # Visual C++ redistributables
        'dotnetfx', 'NDP',  # .NET Framework installers
        'PhysX',  # PhysX installers
        'oalinst.exe',  # OpenAL installer
        'UE4PrereqSetup', 'UEPrereqSetup',  # Unreal Engine prerequisites
        'ActivationUI.exe',  # Activation UI
        'clientdx.exe', 'clientogl.exe', 'clientxna.exe',  # Client executables
        'clokspl.exe',  # Clock splash
        'CSGMERGE.exe',  # CSG merge tool
        'devcon32.exe', 'devcon64.exe',  # Device console
        'DOSBox.exe', 'GOGDOSConfig.exe',  # DOS emulation
        'DromEd.exe',  # DromEd editor
        'ergccopier.exe',  # ERG copier
        'FinalAlert2MO.exe',  # Final Alert 2
        'gamemd.exe',  # Game MD
        'Generals.exe',  # Generals (duplicate)
        'GOLDSKIP.exe',  # Gold skip
        'Guild3ModLauncher.exe', 'Guild3ModUploader.exe',  # Mod tools
        'install_swrnet.bat',  # Install script
        'json_formatter.exe',  # JSON formatter
        'MentalOmegaClient.exe',  # Mental Omega client
        'Microsoft .NET Framework',  # .NET Framework
        'Microsoft Visual C++',  # Visual C++
        'mph.exe', 'mphmd.exe',  # MPH tools
        'NOX.exe',  # NOX (duplicate)
        'PBAConfig.exe',  # Pinball Arcade config
        'pbsvc.exe',  # PunkBuster service
        'PinballArcade11.exe',  # Pinball Arcade 11
        'PinballM-UNLOCKER.exe',  # Pinball M unlocker
        'Ra2.exe', 'RA2Launcher.exe', 'RA2MD.exe',  # Red Alert 2
        'Register.exe',  # Register
        'rgb2theora.exe',  # RGB to Theora
        'ROTR185_Lnchr.exe', 'ROTRMapPack_V2.exe',  # ROTR tools
        'RPG_RT.exe',  # RPG Runtime
        'Setup.exe',  # Setup
        'setup_the_guild_3',  # Guild 3 setup
        'Slot Shots Pinball Ultimate.exe',  # Slot Shots Pinball
        'SpaceChem.exe',  # SpaceChem
        'SuchArtLinkLauncher.exe',  # SuchArt launcher
        'SUN.exe',  # SUN
        'SWR.net',  # SWR.net tools
        'Syringe.exe',  # Syringe
        'The Bard\'s Tale.exe',  # Bard's Tale
        'Thief2.exe',  # Thief 2
        'tis100.exe',  # TIS-100
        'Touchup.exe',  # Touchup
        'TSGDITP1.exe', 'TSNODTP1.exe',  # TS themes
        'TSLauncher.exe',  # TS launcher
        'Uinst_ROTR_Beta185.exe',  # Uninstall ROTR
        'Uninst.exe', 'uninstll.exe',  # Uninstallers
        'UninstRotrMaps.exe',  # Uninstall ROTR maps
        'UninstSwrnet.bat',  # Uninstall SWR.net
        'Verify BIN files before installation.bat',  # Verify script
        'WestwoodOnline.msi',  # Westwood Online
        'WorldBuilder.exe', 'WorldBuilder_ROTR.exe',  # World builders
        'YURI.exe',  # YURI
        'Zombasite.exe',  # Zombasite
        # Additional exclusions
        'Server.exe', 'server.exe',  # Server executables
        'Launcher.exe', 'launcher.exe',  # Generic launchers (we'll prefer main game exes)
        'Cleanup.exe', 'cleanup.exe',  # Cleanup tools
        'BF4WebHelper.exe', 'BF4X86WebHelper.exe',  # Battlefield helpers
        'BFLauncher.exe', 'BFLauncher_x86.exe',  # Battlefield launchers
        'battlelog-web-plugins.exe',  # Battlelog plugins
        'badvpn-client.exe', 'badvpntcp.bat',  # VPN clients
        'swrnet-client.exe',  # SWR.net client
        'EOSAuthLauncher.exe',  # Epic Online Services
        'install_pspc_sdk_runtime.bat',  # PSPC runtime
        'easyanticheat_eos_setup.exe',  # EasyAntiCheat
        'install_easyanticheat_eos_setup.bat',  # EasyAntiCheat install
        'uninstall_easyanticheat_eos_setup.bat',  # EasyAntiCheat uninstall
        'InjectorCLIx64.exe',  # Injector
        'crs-handler.exe',  # CRS handler
        # 'launchmod_',  # Mod launchers - now included
        # 'modengine2_launcher.exe',  # ModEngine launcher - now included
        # 'start_protected_game.exe',  # Protected game launcher - now included
        'dowser.exe',  # Dowser
        'CrashReporter.exe',  # Crash reporter
        'launcher-installer-windows',  # Launcher installer
        'Uninstall Vortex.exe',  # Vortex uninstaller
        'elevate.exe',  # Elevate
        'dotnetprobe.exe',  # .NET probe
        'divine.exe',  # Divine
        'ARCtool.exe',  # ARC tool
        'quickbms_4gb_files.exe',  # QuickBMS
        '7z.exe',  # 7-Zip
        'ModInstallerIPC.exe',  # Mod installer
        'apphost.exe',  # App host
        'compress_bitmaps.bat',  # Bitmap compression
        'UnrealCEFSubProcess.exe',  # Unreal CEF subprocess
        'easyanticheat_setup.exe',  # EasyAntiCheat setup
        'Rockstar-Games-Launcher.exe',  # Rockstar launcher
        'Social-Club-Setup.exe',  # Social Club setup
        'VulkanRT-',  # Vulkan runtime
        'python.exe', 'pythonw.exe',  # Python
        'zsync.exe', 'zsyncmake.exe',  # Zsync
        'TTS-Deck-Editor.exe',  # TTS deck editor
        'run_',  # Run scripts
        'ZFGameBrowser.exe',  # ZF game browser
        'openmw-',  # OpenMW tools
        'Uninstall.exe',  # Generic uninstaller
    ]
    
    # Group executables by game directory
    game_dirs = {}
    
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
                if pattern_lower in file_name:
                    should_exclude = True
                    break
            
            if should_exclude:
                continue
            
            # Find the game directory (first level under target)
            relative_path = file_path.relative_to(target_path)
            game_dir = relative_path.parts[0] if relative_path.parts else "root"
            
            if game_dir not in game_dirs:
                game_dirs[game_dir] = []
            
            game_dirs[game_dir].append(file_path)
    
    # Also check for existing .lnk files (for DOSBox games and other launchers)
    for root, dirs, files in os.walk(target_path):
        for file in files:
            if file.lower().endswith('.lnk'):
                file_path = Path(root) / file
                relative_path = file_path.relative_to(target_path)
                game_dir = relative_path.parts[0] if relative_path.parts else "root"
                
                # Only include .lnk files that look like game launchers
                file_name_lower = file.lower()
                if any(keyword in file_name_lower for keyword in ['launch', 'play', 'start', 'run']):
                    if game_dir not in game_dirs:
                        game_dirs[game_dir] = []
                    game_dirs[game_dir].append(file_path)
    
    # Select one executable per game directory
    selected_executables = []
    
    for game_dir, executables in game_dirs.items():
        if not executables:
            continue
            
        # Sort executables by preference
        def sort_key(exe_path):
            name = exe_path.name.lower()
            # Prefer .lnk launcher files (for DOSBox games)
            if name.endswith('.lnk'):
                return -1
            # Prefer main game executables over shipping builds
            elif 'shipping' in name:
                return 3
            elif 'win64' in name:
                return 2
            elif 'launcher' in name:
                return 1
            else:
                return 0
        
        # Sort by preference, then by name
        executables.sort(key=lambda x: (sort_key(x), x.name.lower()))
        
        # Select the best executable
        selected = executables[0]
        selected_executables.append(selected)
    
    return selected_executables


def get_shortcut_name(exe_path):
    """Generate a better name for the shortcut based on the executable and directory."""
    name = exe_path.name.lower()
    game_dir = exe_path.parent.name
    
    # Map specific launchers to better names
    if 'modengine2_launcher.exe' in name:
        return f"{game_dir} (ModEngine)"
    elif 'start_protected_game.exe' in name:
        return f"{game_dir} (Protected)"
    elif 'mcclauncher.exe' in name:
        return f"{game_dir} (MCC Launcher)"
    elif 'startup.exe' in name:
        return f"{game_dir} (Startup)"
    elif 'redprelauncher.exe' in name:
        return f"{game_dir} (Pre-Launcher)"
    elif 'launchmod_' in name:
        mod_name = name.replace('launchmod_', '').replace('.bat', '')
        return f"{game_dir} (Mod - {mod_name.title()})"
    elif name.endswith('.lnk'):
        # For .lnk files, use the filename without extension
        return exe_path.stem
    else:
        # Default: use the executable name without extension
        return exe_path.stem


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


def clean_old_shortcuts(output_dir, current_executables):
    """Remove shortcuts that no longer point to existing executables."""
    output_path = Path(output_dir)
    if not output_path.exists():
        return 0
    
    current_names = {exe.stem for exe in current_executables}
    removed_count = 0
    
    for shortcut_file in output_path.glob("*.lnk"):
        shortcut_name = shortcut_file.stem
        if shortcut_name not in current_names:
            try:
                shortcut_file.unlink()
                print(f"Removed old shortcut: {shortcut_name}.lnk")
                removed_count += 1
            except Exception as e:
                print(f"Error removing shortcut {shortcut_name}.lnk: {e}")
    
    return removed_count


def main():
    parser = argparse.ArgumentParser(description='Create shortcuts for games using configuration file')
    parser.add_argument('--config', '-c', default='game_directories.conf',
                       help='Configuration file path (default: game_directories.conf)')
    parser.add_argument('--clean', action='store_true',
                       help='Clean old shortcuts that no longer point to existing games')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Show what would be created without actually creating shortcuts')
    
    args = parser.parse_args()
    
    print("Game Shortcut Creator - Configuration Mode")
    print("=" * 50)
    print(f"Configuration file: {args.config}")
    if args.dry_run:
        print("DRY RUN MODE - No shortcuts will be created")
    print()
    
    # Read configuration
    directories, output_dir = read_config(args.config)
    
    if not directories:
        print("No valid directories found in configuration file.")
        return 1
    
    print(f"Found {len(directories)} directories in configuration:")
    for directory in directories:
        print(f"  {directory}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    if not args.dry_run:
        output_path.mkdir(parents=True, exist_ok=True)
        print(f"Created output directory: {output_path}")
    
    # Find all executables from all directories
    all_executables = []
    empty_directories = []
    
    for directory in directories:
        print(f"Scanning: {directory}")
        executables = find_executables(directory)
        if executables:
            all_executables.extend(executables)
            print(f"  Found {len(executables)} executables")
        else:
            empty_directories.append(directory)
            print(f"  No executables found")
    
    # Report empty directories
    if empty_directories:
        print(f"\nDirectories with no executables found:")
        for directory in empty_directories:
            print(f"  {directory}")
        print()
    
    if not all_executables:
        print("No executables found in any directory.")
        return 0
    
    print(f"Total executables found: {len(all_executables)}")
    
    if args.dry_run:
        print("\nShortcuts that would be created:")
        for exe_path in all_executables:
            shortcut_name = get_shortcut_name(exe_path) + ".lnk"
            print(f"  {shortcut_name} -> {exe_path}")
        return 0
    
    # Clean old shortcuts if requested
    if args.clean:
        print("\nCleaning old shortcuts...")
        removed_count = clean_old_shortcuts(output_dir, all_executables)
        print(f"Removed {removed_count} old shortcuts")
    
    print("\nCreating shortcuts...")
    
    # Create shortcuts
    successful_shortcuts = 0
    skipped_shortcuts = 0
    failed_shortcuts = 0
    
    for exe_path in all_executables:
        # Create shortcut name using the improved naming function
        shortcut_name = get_shortcut_name(exe_path) + ".lnk"
        shortcut_path = output_path / shortcut_name
        
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
    print(f"Shortcuts location: {output_path}")
    
    return 0 if failed_shortcuts == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
