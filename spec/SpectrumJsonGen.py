import json
from enum import Enum
import numpy as np


class SpecType(Enum):
  REFLECTANCE = 0
  ILLUMINANT = 200
  COLOR_MATCH = 2
  REFLECTANCE_NATURAL = 1


def main(path: str, start: int, end: int, resolution: int, s_type: SpecType):
  with open(path) as f:
    all_lines = [float(x) for x in f.readlines()]
  json_dict = {
    'name': path.split('.')[0],
    'type': s_type.name,
    'type_max': s_type.value,
    'start_nm': start,
    'end_nm': end,
    'resolution': resolution,
    'data': all_lines
  }
  json.dump(json_dict, open(
    f"{json_dict['name']}.json", 'w'), sort_keys=False, indent=4)


def color(match: str, start: int, end: int, resolution: int, s_type: SpecType):
  xyz = np.loadtxt(match)
  for i, c in enumerate('xyz'):
    json_dict = {
      'name': c,
      'type': s_type.name,
      'type_max': s_type.value,
      'start_nm': start,
      'end_nm': end,
      'resolution': resolution,
      'data': xyz[:, i].tolist()
    }
    json.dump(json_dict,
              open(f"{c}.json", 'w'), indent=4)


def rename_column():
  json_dict = json.load(open('spec/database/spectrum.json'))
  
  
  if __name__ == '__main__':
    # for i in range(1, 121):
    #     main(f'natural/R{i}.txt', 400, 700, 5, SpecType.REFLECTANCE_NATURAL)
    # color('color_match.csv', 400, 700, 5, SpecType.COLOR_MATCH)
    pass
