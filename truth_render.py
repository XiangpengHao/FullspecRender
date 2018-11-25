import bpy
import os
import shutil
import json

SCENE_NAME = "Scene"
LAYERS=['use_pass_z', 'use_pass_normal']

def set_locations(data):
  for obj in data:
    bpy_obj = bpy.data.objects[obj['name']]
    bpy_obj.location.x = obj['location'][0]
    bpy_obj.location.y = obj['location'][1]
    bpy_obj.location.z = obj['location'][2]
    bpy_obj.rotation_euler.x = obj['rotation'][0]
    bpy_obj.rotation_euler.y = obj['rotation'][1]
    bpy_obj.rotation_euler.z = obj['rotation'][2]

def context_setup():
  bpy.context.scene.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
  bpy.context.scene.render.image_settings.color_mode = 'RGB'
  bpy.context.scene.render.image_settings.color_depth = '16'
  bpy.context.scene.render.image_settings.exr_codec = 'PIZ'
  for layer in LAYERS:
    setattr(bpy.data.scene[SCENE_NAME].view_layers['RenderLayer'], layer, True)
  
def render(scene_name, output_path, resolution, viewpoint):
  scene = bpy.data.scenes[scene_name]

  scene.render.engine='CYCLES'
  
  scene.cycles.device='CPU'
  scene.render.tile_x=32
  scene.render.tile_y=32
  scene.cycles.samples = 1
  scene.render.resolution_x = resolution[0]
  scene.render.resolution_y = resolution[1]
  
  camera = scene.camera
  camera.location.x = viewpoint['location'][0]
  camera.location.y = viewpoint['location'][1]
  camera.location.z = viewpoint['location'][2]
  camera.rotation_euler.x = viewpoint['rotation'][0]
  camera.rotation_euler.y = viewpoint['rotation'][1]
  camera.rotation_euler.z = viewpoint['rotation'][2]
  
  scene.render.filepath=output_path
  bpy.ops.render.render(write_still=True)



def main():
  working_dir = os.environ["MODEL"]
  config_file = os.environ["CONFIG_FILE"]
  config = json.load(open(os.path.join(working_dir, config_file)))
  start_from = config['startFrom']
  resolution = config.get('resolution', [960, 720])
  if isinstance(config['viewports'], str):
    viewports = json.load(open(os.path.join(working_dir, config['viewports'])))
  else:
    viewports = config['viewports']
  
  output_dir = os.path.join(working_dir, 'rendered', config['name'], '')
  print(output_dir, config['name'])
  os.makedirs(os.path.dirname(output_dir))

  context_setup()
  for k, vp in enumerate(viewports):
    if k < start_from:
      continue
    render(scene_name=config['scene'],
           output_path=os.path.join(output_dir, f'vp_{k}.exr'),
           resolution=resolution,
           viewpoint=vp)


if __name__ == '__main__':
  main()
