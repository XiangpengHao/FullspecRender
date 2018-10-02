import bpy
import json
import os
import re

INPUT_KEYWORDS = ['Color']
NODE_KEYWORDS = ['Mix', 'BSDF']


class ModelDataExporter:
  def __init__(self):
    self.cur_material = None
    self.cur_node = None
    self.result = []
  
  def parse(self):
    materials = bpy.data.materials
    for m in materials:
      self.cur_material = m
      self.parse_node_tree(m.node_tree.nodes)
  
  def parse_node_tree(self, nodes):
    for n in nodes:
      self.cur_node = n
      for nk in NODE_KEYWORDS:
        if nk in n.name:
          self.parse_inputs(n.inputs)
          break
  
  def parse_inputs(self, inputs):
    for i in inputs:
      if (re.match(r'^Color[12]?$', i.name) or i.name == 'Base Color') \
          and not i.links:
        payload = {
          'type': 'MATERIAL',
          'name': self.cur_material.name,
          'node': self.cur_node.name,
          'input': i.name,
          'value': [x for x in i.default_value]
        }
        self.result.append(payload)


if __name__ == '__main__':
  exporter = ModelDataExporter()
  exporter.parse()
  print(exporter.result)
