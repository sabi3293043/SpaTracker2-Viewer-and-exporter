"""
SpaTracker2 NPZ File Reader

This script reads SpaTracker2 NPZ files and displays information about the contents.
Can also export data to common formats.

Usage:
    python read_npz.py <path_to_npz_file> [--info] [--export] [--output-dir <dir>]
"""

import numpy as np
import argparse
import os
import json
from pathlib import Path


def read_npz_info(npz_path):
    """Read and display NPZ file information"""
    print(f"\n{'='*60}")
    print(f"SpaTracker2 NPZ File: {npz_path}")
    print(f"{'='*60}\n")
    
    data = np.load(npz_path)
    
    print("Available arrays:")
    print("-" * 40)
    
    for key in data.files:
        arr = data[key]
        print(f"  {key:20s}: shape={arr.shape}, dtype={arr.dtype}")
        
        # Show additional info for specific arrays
        if key == "extrinsics":
            print(f"                      -> Camera poses for {arr.shape[0]} frames")
        elif key == "intrinsics":
            print(f"                      -> Camera intrinsics ({'per-frame' if arr.shape[0] > 1 else 'single'})")
        elif key == "coords":
            print(f"                      -> {arr.shape[1]} trajectory points over {arr.shape[0]} frames")
        elif key == "video":
            print(f"                      -> {arr.shape[0]} frames, {arr.shape[2]}x{arr.shape[3]} resolution")
        elif key == "depths":
            print(f"                      -> Depth maps for {arr.shape[0]} frames")
    
    print()
    
    # Show sample data
    if "extrinsics" in data:
        ext = data["extrinsics"]
        print(f"Sample extrinsics (frame 0):")
        print(f"  Translation: {ext[0, :3, 3]}")
        print(f"  Rotation (first row): {ext[0, 0, :3]}")
        print()
    
    if "intrinsics" in data:
        intr = data["intrinsics"]
        if intr.ndim == 3:
            intr = intr[0] if intr.shape[0] == 1 else intr[0]  # Use first frame
        print(f"Sample intrinsics:")
        print(f"  Focal length (fx, fy): ({intr[0, 0].item():.2f}, {intr[1, 1].item():.2f})")
        print(f"  Principal point (cx, cy): ({intr[0, 2].item():.2f}, {intr[1, 2].item():.2f})")
        print()
    
    if "coords" in data:
        coords = data["coords"]
        print(f"Trajectory bounds:")
        print(f"  Min: {coords.min(axis=(0, 1))}")
        print(f"  Max: {coords.max(axis=(0, 1))}")
        print()
    
    data.close()
    
    return data


def export_to_json(npz_path, output_dir):
    """Export NPZ data to JSON format"""
    data = np.load(npz_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    export_data = {
        "metadata": {
            "source_file": str(npz_path),
            "arrays": {}
        }
    }
    
    for key in data.files:
        arr = data[key]
        export_data["metadata"]["arrays"][key] = {
            "shape": arr.shape,
            "dtype": str(arr.dtype)
        }
        
        # Export specific arrays as JSON
        if key in ["extrinsics", "intrinsics"]:
            export_data[key] = arr.tolist()
        elif key == "coords":
            # Export first and last frame trajectories as sample
            export_data[f"{key}_first_frame"] = arr[0].tolist()
            export_data[f"{key}_last_frame"] = arr[-1].tolist()
    
    output_path = output_dir / f"{Path(npz_path).stem}.json"
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"Exported to: {output_path}")
    data.close()


def export_cameras_to_csv(npz_path, output_dir):
    """Export camera positions to CSV"""
    data = np.load(npz_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if "extrinsics" not in data:
        print("No extrinsics found in NPZ file")
        return
    
    extrinsics = data["extrinsics"]
    
    output_path = output_dir / f"{Path(npz_path).stem}_cameras.csv"
    with open(output_path, 'w') as f:
        f.write("frame,tx,ty,tz,r00,r01,r02,r10,r11,r12,r20,r21,r22\n")
        for i, ext in enumerate(extrinsics):
            row = [i]
            row.extend(ext[:3, 3].tolist())  # Translation
            row.extend(ext[:3, :3].flatten().tolist())  # Rotation
            f.write(",".join(map(str, row)) + "\n")
    
    print(f"Exported cameras to: {output_path}")
    data.close()


def export_trajectories_to_csv(npz_path, output_dir):
    """Export trajectory points to CSV"""
    data = np.load(npz_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if "coords" not in data:
        print("No coords found in NPZ file")
        return
    
    coords = data["coords"]
    T, N, _ = coords.shape
    
    output_path = output_dir / f"{Path(npz_path).stem}_trajectories.csv"
    with open(output_path, 'w') as f:
        f.write("frame,point_id,x,y,z\n")
        for t in range(T):
            for n in range(N):
                f.write(f"{t},{n},{coords[t, n, 0]},{coords[t, n, 1]},{coords[t, n, 2]}\n")
    
    print(f"Exported trajectories to: {output_path}")
    data.close()


def main():
    parser = argparse.ArgumentParser(
        description="Read and export SpaTracker2 NPZ files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python read_npz.py results.npz --info
  python read_npz.py results.npz --export --output-dir ./export
  python read_npz.py results.npz --cameras-csv
  python read_npz.py results.npz --trajectories-csv
        """
    )
    
    parser.add_argument("npz_file", help="Path to the NPZ file")
    parser.add_argument("--info", action="store_true", help="Display NPZ file information")
    parser.add_argument("--export", action="store_true", help="Export data to JSON")
    parser.add_argument("--output-dir", default="./export", help="Output directory for exports")
    parser.add_argument("--cameras-csv", action="store_true", help="Export camera positions to CSV")
    parser.add_argument("--trajectories-csv", action="store_true", help="Export trajectories to CSV")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.npz_file):
        print(f"Error: File not found: {args.npz_file}")
        return
    
    # Default to showing info if no action specified
    if not any([args.info, args.export, args.cameras_csv, args.trajectories_csv]):
        args.info = True
    
    if args.info:
        read_npz_info(args.npz_file)
    
    if args.export:
        export_to_json(args.npz_file, args.output_dir)
    
    if args.cameras_csv:
        export_cameras_to_csv(args.npz_file, args.output_dir)
    
    if args.trajectories_csv:
        export_trajectories_to_csv(args.npz_file, args.output_dir)


if __name__ == "__main__":
    main()
