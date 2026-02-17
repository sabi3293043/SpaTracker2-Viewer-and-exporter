# Manual Installation Guide for Blender 5.0

## Method 1: Install from the ZIP file (Easiest - Recommended)

1. Open Blender 5.0
2. Go to **Edit > Preferences**
3. Click on the **Add-ons** tab (NOT "Get Extensions")
4. Click the **Install...** button at the top
5. Navigate to: `E:\AIManagerPInokio\api\SpaTracker2\blender_addon.zip`
6. Select the ZIP file and click **Install Add-on**
7. The addon should appear in the list - search for "SpaTracker2"
8. **Check the checkbox** to enable it
9. Click **Save Preferences** at the bottom left

---

## Method 2: Install the Python file directly

1. Open Blender 5.0
2. Go to **Edit > Preferences**
3. Click on the **Add-ons** tab
4. Click the **Install...** button
5. Navigate to: `E:\AIManagerPInokio\api\SpaTracker2\blender_addon\spatracker2_importer.py`
6. Select the file and click **Install Add-on**
7. Search for "SpaTracker2" in the addon list
8. **Check the checkbox** to enable it
9. Click **Save Preferences**

---

## Method 3: Copy to addons folder manually

1. Close Blender completely
2. Copy the file `spatracker2_importer.py` to:
   ```
   C:\Users\beenj\AppData\Roaming\Blender Foundation\Blender\5.0\scripts\addons\
   ```
3. If the `scripts\addons` folder doesn't exist, create it
4. Open Blender
5. Go to **Edit > Preferences > Add-ons**
6. Search for "SpaTracker2"
7. Enable the addon
8. Click **Save Preferences**

---

## Method 4: Use the install script

Run this command:
```bash
cd E:\AIManagerPInokio\api\SpaTracker2\blender_addon
python install_addon.py
```

Then open Blender and enable the addon in Preferences > Add-ons.

---

## After Installation

1. Go to **File > Import > SpaTracker2 (.npz)**
2. Navigate to your NPZ file:
   ```
   E:\AIManagerPInokio\api\SpaTracker2\app\temp_local\session_fd9d24ad\results\result.npz
   ```
3. Click **Import SpaTracker2 NPZ**

---

## Troubleshooting

### Addon doesn't appear in the list
1. Make sure you're looking in the **Add-ons** tab, not "Get Extensions"
2. Try searching for "spa" or "tracker" or "import"
3. Restart Blender and try again

### Checkbox is grayed out / can't enable
1. Check the System Console (**Window > Toggle System Console**)
2. Look for error messages
3. The most common issue is missing numpy - but Blender 5.0 includes it by default

### Import menu doesn't show after enabling
1. Restart Blender
2. The menu should appear at **File > Import > SpaTracker2 (.npz)**

### Still not working?
1. Open Blender System Console: **Window > Toggle System Console**
2. Enable the addon
3. Watch for error messages in the console
4. Common errors:
   - `No module named 'numpy'`: Need to install numpy
   - `SyntaxError`: Python version mismatch
   - `ImportError`: Missing dependency

---

## Quick Test

After installation, verify it works:

1. In Blender, press **F3** (search)
2. Type "SpaTracker2"
3. If you see "Import SpaTracker2 NPZ", it's working!
4. Or go to **File > Import** and look for "SpaTracker2 (.npz)"
