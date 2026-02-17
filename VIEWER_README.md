# External NPZ Viewer

This viewer allows you to upload and visualize `.npz` tracking result files from SpaTracker2 or compatible sources.

## Features

- **Drag & Drop Upload**: Simply drag your `.npz` file onto the upload area
- **Interactive 3D Visualization**: View tracked points, camera trajectory, and depth data
- **Real-time Processing**: Files are converted and displayed immediately
- **No Server Required**: The viewer runs locally in your browser

## How to Use

1. Click on the "External NPZ Viewer" button in Pinokio
2. Wait for the viewer server to start
3. Upload your `.npz` file:
   - Drag and drop the file onto the upload area, or
   - Click "Choose File" and browse to your file
4. Wait for processing (conversion to visualization format)
5. Interact with the 3D viewer:
   - **Left Click + Drag**: Rotate camera
   - **Right Click + Drag**: Pan camera
   - **Scroll**: Zoom in/out
   - **Play/Pause**: Control video playback
   - **Timeline**: Scrub through frames

## Supported File Format

The viewer accepts `.npz` files containing:
- `video`: RGB video frames (T, C, H, W)
- `depths`: Depth maps (T, H, W)
- `extrinsics`: Camera extrinsic matrices (T, 4, 4)
- `intrinsics`: Camera intrinsic matrices (T, 3, 3)
- `coords`: 3D tracked point coordinates (T, N, 3)
- `visibs`: Visibility masks (optional)
- `conf`: Confidence data (optional)

## Controls

### Playback Controls
- **Play/Pause**: Toggle video playback
- **Speed**: Adjust playback speed (1x, 2x, 4x)
- **Timeline**: Jump to specific frame

### Visualization Settings
- **Point Size**: Adjust point cloud point size
- **Point Opacity**: Control point transparency
- **Max Depth**: Set maximum visualization depth
- **Show Trajectory**: Toggle trajectory visualization
- **Visual-Rich Trail**: Enable advanced trail rendering
- **Line Width**: Adjust trajectory line thickness
- **Ball Size**: Control trajectory point marker size
- **History Frames**: Number of frames to show in trail
- **Show Camera Frustum**: Display camera position indicators
- **Frustum Size**: Adjust camera indicator size
- **Keep History**: Enable historical frame retention
- **White Background**: Toggle background color

## Troubleshooting

### File Upload Fails
- Ensure the file has a `.npz` extension
- Check that the file is not corrupted
- Verify the file contains the required arrays

### Visualization Not Loading
- Check the browser console for errors
- Ensure Python and required dependencies are installed
- Try refreshing the page

### Performance Issues
- Reduce the number of trajectory points in settings
- Lower the history frames count
- Use smaller resolution input files

## File Storage

Uploaded files are stored in:
- **Uploads**: `uploads/` folder (original NPZ files)
- **Processed**: `processed/` folder (converted visualization files)

You can manually delete these folders to clear uploaded files.
