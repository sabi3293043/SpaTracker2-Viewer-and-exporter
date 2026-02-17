# SpaTracker2 PLY Sequence Importer
# Imports animated PLY sequence from SpaTracker2 export
# Works with Blender 4.x and 5.x

bl_info = {
    "name": "SpaTracker2 PLY Sequence Importer",
    "author": "SpaTracker2 Team",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "File > Import > SpaTracker2 PLY Sequence (.ply)",
    "description": "Import SpaTracker2 animated PLY sequence with vertex colors",
    "category": "Import-Export",
}

import bpy
import numpy as np
from bpy.props import StringProperty, FloatProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper
from pathlib import Path
import json
import struct


class ImportSpaTracker2PLY(bpy.types.Operator, ImportHelper):
    """Import SpaTracker2 PLY Sequence"""
    bl_idname = "import_scene.spatracker2_ply"
    bl_label = "Import SpaTracker2 PLY Sequence"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".ply"
    filter_glob: StringProperty(
        default="*.ply",
        options={'HIDDEN'},
    )
    
    filter_folder: BoolProperty(
        name="Filter Folders",
        default=True,
        options={'HIDDEN'}
    )

    # Options
    frame_start: FloatProperty(
        name="Start Frame",
        description="Starting frame number",
        default=1,
        min=1
    )
    
    scale: FloatProperty(
        name="Scale",
        description="Scale factor for coordinates",
        default=1.0,
        min=0.001,
        max=100.0
    )
    
    use_vertex_colors: BoolProperty(
        name="Use Vertex Colors",
        description="Import vertex colors",
        default=True
    )
    
    create_particles: BoolProperty(
        name="Create Particle System",
        description="Create particle system for points",
        default=False
    )
    
    point_size: FloatProperty(
        name="Point Size",
        description="Size of points (for particle system)",
        default=0.01,
        min=0.001,
        max=1.0
    )

    import_cameras: BoolProperty(
        name="Import Cameras",
        description="Import camera objects from cameras folder",
        default=True
    )

    camera_size: FloatProperty(
        name="Camera Size",
        description="Size of camera visualization",
        default=0.1,
        min=0.001,
        max=10.0
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(heading="Import Options")
        col.prop(self, "frame_start")
        col.prop(self, "scale")
        col.prop(self, "use_vertex_colors")
        col.prop(self, "import_cameras")
        col.prop(self, "create_particles")

        if self.create_particles:
            col.prop(self, "point_size")
        
        if self.import_cameras:
            col.prop(self, "camera_size")

    def execute(self, context):
        try:
            return import_ply_sequence(
                context,
                self.filepath,
                frame_start=int(self.frame_start),
                scale=self.scale,
                use_vertex_colors=self.use_vertex_colors,
                create_particles=self.create_particles,
                point_size=self.point_size,
                import_cameras=self.import_cameras,
                camera_size=self.camera_size
            )
        except Exception as e:
            self.report({'ERROR'}, f"Error importing: {str(e)}")
            return {'CANCELLED'}


def parse_ply_file(filepath):
    """Parse a PLY file and return vertices and colors."""
    vertices = []
    colors = []
    
    with open(filepath, 'rb') as f:
        # Read header
        header_lines = []
        while True:
            line = f.readline().decode('ascii').strip()
            if line == 'end_header':
                break
            header_lines.append(line)
        
        # Parse header
        num_vertices = 0
        has_color = False
        
        for line in header_lines:
            if line.startswith('element vertex'):
                num_vertices = int(line.split()[-1])
            elif line.startswith('property uchar red'):
                has_color = True
        
        # Read vertex data
        for i in range(num_vertices):
            # Read 3 floats (position)
            x = struct.unpack('<f', f.read(4))[0]
            y = struct.unpack('<f', f.read(4))[0]
            z = struct.unpack('<f', f.read(4))[0]
            vertices.append((x, y, z))
            
            # Read 3 bytes (color)
            if has_color:
                r = struct.unpack('B', f.read(1))[0]
                g = struct.unpack('B', f.read(1))[0]
                b = struct.unpack('B', f.read(1))[0]
                colors.append((r / 255.0, g / 255.0, b / 255.0, 1.0))
            else:
                colors.append((1.0, 1.0, 1.0, 1.0))
    
    return np.array(vertices), np.array(colors)


def create_point_cloud_object(name, vertices, colors, use_vertex_colors=True):
    """Create a point cloud object from vertices."""
    # Create mesh
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    
    # Add to collection
    bpy.context.collection.objects.link(obj)
    
    # Create mesh from vertices
    mesh.from_pydata(vertices, [], [])
    mesh.update()
    
    # Add vertex colors
    if use_vertex_colors and len(colors) == len(vertices):
        color_attr = mesh.color_attributes.new(
            name="Col",
            domain='CORNER',
            type='BYTE_COLOR'
        )
        
        # Set colors for each corner
        for i, color in enumerate(colors):
            if i < len(color_attr.data):
                color_attr.data[i].color = color
    
    return obj


def find_ply_sequence(first_frame_path):
    """Find all PLY files in the sequence."""
    folder = Path(first_frame_path).parent
    
    # Find all PLY files
    ply_files = sorted(folder.glob("frame_*.ply"))
    
    if not ply_files:
        # Try any PLY files
        ply_files = sorted(folder.glob("*.ply"))
    
    return ply_files


def load_metadata(folder):
    """Load metadata from JSON file."""
    meta_path = folder / 'metadata.json'
    if meta_path.exists():
        with open(meta_path, 'r') as f:
            return json.load(f)
    return None


def import_cameras_from_folder(context, cameras_folder, frame_start, fps, camera_size, parent_collection):
    """Import camera objects from JSON files."""
    import mathutils
    
    # Create camera collection
    cam_collection = bpy.data.collections.new("Cameras")
    parent_collection.children.link(cam_collection)
    
    # Find all camera JSON files
    cam_files = sorted(cameras_folder.glob("camera_*.json"))
    
    if not cam_files:
        print("  No camera files found")
        return
    
    print(f"Importing {len(cam_files)} cameras...")
    
    # Create camera objects
    cam_objects = []
    
    for i, cam_file in enumerate(cam_files):
        with open(cam_file, 'r') as f:
            cam_data = json.load(f)
        
        # Create camera data
        cam = bpy.data.cameras.new(f"Camera_{i:04d}")
        cam_obj = bpy.data.objects.new(f"Camera_{i:04d}", cam)
        cam_collection.objects.link(cam_obj)
        
        # Set intrinsics (focal length)
        intrinsics = cam_data.get('intrinsics', [])
        width = cam_data.get('width', 256)
        height = cam_data.get('height', 192)
        
        if len(intrinsics) >= 3:
            fx = intrinsics[0][0]
            fy = intrinsics[1][1]
            
            # Calculate sensor size and focal length
            cam.sensor_width = 32  # Default sensor width in mm
            cam.lens = fx / width * cam.sensor_width * 1000  # Convert to mm
        
        # Set extrinsics (pose)
        extrinsics = cam_data.get('extrinsics', [])
        if len(extrinsics) == 4 and len(extrinsics[0]) == 4:
            # Convert to Blender matrix
            # SpaTracker2 uses OpenCV convention (Y down, Z forward)
            # Blender uses Z up, -Y forward
            cv_to_blender = mathutils.Matrix([
                [1, 0, 0, 0],
                [0, -1, 0, 0],
                [0, 0, -1, 0],
                [0, 0, 0, 1]
            ])
            
            ext_mat = mathutils.Matrix(extrinsics)
            blender_mat = ext_mat @ cv_to_blender
            cam_obj.matrix_world = blender_mat
        
        # Set camera size for visualization
        cam_obj.scale = (camera_size, camera_size, camera_size)
        
        # Set visibility keyframes (same as PLY objects)
        current_frame = frame_start + i
        
        cam_obj.hide_viewport = True
        cam_obj.hide_render = True
        cam_obj.keyframe_insert(data_path="hide_viewport", frame=current_frame - 0.5)
        cam_obj.keyframe_insert(data_path="hide_render", frame=current_frame - 0.5)
        
        cam_obj.hide_viewport = False
        cam_obj.hide_render = False
        cam_obj.keyframe_insert(data_path="hide_viewport", frame=current_frame)
        cam_obj.keyframe_insert(data_path="hide_render", frame=current_frame)
        
        cam_obj.hide_viewport = True
        cam_obj.hide_render = True
        cam_obj.keyframe_insert(data_path="hide_viewport", frame=current_frame + 0.5)
        cam_obj.keyframe_insert(data_path="hide_render", frame=current_frame + 0.5)
        
        cam_objects.append(cam_obj)
    
    # Set first camera as active
    if cam_objects:
        context.scene.camera = cam_objects[0]
    
    print(f"  Imported {len(cam_objects)} cameras")


def import_ply_sequence(context, filepath, frame_start=1, scale=1.0,
                        use_vertex_colors=True, create_particles=False,
                        point_size=0.01, import_cameras=True, camera_size=0.1):
    """Main import function."""

    filepath = Path(filepath)
    folder = filepath.parent

    # Find PLY sequence
    ply_files = find_ply_sequence(filepath)

    if not ply_files:
        raise ValueError(f"No PLY files found in {folder}")

    print(f"Found {len(ply_files)} PLY files")

    # Load metadata
    metadata = load_metadata(folder)
    fps = metadata.get('fps', 30) if metadata else 30

    # Create collection
    collection = bpy.data.collections.new("SpaTracker2_Points")
    context.scene.collection.children.link(collection)

    # Set scene frame range
    context.scene.frame_start = frame_start
    context.scene.frame_end = frame_start + len(ply_files) - 1
    context.scene.render.fps = fps

    # Import cameras if available
    if import_cameras:
        cameras_folder = folder / 'cameras'
        if cameras_folder.exists():
            import_cameras_from_folder(context, cameras_folder, frame_start, fps, camera_size, collection)
    context.scene.render.fps = fps
    
    # Create objects for each frame
    objects = []
    
    for i, ply_path in enumerate(ply_files):
        print(f"Importing {ply_path.name}...")
        
        # Parse PLY
        vertices, colors = parse_ply_file(str(ply_path))
        
        if len(vertices) == 0:
            print(f"  Warning: No vertices in {ply_path.name}")
            continue
        
        # Apply scale
        vertices = vertices * scale
        
        # Create object
        obj = create_point_cloud_object(
            f"Points_{i:04d}",
            vertices,
            colors,
            use_vertex_colors=use_vertex_colors
        )
        
        # Add to collection
        collection.objects.link(obj)

        # Set visibility keyframes - show only for this single frame
        current_frame = frame_start + i
        
        # Start hidden
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_viewport", frame=current_frame - 0.5)
        obj.keyframe_insert(data_path="hide_render", frame=current_frame - 0.5)
        
        # Show at this frame
        obj.hide_viewport = False
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_viewport", frame=current_frame)
        obj.keyframe_insert(data_path="hide_render", frame=current_frame)
        
        # Hide again at next frame
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_viewport", frame=current_frame + 0.5)
        obj.keyframe_insert(data_path="hide_render", frame=current_frame + 0.5)

        objects.append(obj)
    
    # Create empty to hold all objects
    empty = bpy.data.objects.new("SpaTracker2_Animation", None)
    collection.objects.link(empty)
    
    # Parent all objects to empty
    for obj in objects:
        obj.parent = empty
    
    # Select the empty
    bpy.ops.object.select_all(action='DESELECT')
    empty.select_set(True)
    context.view_layer.objects.active = empty
    
    print(f"Imported {len(objects)} frames")
    print(f"Frame rate: {fps} FPS")
    
    return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportSpaTracker2PLY.bl_idname, text="SpaTracker2 PLY Sequence (.ply)")


classes = (
    ImportSpaTracker2PLY,
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
