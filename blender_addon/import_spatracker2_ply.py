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

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(heading="Import Options")
        col.prop(self, "frame_start")
        col.prop(self, "scale")
        col.prop(self, "use_vertex_colors")
        col.prop(self, "create_particles")
        
        if self.create_particles:
            col.prop(self, "point_size")

    def execute(self, context):
        try:
            return import_ply_sequence(
                context,
                self.filepath,
                frame_start=int(self.frame_start),
                scale=self.scale,
                use_vertex_colors=self.use_vertex_colors,
                create_particles=self.create_particles,
                point_size=self.point_size
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


def import_ply_sequence(context, filepath, frame_start=1, scale=1.0, 
                        use_vertex_colors=True, create_particles=False, 
                        point_size=0.01):
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
