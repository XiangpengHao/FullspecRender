import bpy
import os
import json


def main():
  config_path = os.environ['MODEL_CONFIG']
  config = json.load(open(config_path))
  objects = config['objects']
  for obj in objects:
    if obj['type'] == 'MATERIAL':
      prefix = bpy.data.materials
    elif obj['type'] == 'WORLDS':
      prefix = bpy.data.worlds
    else:
      raise NotImplementedError
    default_value = prefix[obj['name']].node_tree.nodes[obj['node']].inputs[obj['input']].default_value
    obj['value'] = [x for x in default_value]
  json.dump(config, open(config_path, 'w'))
  print(objects)


if __name__ == '__main__':
  main()
