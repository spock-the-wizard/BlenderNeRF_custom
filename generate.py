import bpy
import argparse
import os
import sys
from BlenderNeRF import helper

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="BlenderNeRF Script Arguments")
    parser.add_argument("--mode", choices=['even','random'], required=True)
    # TODO: output dir, overwrite disable
    parser.add_argument("--dataset_name", type=str, default='test',)
    parser.add_argument("--num_views", type=int, required=True)

    parser.add_argument("--only_pose", action='store_true',)
    parser.add_argument("--only_upper", action='store_true')
    parser.add_argument("--debug", action='store_true')
    
    parser.add_argument("--outpath_root", type=str,)


    # Filter Blender's arguments to avoid conflict
    args, unknown = parser.parse_known_args(sys.argv[sys.argv.index("--") + 1:])
    return args

def setup_depth_render():
# Enable Z Depth pass
    bpy.context.view_layer.use_pass_z = True

# Set up the compositor
    scene = bpy.context.scene
    scene.use_nodes = True
    nodes = scene.node_tree.nodes
    links = scene.node_tree.links

# Clear existing nodes
    for node in nodes:
        nodes.remove(node)

# Add Render Layers node
    render_layers = nodes.new('CompositorNodeRLayers')
    render_layers.location = (0, 0)

# Add Composite node for the standard image
    composite = nodes.new('CompositorNodeComposite')
    composite.location = (400, 200)
    links.new(render_layers.outputs['Image'], composite.inputs['Image'])

# Add File Output node for depth
    file_output_depth = nodes.new('CompositorNodeOutputFile')
    file_output_depth.location = (400, -200)
    file_output_depth.format.file_format = 'OPEN_EXR'
    file_output_depth.base_path = f"{data_dir}/depth" # "//depth_output/"
    links.new(render_layers.outputs['Depth'], file_output_depth.inputs[0])


    print("Depth and image rendering setup completed.")


if __name__ == "__main__":
    args = parse_args()

# Enable the addon if it's not already enabled
    addon_name = "BlenderNeRF"  # Replace with the actual name of the addon
    if addon_name not in bpy.context.preferences.addons:
        print("Adding plugin")
        bpy.ops.preferences.addon_enable(module=addon_name)
        
    import bpy
    import mathutils

# Initialize the bounding box min/max coordinates
    min_coords = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    max_coords = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))

    # radius_threshold = 10.0

    for obj in bpy.context.scene.objects:
        if obj.type not in {'LIGHT', 'CAMERA'}:
            distance = obj.location.length

            # if distance > radius_threshold:
            #     print(f"Skipping object '{obj.name}' at distance {distance:.2f}")
            #     continue
            world_matrix = obj.matrix_world
            for corner in obj.bound_box:
                # Transform corner to world coordinates
                world_corner = world_matrix @ mathutils.Vector(corner)
                if world_corner.z <= 0.0:
                    continue
                # Update the bounding box
                min_coords = mathutils.Vector(map(min, min_coords, world_corner))
                max_coords = mathutils.Vector(map(max, max_coords, world_corner))

    center = (min_coords + max_coords) / 2.0
    dimensions = max_coords - min_coords
    diagonal = dimensions.length

    import math
    scene = bpy.context.scene

    focal_length = scene.focal  # Focal length in mm
    sensor_size = scene.camera.data.sensor_width
    fov_rad = 2 * math.atan(sensor_size / (2 * focal_length))

    radius = diagonal / (2 * math.tan(fov_rad / 2))

    ### Modify the radius based on the dataset
    if args.dataset_name.startswith("italian-style"):
        radius = 30.0
    elif args.dataset_name.startswith("hyperspace-shuttle"):
        center[0] = 0.1*2
        center[1] = 0.3*2
        center[2] = 4.0
        radius = 7.0
    elif args.dataset_name.startswith("robot"):
        center[0] = 0.0
        center[1] = 0.0
        center[2] = 0.0
        radius = 12.0
    elif args.dataset_name.startswith("steamtrain"):
        center[0] = 0.0
        center[1] = 0.0
        center[2] = 2.5
        radius = 25.0  # Original
        radius = 25.0*0.7  # Small
        radius = 25.0*1.5 # Big
    elif args.dataset_name.startswith("chinese-palace"):
        center[0] = 0.0
        center[1] = -0.1
        center[2] = 0.0 # 2.5
        radius = 3.5
    elif args.dataset_name.startswith("toad"):
        center[0] = 0.0
        center[1] = 0.0
        center[2] = 0.0 # 2.5
        radius = 40.0
    elif args.dataset_name.startswith("record-player"):
        center[0] = 0.0
        center[1] = 0.0
        center[2] = 0.0 # 2.5
        radius = 0.7
    # NOTE: manually set

    # # NOTE: TMP params for toad
    print(f"Sphere Radius: {radius}")


# Initialize the target location (e.g., world origin)

    if args.debug:
        scene.render.engine = 'BLENDER_WORKBENCH'
    else:
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 256 # TODO 
        scene.cycles.device = 'GPU'

    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_adaptive_threshold = 0.1
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPTIX'
    scene.cycles.max_bounces = 8
    scene.cycles.transparent_max_bounces = 4
    
    scene.render.use_border = False
    scene.render.use_persistent_data = True
    scene.render.resolution_y = 800
    scene.render.resolution_x = 800
    scene.render.film_transparent = True

    scene.frame_start = 1
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

    # scene.render.film_transparent = True
    # scene.render.resolution_x = 800
    # scene.render.resolution_y = 800

# Set dataset settings
    scene.splats = True
    scene.splats_test_dummy = True
    scene.nerf = True
    scene.sphere_radius = radius
    scene.sphere_location = center
    
    scene.cos_nb_frames = args.num_views
    scene.ces_nb_frames = args.num_views
    scene.save_path = args.outpath_root

    if args.only_upper:
        bpy.context.scene.upper_views = True
    else:
        bpy.context.scene.upper_views = False
    if args.only_pose:
        bpy.context.scene.render_frames = False

    dataset_name = args.dataset_name
    data_dir = os.path.join(args.outpath_root,dataset_name)
    while os.path.exists(data_dir):
        print(f"Dataset name {dataset_name} already exists")
        dataset_name = dataset_name + '2'
        data_dir = os.path.join(args.outpath_root,dataset_name)
    print(f"Dataset name is {dataset_name}")
    
    if args.mode == "random":
        print("Place cameras randomly")
        # setup_depth_render()
        bpy.app.handlers.frame_change_post[-1] = helper.cos_camera_update
        bpy.context.scene.cos_dataset_name = dataset_name
        bpy.ops.object.camera_on_sphere()
    elif args.mode == "even":
        print("Place cameras evenly")
        # setup_depth_render()
        bpy.app.handlers.frame_change_post[-1] = helper.ces_camera_update
        bpy.context.scene.ces_dataset_name = dataset_name
        bpy.ops.object.camera_on_even_sphere()
        
        


# Optionally, you can do additional things like saving the scene or rendering
# bpy.ops.wm.save_as_mainfile(filepath="your_output_file.blend")  # Save the file after operation
