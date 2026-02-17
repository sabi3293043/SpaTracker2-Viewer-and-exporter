SpaTracker2 PLY Export
======================

This folder contains animated 3D point tracking data exported from SpaTracker2.

Files:
- ply_files/: Sequence of PLY files (one per frame)
- import_spatracker2_ply.py: Blender import script

To import in Blender:
1. Open Blender
2. Go to File > Import > SpaTracker2 PLY Sequence (.ply)
3. Navigate to the ply_files folder
4. Select the first PLY file (frame_000000.ply)
5. Click "Import"

The importer will automatically:
- Load all PLY files in sequence
- Create point cloud objects with vertex colors
- Set up animation keyframes
- Match the original frame rate (30 FPS)

Frame Rate: 30 FPS
Scale: 1x
Color Source: video
