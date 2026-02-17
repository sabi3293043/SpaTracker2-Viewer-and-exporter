# SpaTracker2 Blender Addon
# Imports SpaTracker2 NPZ tracking data and visualizes it in Blender

bl_info = {
    "name": "SpaTracker2 Importer",
    "author": "SpaTracker2 Team",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "File > Import > SpaTracker2 (.npz)",
    "description": "Import SpaTracker2 tracking data and visualize camera poses and trajectories",
    "category": "Import-Export",
}

import bpy
import numpy as np
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Matrix
import os

# Use __package__ for Blender 5.0 extension system
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
    import_cameras: bpy.props.BoolProperty(
        name="Import Cameras",
        description="Create camera objects for each frame",
        default=True,
    )
    import_trajectories: bpy.props.BoolProperty(
        name="Import Trajectories",
        description="Create trajectory points and curves",
        default=True,
    )
    trajectory_scale: bpy.props.FloatProperty(
        name="Trajectory Scale",
        description="Scale factor for trajectory visualization",
        default=1.0,
        min=0.01,
        max=10.0,
    )
    camera_size: bpy.props.FloatProperty(
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
    # Create vertices for a camera frustum
    vertices = [
        (0, 0, 0),                          # Camera center
        (-size, -size, size),              # Bottom left front
        (size, -size, size),               # Bottom right front
        (size, size, size),                # Top right front
        (-size, size, size),               # Top left front
    ]
    
    # Create edges
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4),   # Lines from center to corners
        (1, 2), (2, 3), (3, 4), (4, 1),   # Front face
    ]
    
    mesh = bpy.data.meshes.new("CameraFrustum")
    mesh.from_pydata(vertices, edges, [])
    mesh.update()
    return mesh


def create_camera_object(frame_idx, extrinsic, intrinsics, img_width, img_height, camera_size):
    """Create a camera object for a single frame"""
    # Create mesh
    mesh = create_camera_mesh(camera_size)
    obj = bpy.data.objects.new(f"Camera_{frame_idx:04d}", mesh)
    
    # Calculate FOV from intrinsics
    fx = intrinsics[0, 0]
    fy = intrinsics[1, 1]
    fov_y = 2 * np.arctan(img_height / (2 * fy)) * (180 / np.pi)
    
    # Create camera data
    cam_data = bpy.data.cameras.new(f"Camera_{frame_idx:04d}")
    cam_data.lens_unit = 'FOV'
    cam_data.angle = np.radians(fov_y)
    
    # Set object data to camera
    obj.data = cam_data
    
    # Convert extrinsic matrix (world_from_cam) to Blender coordinate system
    # SpaTracker2 uses OpenCV convention (Y down, Z forward)
    # Blender uses Z up, -Y forward
    cv_to_blender = Matrix([
        [1, 0, 0, 0],
        [0, -1, 0, 0],
        [0, 0, -1, 0],
        [0, 0, 0, 1]
    ])
    
    # Convert 4x4 numpy array to Blender Matrix
    extrinsic_mat = Matrix(extrinsic.tolist())
    blender_mat = extrinsic_mat @ cv_to_blender
    
    obj.matrix_world = blender_mat
    
    return obj


def create_trajectory_objects(trajs, trajectory_scale):
    """Create trajectory visualization"""
    T, N, _ = trajs.shape  # T frames, N points
    
    # Create a collection for all trajectory points
    traj_collection = bpy.data.collections.new("Trajectories")
    bpy.context.scene.collection.children.link(traj_collection)
    
    # Create vertices for all trajectory points
    all_vertices = []
    vertex_indices = {}  # Map (frame, point_idx) to vertex index
    
    for t in range(T):
        for n in range(N):
            pt = trajs[t, n] * trajectory_scale
            vertex_indices[(t, n)] = len(all_vertices)
            all_vertices.append(tuple(pt))
    
    # Create mesh for trajectory points
    points_mesh = bpy.data.meshes.new("TrajectoryPoints")
    points_mesh.from_pydata(all_vertices, [], [])
    points_mesh.update()
    
    points_obj = bpy.data.objects.new("TrajectoryPoints", points_mesh)
    traj_collection.objects.link(points_obj)
    
    # Create edges connecting points across frames for each trajectory
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
        
        # Add skin modifier to make lines visible
        skin_mod = lines_obj.modifiers.new(name="Skin", type='SKIN')
        for vertex in lines_mesh.vertices:
            vertex.skin_vertices[0].radius = (0.002, 0.002)
    
    return traj_collection


def load_spatracker2_npz(context, filepath, import_cameras=True, import_trajectories=True, 
                         trajectory_scale=1.0, camera_size=0.1):
    """Main loading function"""
    
    # Load NPZ file
    data = np.load(filepath)
    
    # Get required data
    if "extrinsics" not in data:
        raise ValueError("NPZ file missing 'extrinsics' array")
    if "intrinsics" not in data:
        raise ValueError("NPZ file missing 'intrinsics' array")
    
    extrinsics = data["extrinsics"]
    intrinsics = data["intrinsics"]
    
    # Get optional data
    trajs = data.get("coords", None)
    video = data.get("video", None)
    
    # Get image dimensions from video if available
    if video is not None:
        T, C, H, W = video.shape
    else:
        T = extrinsics.shape[0]
        H, W = 192, 256  # Default dimensions
    
    # Create a collection for the import
    main_collection = bpy.data.collections.new("SpaTracker2_Import")
    bpy.context.scene.collection.children.link(main_collection)
    
    # Import cameras
    if import_cameras:
        camera_collection = bpy.data.collections.new("Cameras")
        main_collection.children.link(camera_collection)
        
        for frame_idx in range(T):
            # Use first intrinsics if only one, otherwise use per-frame
            if intrinsics.ndim == 3:
                intr = intrinsics[0] if intrinsics.shape[0] == 1 else intrinsics[frame_idx]
            else:
                intr = intrinsics
            
            ext = extrinsics[frame_idx]
            
            cam_obj = create_camera_object(
                frame_idx, ext, intr, W, H, camera_size
            )
            camera_collection.objects.link(cam_obj)
        
        context.view_layer.update()
    
    # Import trajectories
    if import_trajectories and trajs is not None:
        traj_collection = create_trajectory_objects(trajs, trajectory_scale)
        main_collection.children.link(traj_collection)
    
    # Set active object
    if main_collection.objects:
        context.view_layer.objects.active = main_collection.objects[0]
    
    # Report success
    info = []
    if import_cameras:
        info.append(f"{T} cameras")
    if import_trajectories and trajs is not None:
        info.append(f"{trajs.shape[1]} trajectories over {T} frames")
    
    context.window_manager.progress_end()
    bpy.ops.object.select_all(action='DESELECT')
    
    print(f"Successfully imported: {', '.join(info)}")
    return {'FINISHED'}


# Menu item
def menu_func_import(self, context):
    self.layout.operator(ImportSpaTracker2NPZ.bl_idname, text="SpaTracker2 (.npz)")


# Registration
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
