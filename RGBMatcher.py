import json
from Spectrum import Spectrum
from typing import List, Union, Tuple
import numpy as np
from utils import spec_to_rgb
import utils
from scipy import spatial
import CONSTANT

THRESH_HOLD = 0.996  # 5 degree
DISTANCE_HOLD = 0.0005


def compute_d65_cache_xyz():
  rv = []
  d65 = Spectrum('spec/d65.json')
  for spec in all_spec:
    under_light = np.multiply(d65.data, spec['data'])
    xyz: Tuple[float, float, float] = utils.spec_to_xyz(under_light)
    spec['xyz_d65'] = xyz
    rv.append(spec)
    print(spec)
  json.dump(all_spec, open('spec/database/spectrum.json', 'w'))


def compute_d65_cache_rgb():
  rv = []
  for spec in all_spec:
    r, g, b = utils.under_d65(Spectrum(spec))
    spec['rgb_d65'] = [r, g, b]
    rv.append(spec)
    print(spec)
  json.dump(all_spec, open('spec/database/all.json', 'w'))


all_spec = json.load(open('spec/database/spectrum.json'))
all_spec_xy = [np.asarray(x['xyz_d65']) / sum(x['xyz_d65']) for x in all_spec]
all_spec_xy_kdd = spatial.KDTree(all_spec_xy)


def find_nearest(rgb: np.ndarray) -> (Spectrum, np.ndarray):
  xyz = utils.srgb_to_xyz(rgb)
  if sum(xyz) == 0:
    return Spectrum(all_spec[0]), 0
  xyz_norm = xyz / sum(xyz)
  distance, index = all_spec_xy_kdd.query(xyz_norm)
  
  return Spectrum(all_spec[index]), xyz[1] / all_spec[index]['xyz_d65'][1]


def find_nearest_deprecated(rgb: np.ndarray) -> (Spectrum, np.ndarray):
  xyz = utils.srgb_to_xyz(rgb)
  xyz_norm = xyz / sum(xyz)
  min_distance = 100
  min_index = 0
  for i, spec in enumerate(all_spec):
    spec_xyz = spec['xyz_d65']
    sum_xyz = sum(spec_xyz)
    distance = utils.distance_v2((xyz_norm[0], xyz_norm[1]), (spec_xyz[0] / sum_xyz, spec_xyz[1] / sum_xyz))
    if distance < min_distance:
      min_distance = distance
      min_index = i
  return Spectrum(all_spec[min_index]), xyz[2] / all_spec[min_index]['xyz_d65'][2]


def find_closet_using_rgb(rgb: Tuple[float, float, float]):
  max_cosine = 0
  max_index = 0
  rgb_norm = np.linalg.norm(rgb)
  for i, spec in enumerate(all_spec):
    # if min(spec['rgb_d65']) < 0:
    #   continue
    dot_value = np.dot(rgb, spec['rgb_d65'])
    t = dot_value / (rgb_norm * np.linalg.norm(spec['rgb_d65']))
    if t > max_cosine:
      max_index = i
      max_cosine = t
    if t > THRESH_HOLD:
      max_index = i
      # print(f'====== break with {t}, {i}')
      break
  return all_spec[max_index]


def parse_model_config(path: str):
  config = json.load(open(path))
  result = {}
  for k, v in config.items():
    closet_spec, scale = find_nearest(np.asarray(v))
    closet_spec.data = (np.asarray(closet_spec.data) * scale * CONSTANT.SPECTRUM_SCALE).tolist()
    result[k] = {
      'rgb': v,
      'spec': closet_spec.dict
    }
  json.dump(result, open(path.split('.')[0] + '_q.json', 'w'))


def test():
  rgb = (0.3, 0.6, 0.7)
  # result, s = find_nearest(np.asarray(rgb))
  r_k, s_k = find_nearest(np.asarray(rgb))
  xyz_d65 = np.asarray(r_k.xyz_d65) * s_k
  rgb_new = utils.xyz_to_srgb(xyz_d65)
  print(rgb_new)


if __name__ == '__main__':
  # save_data()
  # parse_model_config('model/donut.json')
  # compute_d65_cache_xyz()
  # test()
  near = find_nearest(np.asarray([0.65, 0.4, 0.35]))[0]
  print(near.json)
