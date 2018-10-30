# pylint: disable=E0401
# disable the import error
import bpy
from typing import Tuple, List, Dict, Any, Union
from os import path
import os
import json
from enum import Enum
from shutil import copyfileobj

ROOT_PATH = '/home/hao/ownCloud/FullSpecRendering/' if os.name == 'posix' else \
  '/mnt/e/ownCloud/FullSpecRendering'


class BlenderType(Enum):
  LIGHTS = 0
  MATERIAL = 1
  TEXTURE = 2
  NODE = 3


class BlenderNode:
  def __init__(self, node_type: str, name: str, node: str, input_slot: str, values: list, value_length=3):
    self.node_type = node_type
    self.name = name
    self.node = node
    self.input_slot = input_slot
    self.values = values
    self._value_length = value_length
    if self.node_type == 'MATERIAL':
      blender_prefix = bpy.data.materials[name]
    elif self.node_type == 'WORLDS':
      blender_prefix = bpy.data.worlds[name]
    elif self.node_type == 'LIGHTS':
      blender_prefix = bpy.data.lights[name]
    else:
      raise NotImplementedError(self.node_type)
    self.node_ref = blender_prefix.node_tree.nodes[node].inputs[input_slot]
  
  def set_color(self, wavelength: int):
    value_index = (wavelength - 400) // 15 * self._value_length
    # print((*self.values[value_index:value_index + 3], 1))
    if self._value_length == 3:
      self.node_ref.default_value = (*self.values[value_index:value_index + self._value_length], 1)
    elif self._value_length == 1:
      self.node_ref.default_value = self.values[value_index]


class TextureNode:
  def __init__(self, name, node, value, intermediate_path):
    self.texture_ref = bpy.data.materials[name].node_tree.nodes[node]
    self.image_name = value
    self.intermediate_path = intermediate_path
  
  def set_color(self, wavelength: int):
    src_file = f'{self.intermediate_path}/{self.image_name}/_{wavelength}_{wavelength+5}_{wavelength+10}_nm.jpg'
    new_img = bpy.data.images.load(filepath=src_file, check_existing=False)
    # print(new_img)
    self.texture_ref.image = new_img


class FullSpecRender:
  def __init__(self, objects: List[Union[BlenderNode, TextureNode]], scene='Scene'):
    self.normal_objects = [o for o in objects if isinstance(o, BlenderNode)]
    self.texture_objects = [o for o in objects if isinstance(o, TextureNode)]
    self.bpy_scene = bpy.data.scenes[scene]
  
  # index_i is sth like 400, 405, 410
  def _set_color(self, index_i: int):
    for obj in self.texture_objects:
      obj.set_color(index_i)
    for obj in self.normal_objects:
      obj.set_color(index_i)
  
  def render(self, index: int, output_prefix: str, resolution=(640, 480), viewport=None):
    self._set_color(index)
    output_path = f'{output_prefix}_{index}_{index+5}_{index+10}_nm.png'
    
    self.bpy_scene.render.resolution_x = resolution[0]
    self.bpy_scene.render.resolution_y = resolution[1]
    self.bpy_scene.render.resolution_percentage = 100
    self.bpy_scene.render.filepath = path.join(ROOT_PATH, output_path)
    self.bpy_scene.render.engine = 'CYCLES'
    
    device = os.environ.get('RENDER_DEVICE')
    if device == "GPU":
      self.bpy_scene.cycles.device = 'GPU'
      context = bpy.context
      cycles_prefs = context.user_preferences.addons['cycles'].preferences
      cycles_prefs.compute_device_type = "CUDA"
      for device in cycles_prefs.devices:
        device.use = False
      for device in cycles_prefs.devices[:]:
        device.use = True
    else:
      self.bpy_scene.cycles.device = 'CPU'
      self.bpy_scene.render.tile_x = 32
      self.bpy_scene.render.tile_y = 32
    if viewport is not None:
      camera = self.bpy_scene.camera
      camera.location.x = viewport['location'][0]
      camera.location.y = viewport['location'][1]
      camera.location.z = viewport['location'][2]
      camera.rotation_euler.x = viewport['rotation'][0]
      camera.rotation_euler.y = viewport['rotation'][1]
      camera.rotation_euler.z = viewport['rotation'][2]
    bpy.ops.render.render(write_still=True)


def set_locations(data):
  for obj in data:
    bpy_obj = bpy.data.objects[obj['name']]
    bpy_obj.location.x = obj['location'][0]
    bpy_obj.location.y = obj['location'][1]
    bpy_obj.location.z = obj['location'][2]
    bpy_obj.rotation_euler.x = obj['rotation'][0]
    bpy_obj.rotation_euler.y = obj['rotation'][1]
    bpy_obj.rotation_euler.z = obj['rotation'][2]


def main():
  working_dir = os.environ["MODEL"]
  config_file = os.environ["CONFIG_FILE"]
  config = json.load(open(path.join(working_dir, config_file)))
  intermediate_dir = path.join(working_dir, config['intermediatePath'])
  start_from = config['startFrom']
  resolution = config.get('resolution', [960, 720])
  
  normal_objects = []
  for node in config['colorNodes']:
    if isinstance(node['name'], str) and isinstance(node['node'], str):
      normal_objects.append(BlenderNode(node['type'], node['name'], node['node'], node['input'], node['value'],
                                        node.get('value_length', 3)))
    elif isinstance(node['name'], list):
      for n in node['name']:
        normal_objects.append(BlenderNode(node['type'], n, node['node'], node['input'], node['value'], node.get('value_length', 3)))
    elif isinstance(node['node'], list):
      for n in node['node']:
        normal_objects.append(BlenderNode(node['type'], node['name'], n, node['input'], node['value'], node.get('value_length', 3)))

  
  if isinstance(config['textureNodes'], str):
    texture_nodes = json.load(open(os.path.join(working_dir, config['textureNodes'])))
  else:
    texture_nodes=config['textureNodes']

  texture_objects = []
  for node in texture_nodes:
    texture_objects.append(
      TextureNode(name=node['name'], node=node['node'], value=node['value'], intermediate_path=intermediate_dir))
  

  if "locations" in config:
    set_locations(config["locations"])
  
  renderer = FullSpecRender(normal_objects + texture_objects, scene=config['scene'])

  if isinstance(config['viewports'], str):
    viewports = json.load(open(os.path.join(working_dir, config['viewports'])))
  else:
    viewports = config['viewports']
  
  
  task_id = os.environ.get('SLURM_ARRAY_TASK_ID', None)
  if task_id:
    k = int(task_id)
    vp = viewports[k]
    output_dir = f"{working_dir}/rendered/{config['name']}/vp_{k}/"
    os.makedirs(os.path.dirname(output_dir))
    for i in range(400, 700, 15):
      print(f'now rendering {i}_{i+5}_{i+10}')
      renderer.render(i, output_dir, resolution=resolution, viewport=vp)
  else:
    for k, vp in enumerate(viewports):
      if k < start_from:
        continue
      output_dir = f"{working_dir}/rendered/{config['name']}/vp_{k}/"
      os.makedirs(os.path.dirname(output_dir))
      for i in range(400, 700, 15):
        print(f'now rendering {i}_{i+5}_{i+10}')
        renderer.render(i, output_dir, resolution=resolution, viewport=vp)


if __name__ == '__main__':
  main()
