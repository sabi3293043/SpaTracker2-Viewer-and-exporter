# SpaTracker2 Blender Addon - Complete Usage Guide (Blender 5.0+)

## Quick Start

### Step 1: Install the Addon

**Option A: Install from ZIP (Easiest)**

1. Use the pre-created ZIP file: `E:\AIManagerPInokio\api\SpaTracker2\blender_addon.zip`
2. Open Blender 5.0+
3. Go to **Edit > Preferences**
4. Click the **Get Extensions** tab
5. Click **Install from Disk...** button (top right)
6. Select `blender_addon.zip`
7. Click **Install from Disk**
8. Enable the addon by checking the checkbox next to "SpaTracker2 Importer"

**Option B: Run Install Script**

```bash
cd E:\AIManagerPInokio\api\SpaTracker2\blender_addon
python install_addon.py
```

Then enable the addon in Blender Preferences > Get Extensions.

**Option C: Manual Installation**

The install script has already copied the addon to:
```
C:\Users\beenj\AppData\Roaming\Blender Foundation\Blender\5.0\extensions\spatracker2_importer\
```

Just open Blender and enable the addon in Preferences.

### Step 2: Run SpaTracker2 Tracking

1. Use the SpaTracker2 web UI to process your video
2. After processing completes, find the output NPZ file at:
   ```
   E:\AIManagerPInokio\api\SpaTracker2\app\temp_local\session_<SESSION_ID>\results\result.npz
   ```

### Step 3: Import into Blender

1. In Blender 5.0+, go to **File > Import > SpaTracker2 (.npz)**
2. Navigate to your `result.npz` file
3. Configure import options (see below)
4. Click **Import SpaTracker2 NPZ**

---

## Import Options Explained

When you open the import dialog, you'll see these options in the left panel:

### Import Cameras
- **What it does**: Creates a camera object for each frame in your video
- **Use case**: Use these cameras to match 3D objects to your video perspective
- **Result**: Camera objects named `Camera_0000`, `Camera_0001`, etc.

### Import Trajectories
- **What it does**: Creates visualization of tracked 3D points
- **Use case**: See the motion paths of tracked features in 3D space
- **Result**: Two objects:
  - `TrajectoryPoints`: Points showing where tracked features are in 3D
  - `TrajectoryLines`: Lines connecting points across time

### Trajectory Scale
- **What it does**: Scales the size of trajectory visualization
- **Default**: 1.0
- **When to adjust**: 
  - Increase if trajectories are too small to see
  - Decrease if trajectories are too large for your scene

### Camera Size
- **What it does**: Controls the visual size of camera frustums
- **Default**: 0.1
- **When to adjust**: 
  - Increase for better visibility in large scenes
  - Decrease for detailed work with many cameras

---

## Understanding the Data

### NPZ File Structure

The SpaTracker2 NPZ file contains:

| Array | Shape | Description |
|-------|-------|-------------|
| `extrinsics` | (T, 4, 4) | Camera pose matrices (world from camera) |
| `intrinsics` | (T, 3, 3) or (1, 3, 3) | Camera intrinsic matrices |
| `coords` | (T, N, 3) | 3D trajectory coordinates (T frames, N points) |
| `video` | (T, C, H, W) | Video frames (used for dimensions) |
| `depths` | (T, H, W) | Depth maps per frame |
| `visibs` | (T, N) | Visibility flags for each point |
| `confs` | (T, N) | Confidence scores |

### Coordinate Systems

**Important**: The addon automatically converts between coordinate systems:

- **SpaTracker2 (OpenCV)**: Y-down, Z-forward
- **Blender**: Z-up, -Y-forward

You don't need to do any manual conversion - the addon handles this automatically.

---

## Collection Structure

After import, your Outliner will show:

```
Scene Collection
└── SpaTracker2_Import
    ├── Cameras
    │   ├── Camera_0000
    │   ├── Camera_0001
    │   ├── Camera_0002
    │   └── ...
    └── Trajectories
        ├── TrajectoryPoints
        └── TrajectoryLines
```

---

## Common Workflows

### Workflow 1: Camera Matchmoving

1. Import your SpaTracker2 NPZ file
2. Add a 3D object to your scene
3. Position the object in the first frame
4. Scrub through the timeline - the object will appear correctly tracked!

### Workflow 2: Trajectory Analysis

1. Import with "Import Trajectories" enabled
2. Select the `TrajectoryPoints` object
3. Go to Edit Mode to see individual points
4. Use Blender's measurement tools to analyze distances

