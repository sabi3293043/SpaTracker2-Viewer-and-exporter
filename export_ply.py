"""
SpaTracker2 PLY Export Script

Exports NPZ tracking data to animated PLY sequence with vertex colors.
Each frame is exported as a separate PLY file.

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


def export_ply_sequence(npz_path, output_dir, fps=30, scale=1.0, color_source='video'):
    """
    Export NPZ data to PLY sequence.
    
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
    coords = data.get('coords', None)
    video = data.get('video', None)
    depths = data.get('depths', None)
    visibs = data.get('visibs', None)
    
    if coords is None:
        raise ValueError("NPZ file missing 'coords' array")
    
    T, N, _ = coords.shape
    print(f"Found {T} frames with {N} trajectory points")
    
    # Prepare output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process video for colors if needed
    if color_source == 'video' and video is not None:
        print("Extracting colors from video...")
        # Video is (T, C, H, W), need to sample at trajectory projected positions
        # For simplicity, we'll use the mean color per frame
        video_colors = []
        for t in range(T):
            frame = video[t]
            if frame.max() <= 1.0:
                frame = (frame * 255).astype(np.uint8)
            # Get average color
            avg_color = frame.mean(axis=(1, 2)).astype(np.uint8)
            video_colors.append(avg_color)
        video_colors = np.array(video_colors)  # (T, 3)
    
    # Process depth for colors if needed
    if color_source == 'depth' and depths is not None:
        print("Extracting colors from depth...")
        min_d = depths.min()
        max_d = depths.max()
    
    # Export each frame
    print(f"Exporting {T} frames to {output_dir}...")
    
    for t in range(T):
        # Get coordinates for this frame
        frame_coords = coords[t] * scale
        
        # Get colors
        if color_source == 'video' and video is not None:
            # Use the same color for all points in this frame
            colors = np.tile(video_colors[t], (N, 1))
        elif color_source == 'depth' and depths is not None:
            # Sample depth at trajectory points and convert to color
            # For simplicity, use Z coordinate for depth coloring
            frame_colors = depth_to_color(frame_coords[:, 2], min_d * scale, max_d * scale)
            colors = frame_colors
        else:
            # White points
            colors = np.ones((N, 3), dtype=np.uint8) * 255
        
        # Apply visibility mask if available
        if visibs is not None:
            vis_mask = visibs[t] > 0.5
            frame_coords = frame_coords[vis_mask]
            colors = colors[vis_mask]
        
        # Write PLY file
        ply_path = output_dir / f"frame_{t:06d}.ply"
        write_ply_with_colors(ply_path, frame_coords, colors)
        
        # Progress
        progress = int((t + 1) / T * 100)
        print(f"Progress: {progress}%")
    
    data.close()
    
    # Write metadata
    metadata = {
        'fps': fps,
        'scale': scale,
        'color_source': color_source,
        'total_frames': T,
        'num_points': N,
        'export_time': datetime.now().isoformat()
    }
    
    import json
    with open(output_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Export complete! {T} PLY files saved to {output_dir}")


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
