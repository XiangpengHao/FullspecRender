import numpy as np
import CONSTANT
import json
import os
from ColorSpace import Spectrum, SpecType, XYZ, RGB


def update_xyz_cache():
  d65 = CONSTANT.COMMON_LIGHTS["d65"]
  rv = []
  for m in CONSTANT.REFLECTANCE:
    m1 = np.multiply(m.data, d65.data)
    xyz = Spectrum.spec_to_xyz(m1)
    rgb = xyz.to_srgb()
    m_dict = m.dict
    m_dict["xyz"] = xyz.np_xyz.tolist()
    m_dict["rgb"] = rgb.np_rgb.tolist()
    rv.append(m_dict)
  
  json.dump(rv, open("spec/database/reflectance.json", "w"))
  # print(rv)rv


def replace_rgb_in_config():
  config_path = os.environ['MODEL_CONFIG']
  config = json.load(open(config_path))
  objects = config['colorNodes']
  for obj in objects:
    rgb_value = obj['value'][:-1]
    rgb = RGB(*rgb_value)
    spec, scale = rgb.to_spectrum()
    # spec.data *= scale
    avg_spec = spec.data.mean()
    avg_rgb = rgb.np_rgb.mean()
    obj['value'] = (spec.data / avg_spec * avg_rgb).tolist()
    # obj['value'] = (spec.data * scale * 3000).tolist()
  json.dump(config, open(config_path, 'w'))
  print(objects)


def read_all_nodes_from_model(config):
  pass


if __name__ == '__main__':
  config_path = os.environ['MODEL_CONFIG']
  config = json.load(open(config_path))
  replace_rgb_in_config()
