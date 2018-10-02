import os
import json
from ColorSpace import RGB


def main():
  config_path = os.environ['MODEL_CONFIG']
  config = json.load(open(config_path))
  objects = config['objects']
  for obj in objects:
    rgb_value = obj['value'][:-1]
    rgb = RGB(*rgb_value)
    spec, scale = rgb.to_spectrum()
    # spec.data *= scale
    obj['value'] = (spec.data * scale).aslist()
  print(objects)


if __name__ == '__main__':
  main()
