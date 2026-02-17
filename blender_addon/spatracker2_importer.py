# SpaTracker2 Blender Addon
# Imports SpaTracker2 NPZ tracking data and visualizes it in Blender
# Works with Blender 4.x and 5.x (legacy addon mode)

bl_info = {
    "name": "SpaTracker2 Importer",
    "author": "SpaTracker2 Team",
    "version": (1, 0, 1),
    "blender": (4, 0, 0),
    "location": "File > Import > SpaTracker2 (.npz)",
    "description": "Import SpaTracker2 tracking data and visualize camera poses and trajectories",
    "category": "Import-Export",
}

import bpy
import numpy as np
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Matrix
import os


class ImportSpaTracker2NPZ(bpy.types.Operator, ImportHelper):
    """Import SpaTracker2 NPZ tracking data"""
    bl_idname = "import_scene.spatracker2_npz"
    bl_label = "Import SpaTracker2 NPZ"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".npz"
    filter_glob: StringProperty(
        default="*.npz",
        options={'HIDDEN'},
    )

    # Options
    import_cameras: BoolProperty(
        name="Import Cameras",
        description="Create camera objects for each frame",
        default=True,
    )
    import_trajectories: BoolProperty(
        name="Import Trajectories",
        description="Create trajectory points and curves",
        default=True,
    )
    import_video: BoolProperty(
        name="Import Video",
        description="Import video file as reference for camera background",
        default=True,
    )
    trajectory_scale: FloatProperty(
        name="Trajectory Scale",
        description="Scale factor for trajectory visualization",
        default=1.0,
        min=0.01,
        max=10.0,
    )
    camera_size: FloatProperty(
        name="Camera Size",
        description="Size of camera visualization",
        default=0.1,
        min=0.001,
        max=10.0,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(heading="Import Options")
        col.prop(self, "import_cameras")
        col.prop(self, "import_trajectories")
        col.prop(self, "import_video")
        
        if self.import_trajectories:
            col.prop(self, "trajectory_scale")
        
        if self.import_cameras:
            col.prop(self, "camera_size")

    def execute(self, context):
        try:
            return load_spatracker2_npz(
                context,
                self.filepath,
                import_cameras=self.import_cameras,
                import_trajectories=self.import_trajectories,
                trajectory_scale=self.trajectory_scale,
                camera_size=self.camera_size,
            )
        except Exception as e:
            self.report({'ERROR'}, f"Error importing file: {str(e)}")
            return {'CANCELLED'}


def create_camera_mesh(size=0.1):
    """Create a camera frustum mesh"""
    vertices = [
        (0, 0, 0),
        (-size, -size, size),
        (size, -size, size),
        (size, size, size),
        (-size, size, size),
    ]
    
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4),
        (1, 2), (2, 3), (3, 4), (4, 1),
    ]
    
    mesh = bpy.data.meshes.new("CameraFrustum")
    mesh.from_pydata(vertices, edges, [])
    mesh.update()
    return mesh


def create_camera_object(frame_idx, extrinsic, intrinsics, img_width, img_height, camera_size):
    """Create a camera object for a single frame"""
    # Create actual camera data
    cam_data = bpy.data.cameras.new(f"Camera_{frame_idx:04d}")
    
    # Calculate FOV from intrinsics
    fx = intrinsics[0, 0]
    fy = intrinsics[1, 1]
    fov_y = 2 * np.arctan(img_height / (2 * fy)) * (180 / np.pi)
    
    cam_data.lens_unit = 'FOV'
    cam_data.angle = np.radians(fov_y)
    
    # Create object with camera data
    obj = bpy.data.objects.new(f"Camera_{frame_idx:04d}", cam_data)
    
    # Convert extrinsic matrix (world_from_cam) to Blender coordinate system
    # SpaTracker2 uses OpenCV convention (Y down, Z forward)
    # Blender uses Z up, -Y forward
    cv_to_blender = Matrix([
        [1, 0, 0, 0],
        [0, -1, 0, 0],
        [0, 0, -1, 0],
        [0, 0, 0, 1]
    ])
    
    extrinsic_mat = Matrix(extrinsic.tolist())
    blender_mat = extrinsic_mat @ cv_to_blender
    
    obj.matrix_world = blender_mat
    
    # Add visual frustum display
    obj.data.show_limits = True
    obj.data.clip_end = 100.0
    
    return obj


def create_trajectory_objects(trajs, trajectory_scale):
    """Create trajectory visualization"""
    T, N, _ = trajs.shape
    
    traj_collection = bpy.data.collections.new("Trajectories")
    bpy.context.scene.collection.children.link(traj_collection)
    
    all_vertices = []
    
    for t in range(T):
        for n in range(N):
            pt = trajs[t, n] * trajectory_scale
            all_vertices.append(tuple(pt))
    
    points_mesh = bpy.data.meshes.new("TrajectoryPoints")
    points_mesh.from_pydata(all_vertices, [], [])
    points_mesh.update()
    
    points_obj = bpy.data.objects.new("TrajectoryPoints", points_mesh)
    traj_collection.objects.link(points_obj)
    
    edge_vertices = []
    edges = []
    
    for n in range(N):
        for t in range(T - 1):
            v1_idx = len(edge_vertices)
            v2_idx = len(edge_vertices) + 1
            edge_vertices.append(tuple(trajs[t, n] * trajectory_scale))
            edge_vertices.append(tuple(trajs[t + 1, n] * trajectory_scale))
            edges.append((v1_idx, v2_idx))
    
    if edge_vertices:
        lines_mesh = bpy.data.meshes.new("TrajectoryLines")
        lines_mesh.from_pydata(edge_vertices, edges, [])
        lines_mesh.update()
        
        lines_obj = bpy.data.objects.new("TrajectoryLines", lines_mesh)
        traj_collection.objects.link(lines_obj)
        
        skin_mod = lines_obj.modifiers.new(name="Skin", type='SKIN')
        for vertex in lines_mesh.vertices:
            vertex.skin_vertices[0].radius = (0.002, 0.002)
    
    return traj_collection


