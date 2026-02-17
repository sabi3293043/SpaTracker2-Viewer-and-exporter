# SpaTracker2 Viewer

🎯 **Web-based NPZ viewer and Blender export tool for SpaTracker2 tracking data**

Upload SpaTracker2 `.npz` tracking files and visualize them in 3D, then export complete animated scenes to Blender with point clouds, camera poses, and video reference.

![Export Preview](https://via.placeholder.com/800x450.png?text=SpaTracker2+Viewer+Preview)

## ✨ Features

### 🌐 Web Viewer
- **Drag & Drop Upload** - Upload `.npz` files directly in your browser
- **Interactive 3D Visualization** - View tracked points, camera trajectory, and depth data
- **Real-time Processing** - Files are converted and displayed immediately
- **No Server Required** - Runs locally through Pinokio

### 📦 Complete Export Package
Export everything needed for Blender in one ZIP file:

| Component | Format | Description |
|-----------|--------|-------------|
| **Trajectory** | PLY sequence | Sparse tracked feature points with colors |
| **Point Cloud** | PLY sequence | Dense depth-based point cloud |
| **Cameras** | JSON + Blender script | Camera poses with import automation |
| **Video** | MP4 (H.264) | Original video sequence for reference |

### 🎬 Blender Integration
- **PLY Sequence Importer** - Import animated point clouds with vertex colors
- **Camera Importer** - Two import modes:
  - *Single Animated Camera* - One camera that moves through space (always visible)
  - *Multiple Cameras* - One camera per frame (shows camera path)
- **Automatic Setup** - Correct frame rates, coordinate conversion, and keyframes

## 🚀 Quick Start

### 1. Install via Pinokio

1. Install [Pinokio](https://pinokio.computer/)
2. Discover this repo in the Pinokio browser
3. Click "Install" and wait for dependencies
4. Launch the viewer

### 2. Use the Viewer

1. **Upload** your `result.npz` file (drag & drop or click to browse)
2. **Visualize** the tracking data in 3D
3. **Export** → Click "Export to Blender"
4. **Configure** settings:
   - Frame Rate (default: 30 FPS)
   - Scale (default: 1.0)
   - Color Source (video, depth heatmap, or white)
5. **Download** the ZIP file

### 3. Import in Blender

#### Import Points:
1. Open Blender
2. `File > Import > SpaTracker2 PLY Sequence (.ply)`
3. Navigate to `trajectory/` or `pointcloud/` folder
4. Select first file (`frame_000000.ply`)
5. Click "Import"

#### Import Cameras:
1. `File > Import > SpaTracker2 Camera Sequence (.json)`
2. Navigate to `cameras/` folder
3. Select any `camera_*.json` file
4. Enable "Single Animated Camera" for smooth navigation
5. Click "Import"

## 📋 Export Contents

```
spatracker2_export_xxxxxxxx.zip
├── trajectory/              # Sparse tracked points (PLY)
│   ├── frame_000000.ply
│   ├── frame_000001.ply
│   └── ...
├── pointcloud/              # Dense point cloud (PLY)
│   ├── frame_000000.ply
│   ├── frame_000001.ply
│   └── ...
├── cameras/                 # Camera poses (JSON)
│   ├── camera_000000.json
│   ├── camera_000001.json
│   └── ...
├── video.mp4                # Original video
├── import_spatracker2_ply.py
├── import_spatracker2_cameras.py
└── README.txt
```

## 🛠️ Technical Details

### NPZ File Requirements
The viewer expects `.npz` files with the following arrays:
- `coords` (T, N, 3) - 3D trajectory points
- `depths` (T, H, W) - Depth maps per frame
- `extrinsics` (T, 4, 4) - Camera pose matrices
- `intrinsics` (T or 1, 3, 3) - Camera intrinsic matrices
- `video` (T, C, H, W) - Video frames (RGB, 0-1 normalized)
- `visibs` (T, N) - Visibility masks (optional)

### Coordinate Systems
- **SpaTracker2**: OpenCV convention (Y down, Z forward)
- **Blender**: Z up, -Y forward
- **Automatic conversion** is applied during import

### Supported Formats
- **Input**: `.npz` (SpaTracker2 format)
- **Output**: 
  - PLY (binary, with vertex colors)
  - JSON (camera poses)
  - MP4 (H.264 video)

## 🎨 Use Cases

### 1. VFX Integration
Export tracked points and cameras to integrate CGI elements into your footage with perfect tracking.

### 2. 3D Reconstruction
Use the dense point cloud to create detailed 3D models from monocular video.

### 3. Camera Tracking Analysis
Visualize and verify camera tracking data in Blender before final compositing.

### 4. Motion Capture
Export sparse trajectory points as motion capture data for animation reference.

## 🔧 Development

### Local Development (without Pinokio)

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies (in app/venv)
cd app
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Start the viewer server
node viewer_server.js 8080
```

### Project Structure
```
SpaTracker2-Viewer/
├── index.html                 # Web UI
├── viewer.js                  # Pinokio launcher
├── viewer_server.js           # Node.js server
├── export_ply.py              # PLY export script
├── blender_addon/
│   ├── import_spatracker2_ply.py
│   └── import_spatracker2_cameras.py
├── app/                       # SpaTracker2 core (3rd party)
│   ├── tapip3d_viz.py
│   └── viz.html
└── package.json
```

## 📄 License

This project is provided as-is for educational and research purposes.

## 🙏 Acknowledgments

- **SpaTracker2** - Original tracking system by Henry et al.
- **TAPIP3D** - 3D visualization framework
- **Pinokio** - One-click AI app launcher

## 🐛 Issues & Contributions

Found a bug or have a feature request? Please open an issue!

For contributions:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📬 Contact

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and community support

---

**Made with ❤️ for the VFX and 3D community**
