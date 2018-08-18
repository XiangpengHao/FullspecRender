import json
from ColorSpace import Spectrum
from typing import List, Union, Tuple
import numpy as np
import utils
from scipy import spatial
import CONSTANT

reflectance: List[Spectrum] = [Spectrum(x) for x in json.load(open('spec/database/reflectance.json'))]
_all_reflectance_xy = [np.asarray(x['xyz']) / sum(x['xyz']) for x in reflectance]
reflectance_kdd = spatial.KDTree(_all_reflectance_xy)

illuminant: List[Spectrum] = [Spectrum(x) for x in json.load(open('spec/database/illuminant.json'))]
_all_illuminant_xy = [np.asarray(x['xyz']) / sum(x['xyz']) for x in illuminant]
illuminant_kdd = spatial.KDTree(_all_illuminant_xy)


def find_nearest_reflectance(rgb: np.ndarray) -> (Spectrum, np.ndarray):
  xyz = utils.srgb_to_xyz(rgb)
  if sum(xyz) == 0:
    return reflectance[0], 0
  xyz_norm = xyz / sum(xyz)
  distance, index = reflectance_kdd.query(xyz_norm)
  
  return reflectance[index], xyz[1] / reflectance[index]['xyz'][1]


def find_nearest_illuminant(rgb: np.ndarray) -> (Spectrum, np.ndarray):
  xyz = utils.srgb_to_xyz(rgb)
  if sum(xyz) == 0:
    return illuminant[0], 0
  xyz_norm = xyz / sum(xyz)
  distance, index = illuminant_kdd.query(xyz_norm)
  return illuminant[index], xyz[1] / illuminant[index]['xyz'][1]


if __name__ == '__main__':
  # save_data()
  # parse_model_config('model/donut.json')
  # compute_d65_cache_xyz()
  # test()
  near = find_nearest_illuminant(np.asarray([0.65, 0.4, 0.35]))
  print(near[0].json, near[1])
