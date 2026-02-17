"""
SpaTracker2 PLY Export Script

Exports NPZ tracking data to animated PLY sequence with vertex colors.
Exports both trajectory points and dense point cloud from depth.

Usage:
    python export_ply.py <npz_file> <output_dir> [--fps <fps>] [--scale <scale>] [--color <source>]
    
Arguments:
    npz_file: Path to the input NPZ file
    output_dir: Directory to save PLY files
    --fps: Frame rate for the animation (default: 30)
    --scale: Scale factor for coordinates (default: 1.0)
    --color: Color source - video, depth, or white (default: video)
"""

import numpy as np
import argparse
import os
from pathlib import Path
from datetime import datetime


def write_ply_with_colors(filepath, vertices, colors):
    """
    Write PLY file with vertex colors.
    
    Args:
        filepath: Output PLY file path
        vertices: Nx3 array of vertex positions
        colors: Nx3 array of RGB colors (0-255)
    """
    with open(filepath, 'wb') as f:
        # Write header
        header = f"""ply
format binary_little_endian 1.0
element vertex {len(vertices)}
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
"""
        f.write(header.encode('ascii'))
        
        # Write vertex data
        for i, (v, c) in enumerate(zip(vertices, colors)):
            # Position (3 floats)
            f.write(np.array(v, dtype='<f4').tobytes())
            # Color (3 bytes)
            f.write(np.array(c, dtype='u1').tobytes())


def depth_to_color(depth, min_depth, max_depth):
    """Convert depth to colormap (matplotlib-like jet)."""
    # Normalize depth
    norm_depth = (depth - min_depth) / (max_depth - min_depth + 1e-8)
    norm_depth = np.clip(norm_depth, 0, 1)
    
    # Jet colormap
    r = np.clip(1.5 - 4 * np.abs(norm_depth - 0.75), 0, 1)
    g = np.clip(1.5 - 4 * np.abs(norm_depth - 0.5), 0, 1)
    b = np.clip(1.5 - 4 * np.abs(norm_depth - 0.25), 0, 1)
    
    return np.stack([r * 255, g * 255, b * 255], axis=-1).astype(np.uint8)


def depth_to_point_cloud(depth, intrinsics, color_source='video', video_frame=None, scale=1.0):
    """
    Convert depth map to 3D point cloud with colors.
    
    Args:
        depth: HxW depth map
        intrinsics: 3x3 camera intrinsics
        color_source: 'video', 'depth', or 'white'
        video_frame: Optional video frame for color
        scale: Scale factor
    
    Returns:
        vertices: Nx3 array of 3D points
        colors: Nx3 array of RGB colors
    """
    H, W = depth.shape
    fx, fy = intrinsics[0, 0], intrinsics[1, 1]
    cx, cy = intrinsics[0, 2], intrinsics[1, 2]
    
    # Create pixel grid
    y, x = np.indices((H, W))
    
    # Filter out zero depths
    valid_mask = depth > 0
    valid_count = valid_mask.sum()
    
    if valid_count == 0:
        return np.array([]).reshape(0, 3), np.array([]).reshape(0, 3)
    
    # Get valid pixels
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]
    z_valid = depth[valid_mask]
    
    # Convert to 3D coordinates (camera space)
    X = (x_valid - cx) * z_valid / fx
    Y = (y_valid - cy) * z_valid / fy
    Z = z_valid
    
    # Stack and scale
    vertices = np.stack([X, Y, Z], axis=-1) * scale
    
    # Get colors
    if color_source == 'video' and video_frame is not None:
        # Sample color from video frame
        if video_frame.max() <= 1.0:
            video_frame = (video_frame * 255).astype(np.uint8)
        
        # Handle different video frame formats
        if video_frame.ndim == 3:  # H, W, C or C, H, W
            if video_frame.shape[0] == 3:  # C, H, W
                colors = video_frame[:, y_valid, x_valid].T
            else:  # H, W, C
                colors = video_frame[y_valid, x_valid]
        else:
            colors = np.ones((valid_count, 3), dtype=np.uint8) * 255
    elif color_source == 'depth':
        # Use depth-based coloring
        colors = depth_to_color(z_valid, depth[valid_mask].min(), depth[valid_mask].max())
    else:
        # White points
        colors = np.ones((valid_count, 3), dtype=np.uint8) * 255
    
    return vertices, colors


