"""
SpaTracker2 Blender Addon Installer (Blender 5.0+)

This script helps install the SpaTracker2 addon for Blender 5.0+.
Blender 5.0 uses the new extension system with blender_manifest.toml.
"""

import os
import shutil
import sys
from pathlib import Path


def find_blender_extension_path():
    """Find the Blender 5.0+ extension directory for the current user"""
    
    if sys.platform == 'win32':
        # Windows - Blender 5.0+ uses extensions folder
        base = Path(os.environ.get('APPDATA', '')) / 'Blender Foundation' / 'Blender'
    elif sys.platform == 'darwin':
        # macOS
        base = Path.home() / 'Library' / 'Application Support' / 'Blender'
    elif sys.platform == 'linux':
        # Linux
        base = Path.home() / '.config' / 'blender'
    else:
        return None
    
    # Find Blender 5.0+ folder
    if base.exists():
        versions = [d for d in base.iterdir() if d.is_dir()]
        # Look for version 5.0 or higher
        for version in sorted(versions, reverse=True):
            try:
                version_num = float(version.name.split('.')[0] + '.' + version.name.split('.')[1])
                if version_num >= 5.0:
                    extension_path = version / 'extensions'
                    extension_path.mkdir(parents=True, exist_ok=True)
                    return extension_path, version.name
            except (ValueError, IndexError):
                continue
        
        # If no 5.0+ found, use the latest version
        if versions:
            latest_version = max(versions)
            extension_path = latest_version / 'extensions'
            extension_path.mkdir(parents=True, exist_ok=True)
            return extension_path, latest_version.name
    
    return None


def install_addon():
    """Install the SpaTracker2 addon to Blender 5.0+"""
    
    # Get the current directory (blender_addon folder)
    addon_source = Path(__file__).parent
    addon_name = 'spatracker2_importer'
    
    # Find Blender extension path
    result = find_blender_extension_path()
    
    if not result:
        print("[ERROR] Could not find Blender 5.0+ extension directory.")
        print("\nManual installation instructions:")
        print("1. Open Blender 5.0+")
        print("2. Go to Edit > Preferences")
        print("3. Click 'Get Extensions' tab")
        print("4. Click 'Install from Disk...' button")
        print(f"5. Create a ZIP of this folder and select it")
        print(f"\nAddon folder: {addon_source}")
        return False
    
    extension_path, blender_version = result
    
    # Create destination folder
    addon_dest = extension_path / addon_name
    addon_dest.mkdir(exist_ok=True)
    
    # Copy addon files
    files_to_copy = ['__init__.py', 'blender_manifest.toml', 'README.md']
    copied = []
    for file in files_to_copy:
        src = addon_source / file
        if src.exists():
            shutil.copy(src, addon_dest / file)
            copied.append(file)
            print(f"[OK] Copied: {file}")
    
    if not copied:
        print("[ERROR] No files were copied. Check that the addon files exist.")
        return False
    
    print(f"\n[OK] Addon installed to: {addon_dest}")
    print(f"  Blender version detected: {blender_version}")
    
    print("\nNext steps:")
    print("1. Open Blender 5.0+ (or restart if already open)")
    print("2. Go to Edit > Preferences")
    print("3. Click 'Get Extensions' or 'Add-ons' tab")
    print("4. Search for 'SpaTracker2'")
    print("5. Enable the addon by checking the checkbox")
    print("\nUsage:")
    print("  File > Import > SpaTracker2 (.npz)")
    
    print("\nTip: You can also create a ZIP file for easier installation:")
    print(f"  1. Select all files in: {addon_source}")
    print(f"  2. Right-click > Send to > Compressed (zipped) folder")
    print(f"  3. In Blender: Edit > Preferences > Get Extensions > Install from Disk")
    
    return True


def create_zip():
    """Create a ZIP file for easy installation"""
    import zipfile
    
    addon_source = Path(__file__).parent
    zip_path = addon_source.parent / f'{addon_source.name}.zip'
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in ['__init__.py', 'blender_manifest.toml', 'README.md', 'USAGE.md']:
            src = addon_source / file
            if src.exists():
                zipf.write(src, file)
    
    print(f"\n[OK] Created ZIP file: {zip_path}")
    print("\nTo install:")
    print("1. Open Blender 5.0+")
    print("2. Edit > Preferences > Get Extensions")
    print("3. Click 'Install from Disk...'")
    print("4. Select the ZIP file")
    print("5. Enable the addon")
    
    return zip_path


if __name__ == "__main__":
    print("SpaTracker2 Blender Addon Installer (Blender 5.0+)")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--zip':
        create_zip()
    else:
        install_addon()
