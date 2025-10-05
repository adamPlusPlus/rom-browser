#!/usr/bin/env python3
"""
Script to create shortcuts for executables in a single target directory.
"""

import os
import sys
from pathlib import Path
import win32com.client


def find_executables(target_dir):
    """Find all executable files in subdirectories of the target directory."""
    target_path = Path(target_dir)
    
    if not target_path.exists():
        print(f"Error: Target directory '{target_dir}' does not exist.")
        return []
    
    if not target_path.is_dir():
        print(f"Error: '{target_dir}' is not a directory.")
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
        'launchmod_',  # Mod launchers
        'modengine2_launcher.exe',  # ModEngine launcher
        'start_protected_game.exe',  # Protected game launcher
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
    
    print(f"Scanning '{target_dir}' for executables...")
    
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
                print(f"Excluded: {file_path}")
                continue
            
            # Find the game directory (first level under target)
            relative_path = file_path.relative_to(target_path)
            game_dir = relative_path.parts[0] if relative_path.parts else "root"
            
            if game_dir not in game_dirs:
                game_dirs[game_dir] = []
            
            game_dirs[game_dir].append(file_path)
            print(f"Found: {file_path}")
    
    # Select one executable per game directory
    selected_executables = []
    
    for game_dir, executables in game_dirs.items():
        if not executables:
            continue
            
        # Sort executables by preference
        def sort_key(exe_path):
            name = exe_path.name.lower()
            # Prefer main game executables over shipping builds
            if 'shipping' in name:
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
        print(f"Selected for {game_dir}: {selected}")
        
        # Log other executables that were skipped
        for exe in executables[1:]:
            print(f"  Skipped: {exe}")
    
    return selected_executables


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
    if len(sys.argv) != 2:
        print("Usage: python create_shortcuts_single.py <target_directory>")
        print("Example: python create_shortcuts_single.py \"D:\\Games\"")
        return 1
    
    target_directory = sys.argv[1]
    shortcuts_directory = r"E:\Desktop\Games"
    
    print("Game Shortcut Creator - Single Directory")
    print("=" * 50)
    print(f"Target directory: {target_directory}")
    print(f"Shortcuts directory: {shortcuts_directory}")
    print()
    
    # Create shortcuts directory if it doesn't exist
    shortcuts_path = Path(shortcuts_directory)
    shortcuts_path.mkdir(parents=True, exist_ok=True)
    print(f"Created shortcuts directory: {shortcuts_path}")
    
    # Find all executables
    executables = find_executables(target_directory)
    
    if not executables:
        print("No executables found in the target directory.")
        return 0
    
    print(f"\nFound {len(executables)} executables.")
    print("\nCreating shortcuts...")
    
    # Create shortcuts
    successful_shortcuts = 0
    skipped_shortcuts = 0
    failed_shortcuts = 0
    
    for exe_path in executables:
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
    print(f"Total executables found: {len(executables)}")
    print(f"Shortcuts created successfully: {successful_shortcuts}")
    print(f"Shortcuts skipped (already exist): {skipped_shortcuts}")
    print(f"Shortcuts failed: {failed_shortcuts}")
    print(f"Shortcuts location: {shortcuts_path}")
    
    return 0 if failed_shortcuts == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
