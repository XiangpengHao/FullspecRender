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


def get_light_spectral(file_name) -> List[float]:
  with open(path.join(ROOT_PATH, file_name)) as f:
    data = [float(x) for x in f.readlines()]
  return data


def get_natural_spectral(file_name) -> List[float]:
  with open(path.join(ROOT_PATH, file_name)) as f:
    data = [float(x) for x in f.readlines()[:-1]]
  return data


class BlenderType(Enum):
  LIGHTS = 0
  MATERIAL = 1
  TEXTURE = 2


class Spectrum:
  def __init__(self, spec_file: Union[str, dict]):
    self.name = ''
    self.type = ''
    if type(spec_file) == str:
      with open(os.path.join(ROOT_PATH, spec_file)) as f:
        data = json.load(f)
      self.name = data.get('name')
      self.type = data.get('type')
      self.start_nm = data.get('start_nm')
      self.end_nm = data.get('end_nm')
      self.resolution = data.get('resolution')
      self.rgb_d65 = data.get('rgb_d65')
      self.xyz_d65 = data.get('xyz_d65')
      self.data = [x / data.get('type_max') for x in data.get('data')]
    elif type(spec_file) == dict:
      self.name = spec_file.get('name')
      self.type = spec_file.get('type')
      self.start_nm = spec_file.get('start_nm')
      self.end_nm = spec_file.get('end_nm')
      self.resolution = spec_file.get('resolution')
      self.rgb_d65 = spec_file.get('rgb_d65')
      self.xyz_d65 = spec_file.get('xyz_d65')
      self.data = [x / spec_file.get('type_max') for x in spec_file.get('data')]
  
  def __getitem__(self, item):
    if isinstance(item, slice):
      if item.start < self.start_nm or item.stop > self.end_nm:
        raise ArithmeticError("nm not in range")
      start_i = (item.start - self.start_nm) // self.resolution
      end_i = (item.stop - self.start_nm) // self.resolution
      return self.data[start_i:end_i]


class SpectrumObj:
  def __init__(self, obj_name: str, spc_path: str, blender_type: BlenderType):
    self.name = obj_name
    self.blender_type = blender_type
    if blender_type == BlenderType.LIGHTS:
      self.blender_obj = bpy.data.lamps[obj_name].node_tree.nodes['Emission'].inputs[0]
    elif blender_type == BlenderType.MATERIAL:
      self.blender_obj = bpy.data.materials[obj_name].node_tree.nodes['Diffuse BSDF'].inputs[0]
    else:
      raise RuntimeError(f"not supported blender type: {blender_type.name}")
    
    self.spec_data = Spectrum(spc_path)
  
  def set_color(self, color: Tuple[float, float, float, float]):
    self.blender_obj.default_value = color


class SpectrumTexture:
  def __init__(self, texture_dst: str, texture_src_folder: str, blender_type: BlenderType):
    assert blender_type == BlenderType.TEXTURE
    self.texture_dst = texture_dst
    self.texture_src_folder = texture_src_folder
  
  def set_color(self, wavelength: int):
    src_file = '{}/_{}_{}_{}_nm.jpg'.format(self.texture_src_folder, wavelength, wavelength + 5, wavelength + 10)
    # src_file = f'{self.texture_src_folder}/_{wavelength}_{wavelength+5}_{wavelength+10}nm.png'
    with open(os.path.join(ROOT_PATH, src_file), 'rb') as src, \
        open(os.path.join(ROOT_PATH, self.texture_dst), 'wb') as dst:
      copyfileobj(src, dst)


class FullSpecRender:
  def __init__(self, objects: List[Union[SpectrumObj, SpectrumTexture]], scene='Scene'):
    self.normal_objects = [o for o in objects if isinstance(o, SpectrumObj)]
    self.texture_objects = [o for o in objects if isinstance(o, SpectrumTexture)]
    self.bpy_scene = bpy.data.scenes[scene]
  
  # index_i is sth like 400, 405, 410
  def _set_color(self, index_i: int):
    for obj in self.texture_objects:
      obj.set_color(index_i)
    for obj in self.normal_objects:
      spc_rgb = (*(obj.spec_data[index_i:index_i + 15]), 1)
      obj.set_color(spc_rgb)
  
  def render(self, index: int, output_prefix: str, resolution=(640, 480), viewport=None):
    self._set_color(index)
    output_path = '{output_prefix}_{index}_{index_5}_{index_10}_nm.png'.format(output_prefix=output_prefix,
                                                                               index=index, index_5=index + 5,
                                                                               index_10=index + 10)
    
    self.bpy_scene.render.resolution_x = resolution[0]
    self.bpy_scene.render.resolution_y = resolution[1]
    self.bpy_scene.render.resolution_percentage = 100
    self.bpy_scene.render.filepath = path.join(ROOT_PATH, output_path)
    if viewport is not None:
      camera = self.bpy_scene.camera
      camera.location.x = viewport['location'][0]
      camera.location.y = viewport['location'][1]
      camera.location.z = viewport['location'][2]
      camera.rotation_euler.x = viewport['rotation'][0]
      camera.rotation_euler.y = viewport['rotation'][1]
      camera.rotation_euler.z = viewport['rotation'][2]
    bpy.ops.render.render(write_still=True)


def main():
  model_config_path = os.environ["MODEL"]
  config = json.load(open(model_config_path))
  working_dir = config['rootPath']
  texture_dir = path.join(working_dir, config['texturePath'])
  intermediate_dir = path.join(working_dir, config['intermediatePath'])
  
  spc_objs = [
    # SpectrumObj('sun_set', 'spec/illA.json', BlenderType.LIGHTS),
    SpectrumObj('white_lotus_orange', 'spec/munsell/m_2.5YR6_14.json', BlenderType.MATERIAL),
    SpectrumObj('trunk', 'spec/munsell/m_2.5Y8.5_6.json', BlenderType.MATERIAL),
    *[SpectrumTexture(path.join(texture_dir, x[:-3]),
                      path.join(intermediate_dir, x.split('.')[0]),
                      BlenderType.TEXTURE)
      for x in config['textures']]
  ]
  renderer = FullSpecRender(spc_objs, scene=config['scene'])
  for k, vp in enumerate(config['viewports']):
    output_dir = f"{working_dir}/rendered/{config['name']}/vp_{k}/"
    os.makedirs(os.path.dirname(output_dir))
    for i in range(400, 700, 15):
      print('now rendering {i}_{i+5}_{i+10}' + str(i))
      renderer.render(i, output_dir, resolution=(960, 720), viewport=vp)


if __name__ == '__main__':
  main()
