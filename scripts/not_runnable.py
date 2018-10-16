import matplotlib.pyplot as plt
import numpy as np
import bpy

D = bpy.data


def spec_texture_histogram():
  texture = SpecTexture()
  file = 'lotus.jpg'
  texture.load_spec(rf'E:\ownCloud\BarceNew\3d\textures\{file}.st')
  vals = texture.spectrum.flatten()
  plt.hist(vals, bins='auto')
  plt.title(
    f'file: {file}, mean: {int(np.mean(vals)*1000)/1000}, '
    f'max: {int(np.amax(vals)*1000)/1000}, min: {int(np.amin(vals)*1000)/1000}')
  plt.show()


def set_all_glossy_bsdf():
  for m in D.materials:
    glossy = m.node_tree.nodes.get('Glossy BSDF')
    if not glossy:
      continue
    value = glossy.inputs[0].default_value
    if value[0] == value[1] and value[1] == value[2]:
      print(m.name)
      glossy.inputs[0].default_value = (0.4, 0.4, 0.4, 1)


def set_all_specular_0_in_principle_BSDF():
  for m in D.materials:
    principle = m.node_tree.nodes.get('Principled BSDF')
    if principle:
      print(m.name)
      principle.inputs['Specular'].default_value = 0
    glossy = m.node_tree.nodes.get('Glossy BSDF')
    if glossy:
      value = glossy.inputs[0].default_value
      if value[0] == value[1] and value[1] == value[2]:
        print(m.name)
        glossy.inputs[0].default_value = (0, 0, 0, 1)


vp_list = []


def get_cam():
  s = bpy.data.scenes['Scene']
  loc = s.camera.location
  rot = s.camera.rotation_euler
  output = "{{\"location\":{},\"rotation\":{}}}".format([loc.x, loc.y, loc.z],
                                                        [rot.x, rot.y, rot.z])
  vp_list.append(output)
  print(output)


def align_light_with_camera():
  import math
  s = bpy.data.scenes["2- time: sunset"]
  light = bpy.data.objects['Area']
  cam_loc = s.camera.location.copy()
  # cam_loc[2] += 2
  cam_rot = s.camera.rotation_euler.copy()
  # cam_rot[0] -= 0.13
  # cam_rot[1] -= 0.13
  light.location = cam_loc
  light.rotation_euler = cam_rot


if __name__ == '__main__':
  spec_texture_histogram()
