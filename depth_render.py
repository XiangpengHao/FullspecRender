import bpy
import os
import shutil
import json

DEPTH_OUTPUT_FILENAME = 'Image0002.png'


def set_locations(data):
  for obj in data:
    bpy_obj = bpy.data.objects[obj['name']]
    bpy_obj.location.x = obj['location'][0]
    bpy_obj.location.y = obj['location'][1]
    bpy_obj.location.z = obj['location'][2]
    bpy_obj.rotation_euler.x = obj['rotation'][0]
    bpy_obj.rotation_euler.y = obj['rotation'][1]
    bpy_obj.rotation_euler.z = obj['rotation'][2]


def render(scene_name, output_path, resolution, viewpoint):
  bpy.context.scene.use_nodes = True
  scene = bpy.data.scenes[scene_name]
  tree = scene.node_tree
  links = tree.links
  for n in tree.nodes:
    tree.nodes.remove(n)
  
  rl = tree.nodes.new('CompositorNodeRLayers')
  
  normalize = tree.nodes.new('CompositorNodeNormalize')
  links.new(rl.outputs[2], normalize.inputs[0])
  
  invert = tree.nodes.new('CompositorNodeInvert')
  links.new(normalize.outputs[0], invert.inputs[1])
  
  file_output = tree.nodes.new('CompositorNodeOutputFile')
  file_output.base_path = '/tmp/'
  links.new(invert.outputs[0], file_output.inputs[0])
  
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
  
  bpy.ops.render.render()
  shutil.move(f'/tmp/{DEPTH_OUTPUT_FILENAME}', output_path)


# os.remove('/home/hao/Documents/a.png')


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
  for k, vp in enumerate(viewports):
    if k < start_from:
      continue
    render(scene_name=config['scene'],
           output_path=os.path.join(output_dir, f'vp_{k}.png'),
           resolution=resolution,
           viewpoint=vp)


if __name__ == '__main__':
  main()
