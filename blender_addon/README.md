# SpaTracker2 Blender Addon (Blender 5.0+)

This Blender addon imports SpaTracker2 NPZ tracking data files and visualizes camera poses and 3D trajectories in Blender.

**Important:** This addon is designed for **Blender 5.0+** and uses the new extension system with `blender_manifest.toml`.

## Features

- **Import Camera Poses**: Creates camera objects for each frame with correct intrinsics and extrinsics
- **Import Trajectories**: Visualizes 3D tracking points and their motion paths
- **Configurable Options**: Adjust camera size, trajectory scale, and what to import
- **Organized Collections**: Automatically organizes imported data into Blender collections

## Installation

### Method 1: Install from ZIP (Recommended)

1. **Create a ZIP file** of the `blender_addon` folder contents:
   - Select all files in `E:\AIManagerPInokio\api\SpaTracker2\blender_addon\`
   - Right-click > Send to > Compressed (zipped) folder
   - Name it `spatracker2_importer.zip`

2. **Install in Blender**:
   - Open Blender 5.0+
   - Go to **Edit > Preferences**
   - Click on the **Get Extensions** tab
   - Click the **Install from Disk...** button (top right)
   - Select your `spatracker2_importer.zip` file
   - Click **Install from Disk**
   - Enable the addon by checking the checkbox next to "SpaTracker2 Importer"

### Method 2: Install from Folder (Development)

1. **Copy the addon folder** to Blender's extensions directory:
   - Windows: `C:\Users\<YourUsername>\AppData\Roaming\Blender Foundation\Blender\5.0\extensions\`
   
2. **Create the folder structure**:
   ```
   extensions/
   └── spatracker2_importer/
       ├── __init__.py
       ├── blender_manifest.toml
       └── README.md
   ```

3. **Enable in Blender**:
   - Open Blender 5.0+
   - Go to **Edit > Preferences > Add-ons**
   - Find "SpaTracker2 Importer" and enable it

### Method 3: Use the Install Script

Run the install script from the command line:

```bash
cd E:\AIManagerPInokio\api\SpaTracker2\blender_addon
python install_addon.py
```

Then enable the addon in Blender Preferences.

## Usage

### Importing NPZ Files

1. In Blender, go to **File > Import > SpaTracker2 (.npz)**
2. Navigate to your NPZ file location:
   ```
   E:\AIManagerPInokio\api\SpaTracker2\app\temp_local\session_fd9d24ad\results\result.npz
   ```
3. Configure import options in the left panel:
   - **Import Cameras**: Create camera objects for each frame
   - **Import Trajectories**: Create trajectory points and motion lines
   - **Trajectory Scale**: Scale factor for trajectory visualization
   - **Camera Size**: Size of camera frustum visualization
4. Click **Import SpaTracker2 NPZ**

### Understanding the Import

#### Camera Objects
- Each frame gets a camera object named `Camera_XXXX`
- Cameras are organized in the "Cameras" collection
- Camera FOV is calculated from the intrinsics matrix
- Coordinate system is automatically converted from OpenCV (Y-down, Z-forward) to Blender (Z-up, -Y-forward)

#### Trajectory Visualization
- Trajectory points are shown as vertices in "TrajectoryPoints" object
- Motion paths connecting points across frames are shown in "TrajectoryLines" object
- A Skin modifier is automatically added to make lines visible in renders

#### Collections Structure
```
Scene Collection
└── SpaTracker2_Import
    ├── Cameras
    │   ├── Camera_0000
    │   ├── Camera_0001
    │   └── ...
    └── Trajectories
        ├── TrajectoryPoints
        └── TrajectoryLines
```

## NPZ File Format

The addon expects NPZ files with the following arrays:

### Required
- `extrinsics`: Camera extrinsic matrices (T, 4, 4) - world_from_cam transformation
- `intrinsics`: Camera intrinsic matrices (T, 3, 3) or (1, 3, 3)

### Optional
- `coords`: 3D trajectory coordinates (T, N, 3) - T frames, N points
- `video`: Video frames (T, C, H, W) - used to determine image dimensions
- `visibs`: Visibility flags
- `confs`: Confidence values
- `depths`: Depth maps

## Testing Your Installation

1. Open Blender System Console (**Window > Toggle System Console**)
2. Run the addon installation
3. Check the console for any error messages
4. Try importing the test file:
   ```
   E:\AIManagerPInokio\api\SpaTracker2\app\temp_local\session_fd9d24ad\results\result.npz
   ```

Expected output in console:
```
Successfully imported: 17 cameras, 100 trajectories over 17 frames
```

## Troubleshooting

### "No module named 'numpy'"
Blender 5.0+ should include numpy by default. If not:
1. Find Blender's Python executable
2. Install numpy: `python -m pip install numpy`

### Import Fails with "KeyError"
The NPZ file may be corrupted or incomplete. Re-run the tracking process.

### Cameras Appear Distorted
Check that the NPZ file contains valid intrinsics. The addon reads FOV from the focal length values.

### Trajectories Not Visible
- Enable "Import Trajectories" in the import dialog
- Increase "Trajectory Scale" if points are too small
- Check that the NPZ file contains `coords` array

### Addon Doesn't Show in Preferences
1. Make sure `blender_manifest.toml` is in the same folder as `__init__.py`
2. Check that the ZIP file contains both files at the root level
3. Verify you're using Blender 5.0 or later

## Coordinate System Conversion

SpaTracker2 uses the OpenCV convention:
- Y axis: Down
- Z axis: Forward (into the scene)

Blender uses:
- Z axis: Up
- -Y axis: Forward (into the scene)

The addon automatically applies the conversion matrix:
```
[1,  0,  0, 0]
[0, -1,  0, 0]
[0,  0, -1, 0]
[0,  0,  0, 1]
```

## Example Workflow

1. Run SpaTracker2 tracking on your video
2. Find the output NPZ file in `app/temp_local/session_XXXX/results/result.npz`
3. Open Blender 5.0+
4. Install and enable the SpaTracker2 Importer addon
5. Import the NPZ file using **File > Import > SpaTracker2 (.npz)**
6. Adjust camera and trajectory settings as needed
7. Use the imported cameras for further 3D work or rendering

## File Locations

### NPZ Output Files
```
E:\AIManagerPInokio\api\SpaTracker2\app\temp_local\session_<SESSION_ID>\results\result.npz
```

### Addon Location (after install)
```
Windows: C:\Users\<USERNAME>\AppData\Roaming\Blender Foundation\Blender\5.0\extensions\spatracker2_importer\
```

### Blender Logs
```
Windows: C:\Users\<USERNAME>\AppData\Roaming\Blender Foundation\Blender\5.0\logs\blender.log
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the SpaTracker2 documentation
3. Check Blender's system console for error messages (Window > Toggle System Console)

## License

This addon is part of the SpaTracker2 project and is released under GPL-3.0-or-later.