def find_video_file(npz_filepath):
    """Find video file in the parent folder of the NPZ file"""
    from pathlib import Path
    
    npz_path = Path(npz_filepath)
    parent_folder = npz_path.parent
    
    # Common video extensions
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v']
    
    # Look for video files in the parent folder
    for ext in video_extensions:
        for video_file in parent_folder.glob(f'*{ext}'):
            return str(video_file)
    
    return None


def import_video_as_background(video_path, context):
    """Import video and set it up as background for camera view"""
    from pathlib import Path
    
    # Load video into VSE
    scene = context.scene
    if not scene.sequence_editor:
        scene.sequence_editor_create()
    
    vse = scene.sequence_editor
    
    # Add video strip
    video_name = Path(video_path).stem
    strip = vse.sequences.new_movie(
        name=video_name,
        filepath=video_path,
        channel=1,
        frame_start=1
    )
    
    # Set frame range to match video
    scene.frame_start = 1
    scene.frame_end = int(strip.frame_final_duration)
    scene.frame_current = 1
    
    # Set resolution to match video
    scene.render.resolution_x = strip.frame_width
    scene.render.resolution_y = strip.frame_height
    scene.render.resolution_percentage = 100
    
    return strip


def setup_camera_background(context, video_strip):
    """Setup camera to show video in background"""
    scene = context.scene
    camera = scene.camera
    
    if camera:
        # Enable background images for the camera
        bg = camera.data.background_images.new()
        bg.source = 'IMAGE'
        
        # Create image from video
        # Note: Blender doesn't directly support video as camera BG
        # We'll use the VSE preview instead
        pass
    
    # Set view to camera view
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # Set region to camera view
                    if area.regions:
                        for region in area.regions:
                            if region.type == 'WINDOW':
                                override = {
                                    'area': area,
                                    'region': region,
                                    'scene': scene,
                                    'screen': context.screen,
                                    'window': context.window
                                }
                                bpy.ops.view3d.view_camera(override)
                                break


def load_spatracker2_npz(context, filepath, import_cameras=True, import_trajectories=True, 
                         import_video=True, trajectory_scale=1.0, camera_size=0.1):
    """Main loading function"""
    
    data = np.load(filepath)
    
    if "extrinsics" not in data:
        raise ValueError("NPZ file missing 'extrinsics' array")
    if "intrinsics" not in data:
        raise ValueError("NPZ file missing 'intrinsics' array")
    
    extrinsics = data["extrinsics"]
    intrinsics = data["intrinsics"]
    
    trajs = data.get("coords", None)
    video_data = data.get("video", None)
    
    if video_data is not None:
        T, C, H, W = video_data.shape
    else:
        T = extrinsics.shape[0]
        H, W = 192, 256
    
    main_collection = bpy.data.collections.new("SpaTracker2_Import")
    bpy.context.scene.collection.children.link(main_collection)
    
    # Import video first if enabled
    video_strip = None
    if import_video:
        video_path = find_video_file(filepath)
        if video_path:
            try:
                video_strip = import_video_as_background(video_path, context)
                print(f"Imported video: {video_path}")
            except Exception as e:
                print(f"Warning: Could not import video: {e}")
        else:
            print("Warning: No video file found in the same folder as NPZ")
    
    if import_cameras:
        camera_collection = bpy.data.collections.new("Cameras")
        main_collection.children.link(camera_collection)
        
        for frame_idx in range(T):
            if intrinsics.ndim == 3:
                intr = intrinsics[0] if intrinsics.shape[0] == 1 else intrinsics[frame_idx]
            else:
                intr = intrinsics
            
            ext = extrinsics[frame_idx]
            cam_obj = create_camera_object(frame_idx, ext, intr, W, H, camera_size)
            camera_collection.objects.link(cam_obj)
        
        # Set first camera as active
        if camera_collection.objects:
            context.scene.camera = camera_collection.objects[0]
            context.view_layer.update()
    
    if import_trajectories and trajs is not None:
        traj_collection = create_trajectory_objects(trajs, trajectory_scale)
        main_collection.children.link(traj_collection)
    
    if main_collection.objects:
        context.view_layer.objects.active = main_collection.objects[0]
    
    info = []
    if import_cameras:
        info.append(f"{T} cameras")
    if import_trajectories and trajs is not None:
        info.append(f"{trajs.shape[1]} trajectories over {T} frames")
    if video_strip:
        info.append("video imported")
    
    bpy.ops.object.select_all(action='DESELECT')
    
    print(f"Successfully imported: {', '.join(info)}")
    return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportSpaTracker2NPZ.bl_idname, text="SpaTracker2 (.npz)")


classes = (
    ImportSpaTracker2NPZ,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
