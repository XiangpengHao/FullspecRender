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


s = bpy.data.scenes['Scene'].camera


def get_cam():
  loc = s.camera.location
  rot = s.camera.rotation_euler
  print("{")
  print(f'\"location\":{[loc.x,loc.y,loc.z]},')
  print(f'\"rotation\":{[rot.x,rot.y,rot.z]}')
  print("},")


if __name__ == '__main__':
  spec_texture_histogram()
