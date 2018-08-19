import numpy as np
import CONSTANT
import json
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


if __name__ == '__main__':
  update_xyz_cache()