def export_ply_sequence(npz_path, output_dir, fps=30, scale=1.0, color_source='video'):
    """
    Export NPZ data to PLY sequence.
    Exports both trajectory points and dense point clouds.
    
    Args:
        npz_path: Path to input NPZ file
        output_dir: Directory to save PLY files
        fps: Frame rate
        scale: Scale factor for coordinates
        color_source: 'video', 'depth', or 'white'
    """
    print(f"Loading NPZ file: {npz_path}")
    data = np.load(npz_path)
    
    # Extract data
    coords = data.get('coords', None)  # Trajectory points
    video = data.get('video', None)
    depths = data.get('depths', None)
    intrinsics = data.get('intrinsics', None)
    visibs = data.get('visibs', None)
    
    if depths is None and coords is None:
        raise ValueError("NPZ file missing both 'coords' and 'depths' arrays")
    
    # Determine number of frames
    if depths is not None:
        T = depths.shape[0]
    else:
        T = coords.shape[0]
    
    print(f"Found {T} frames")
    
    # Process output directories
    output_dir = Path(output_dir)
    trajectory_dir = output_dir / 'trajectory'
    pointcloud_dir = output_dir / 'pointcloud'
    
    trajectory_dir.mkdir(parents=True, exist_ok=True)
    pointcloud_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare video colors if needed
    video_colors = None
    if color_source == 'video' and video is not None:
        print("Processing video frames...")
        video_colors = []
        for t in range(T):
            frame = video[t]
            if frame.max() <= 1.0:
                frame = (frame * 255).astype(np.uint8)
            # Reshape to H, W, C if needed
            if frame.ndim == 3 and frame.shape[0] == 3:
                frame = np.transpose(frame, (1, 2, 0))
            video_colors.append(frame)
    
    # Get intrinsics
    if intrinsics is not None:
        if intrinsics.ndim == 3:
            intr = intrinsics[0] if intrinsics.shape[0] == 1 else intrinsics[0]
        else:
            intr = intrinsics
    else:
        # Default intrinsics
        intr = np.array([[256, 0, 128], [0, 256, 96], [0, 0, 1]])
    
    # Export trajectory points
    if coords is not None:
        N = coords.shape[1]
        print(f"Exporting {T} frames of trajectory ({N} points per frame)...")
        
        for t in range(T):
            frame_coords = coords[t] * scale
            
            # Get colors
            if color_source == 'video' and video_colors is not None:
                # Use average color from video frame
                avg_color = video_colors[t].mean(axis=(0, 1)).astype(np.uint8)
                colors = np.tile(avg_color, (N, 1))
            elif color_source == 'depth':
                frame_colors = depth_to_color(frame_coords[:, 2], coords[:,:,2].min()*scale, coords[:,:,2].max()*scale)
                colors = frame_colors
            else:
                colors = np.ones((N, 3), dtype=np.uint8) * 255
            
            # Apply visibility mask if available
            if visibs is not None:
                vis_mask = visibs[t].flatten() > 0.5
                if len(vis_mask) == len(frame_coords):
                    frame_coords = frame_coords[vis_mask]
                    colors = colors[vis_mask]
            
            # Write PLY file
            ply_path = trajectory_dir / f"frame_{t:06d}.ply"
            write_ply_with_colors(ply_path, frame_coords, colors)
            
            progress = int((t + 1) / T * 50)
            print(f"Trajectory Progress: {progress}%")
    
    # Export dense point clouds from depth
    if depths is not None:
        print(f"Exporting {T} frames of dense point cloud...")
        
        for t in range(T):
            depth_frame = depths[t]
            
            # Get video frame for color
            video_frame = video_colors[t] if video_colors is not None else None
            
            # Convert depth to point cloud
            vertices, colors = depth_to_point_cloud(
                depth_frame, intr, 
                color_source=color_source, 
                video_frame=video_frame,
                scale=scale
            )
            
            if len(vertices) > 0:
                # Write PLY file
                ply_path = pointcloud_dir / f"frame_{t:06d}.ply"
                write_ply_with_colors(ply_path, vertices, colors)
            
            progress = 50 + int((t + 1) / T * 50)
            print(f"Point Cloud Progress: {progress}%")
    
    data.close()
    
    # Write metadata
    metadata = {
        'fps': fps,
        'scale': scale,
        'color_source': color_source,
        'total_frames': T,
        'export_time': datetime.now().isoformat()
    }
    
    if coords is not None:
        metadata['trajectory_points'] = coords.shape[1]
    
    import json
    with open(output_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Export complete! PLY files saved to {output_dir}")
    print(f"  - Trajectory: {trajectory_dir}")
    print(f"  - Point Cloud: {pointcloud_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Export SpaTracker2 NPZ to PLY sequence",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("npz_file", help="Path to input NPZ file")
    parser.add_argument("output_dir", help="Directory to save PLY files")
    parser.add_argument("--fps", type=int, default=30, help="Frame rate (default: 30)")
    parser.add_argument("--scale", type=float, default=1.0, help="Scale factor (default: 1.0)")
    parser.add_argument("--color", type=str, default="video", 
                        choices=["video", "depth", "white"],
                        help="Color source (default: video)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.npz_file):
        print(f"Error: File not found: {args.npz_file}")
        return 1
    
    try:
        export_ply_sequence(
            args.npz_file,
            args.output_dir,
            fps=args.fps,
            scale=args.scale,
            color_source=args.color
        )
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
