# SpaTracker2 Camera Sequence Importer
# Imports camera poses from JSON files exported by SpaTracker2
# Works with Blender 4.x and 5.x

bl_info = {
    "name": "SpaTracker2 Camera Importer",
    "author": "SpaTracker2 Team",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "File > Import > SpaTracker2 Camera Sequence (.json)",
    "description": "Import SpaTracker2 camera sequence from JSON files",
    "category": "Import-Export",
}

import bpy
import json
import mathutils
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ImportHelper
from pathlib import Path


class ImportSpaTracker2Cameras(bpy.types.Operator, ImportHelper):
    """Import SpaTracker2 Camera Sequence"""
    bl_idname = "import_scene.spatracker2_cameras"
    bl_label = "Import SpaTracker2 Camera Sequence"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".json"
    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )

    # Options
    frame_start: IntProperty(
        name="Start Frame",
        description="Starting frame number",
        default=1,
        min=1
    )

    camera_size: FloatProperty(
        name="Camera Size",
        description="Size of camera visualization",
        default=0.1,
        min=0.001,
        max=10.0
    )

    animate_cameras: BoolProperty(
        name="Animate Cameras",
        description="Set up visibility animation for cameras",
        default=True
    )

    set_active_camera: BoolProperty(
        name="Set Active Camera",
        description="Set first camera as active scene camera",
        default=True
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(heading="Import Options")
        col.prop(self, "frame_start")
        col.prop(self, "camera_size")
        col.prop(self, "animate_cameras")
        col.prop(self, "set_active_camera")

    def execute(self, context):
        try:
            return import_cameras_sequence(
                context,
                self.filepath,
                frame_start=self.frame_start,
                camera_size=self.camera_size,
                animate_cameras=self.animate_cameras,
                set_active_camera=self.set_active_camera
            )
        except Exception as e:
            self.report({'ERROR'}, f"Error importing: {str(e)}")
            return {'CANCELLED'}


def import_cameras_sequence(context, filepath, frame_start=1, camera_size=0.1,
                            animate_cameras=True, set_active_camera=True):
    """Main import function for camera sequence."""

    filepath = Path(filepath)
    folder = filepath.parent

    # Find all camera JSON files
    cam_files = sorted(folder.glob("camera_*.json"))

    if not cam_files:
        # Try any JSON files in the folder
        cam_files = sorted(folder.glob("*.json"))

    if not cam_files:
        raise ValueError(f"No camera JSON files found in {folder}")

    print(f"Found {len(cam_files)} camera files")

    # Create collection
    collection = bpy.data.collections.new("SpaTracker2_Cameras")
    context.scene.collection.children.link(collection)

    # Load metadata if available
    metadata_path = folder / 'metadata.json'
    fps = 30
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            fps = metadata.get('fps', 30)

    # Set scene frame rate
    context.scene.render.fps = fps

    # Create camera objects
    cam_objects = []

    for i, cam_file in enumerate(cam_files):
        print(f"Importing {cam_file.name}...")

        # Load camera data
        with open(cam_file, 'r') as f:
            cam_data = json.load(f)

        # Create camera data
        cam = bpy.data.cameras.new(f"Camera_{i:04d}")
        cam_obj = bpy.data.objects.new(f"Camera_{i:04d}", cam)
        collection.objects.link(cam_obj)

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

            # Set clip range
            cam.clip_start = 0.01
            cam.clip_end = 1000

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

        # Set visibility keyframes if animation enabled
        if animate_cameras:
            current_frame = frame_start + i

            # Start hidden
            cam_obj.hide_viewport = True
            cam_obj.hide_render = True
            cam_obj.keyframe_insert(data_path="hide_viewport", frame=current_frame - 0.5)
            cam_obj.keyframe_insert(data_path="hide_render", frame=current_frame - 0.5)

            # Show at this frame
            cam_obj.hide_viewport = False
            cam_obj.hide_render = False
            cam_obj.keyframe_insert(data_path="hide_viewport", frame=current_frame)
            cam_obj.keyframe_insert(data_path="hide_render", frame=current_frame)

            # Hide again at next frame
            cam_obj.hide_viewport = True
            cam_obj.hide_render = True
            cam_obj.keyframe_insert(data_path="hide_viewport", frame=current_frame + 0.5)
            cam_obj.keyframe_insert(data_path="hide_render", frame=current_frame + 0.5)

        cam_objects.append(cam_obj)

    # Set scene frame range
    if animate_cameras:
        context.scene.frame_start = frame_start
        context.scene.frame_end = frame_start + len(cam_files) - 1

    # Set first camera as active
    if set_active_camera and cam_objects:
        context.scene.camera = cam_objects[0]

    # Select all imported cameras
    bpy.ops.object.select_all(action='DESELECT')
    for obj in cam_objects:
        obj.select_set(True)
    context.view_layer.objects.active = cam_objects[0] if cam_objects else None

    print(f"Imported {len(cam_objects)} cameras")
    print(f"Frame rate: {fps} FPS")
    print(f"Frame range: {context.scene.frame_start} - {context.scene.frame_end}")

    return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportSpaTracker2Cameras.bl_idname, text="SpaTracker2 Camera Sequence (.json)")


classes = (
    ImportSpaTracker2Cameras,
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