### Workflow 3: Export to Other Formats

1. After importing, select the cameras or trajectories
2. Use **File > Export** to save as FBX, OBJ, etc.
3. Import into other 3D software

---

## Using the NPZ Reader Script

For quick inspection of NPZ files without opening Blender:

### Show File Info
```bash
cd E:\AIManagerPInokio\api\SpaTracker2\blender_addon
E:\AIManagerPInokio\api\SpaTracker2\app\venv\Scripts\python.exe ^
  read_npz.py ^
  "E:\AIManagerPInokio\api\SpaTracker2\app\temp_local\session_fd9d24ad\results\result.npz" ^
  --info
```

### Export to JSON
```bash
E:\AIManagerPInokio\api\SpaTracker2\app\venv\Scripts\python.exe ^
  read_npz.py ^
  "path/to/result.npz" ^
  --export --output-dir ./export
```

### Export Cameras to CSV
```bash
E:\AIManagerPInokio\api\SpaTracker2\app\venv\Scripts\python.exe ^
  read_npz.py ^
  "path/to/result.npz" ^
  --cameras-csv
```

### Export Trajectories to CSV
```bash
E:\AIManagerPInokio\api\SpaTracker2\app\venv\Scripts\python.exe ^
  read_npz.py ^
  "path/to/result.npz" ^
  --trajectories-csv
```

---

## Troubleshooting

### Addon Doesn't Show in Preferences
1. Make sure you're using Blender 5.0 or later
2. Check that `blender_manifest.toml` exists in the addon folder
3. Verify the addon is in the correct location:
   ```
   C:\Users\beenj\AppData\Roaming\Blender Foundation\Blender\5.0\extensions\spatracker2_importer\
   ```

### "No module named 'numpy'"
Blender 5.0+ includes numpy by default. If you get this error:
1. Check Blender's system console for details
2. Try resetting Blender preferences

### Import Fails with "KeyError"
The NPZ file may be corrupted or incomplete. Re-run the tracking process.

### Cameras Appear Distorted
Check that the NPZ file contains valid intrinsics. The addon reads FOV from the focal length values.

### Trajectories Not Visible
- Enable "Import Trajectories" in the import dialog
- Increase "Trajectory Scale" if points are too small
- Check that the NPZ file contains `coords` array

### Wrong Orientation
The addon automatically converts coordinate systems. If orientation looks wrong:
1. Check the NPZ file contains valid extrinsics
2. Verify the video was processed correctly in SpaTracker2

### Import Menu Not Showing
1. Restart Blender after enabling the addon
2. Check **Edit > Preferences > Add-ons** to ensure it's enabled
3. Look for errors in **Window > Toggle System Console**

---

## Tips and Best Practices

1. **Organize your imports**: Each import creates a new collection. Name your sessions or delete old imports to keep scenes clean.

2. **Use collections**: Mute the Cameras or Trajectories collections in the Outliner to hide them without deleting.

3. **Animate cameras**: The imported cameras are already animated across frames. Scrub the timeline to see camera motion.

4. **Combine with video**: Import your video as a background image in the camera view for reference.

5. **Export for game engines**: After importing, export as FBX for use in Unity, Unreal, etc.

6. **Check the console**: Enable Blender's system console (**Window > Toggle System Console**) to see detailed error messages.

---

## File Locations

### NPZ Output Files
```
E:\AIManagerPInokio\api\SpaTracker2\app\temp_local\session_<SESSION_ID>\results\result.npz
```

### Addon Location (after install)
```
C:\Users\beenj\AppData\Roaming\Blender Foundation\Blender\5.0\extensions\spatracker2_importer\
```

### ZIP File for Installation
```
E:\AIManagerPInokio\api\SpaTracker2\blender_addon.zip
```

### Blender Logs
```
C:\Users\beenj\AppData\Roaming\Blender Foundation\Blender\5.0\logs\blender.log
```

---

## Verifying Installation

1. Open Blender 5.0+
2. Go to **Edit > Preferences > Add-ons**
3. Search for "SpaTracker2"
4. You should see "SpaTracker2 Importer" in the list
5. Check the checkbox to enable it
6. The import menu should now appear at **File > Import > SpaTracker2 (.npz)**

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the SpaTracker2 documentation
3. Check Blender's system console for error messages (**Window > Toggle System Console**)
4. Inspect the Blender log file for detailed errors
