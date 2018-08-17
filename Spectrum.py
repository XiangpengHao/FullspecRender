from typing import List, Union, Dict
import json
from os import path
import random
import os

ROOT_PATH = '/home/hao/Dropbox/FullSpecRendering/' if os.name == 'posix' else 'C:\\Users\\haoxi\\Dropbox\\FullSpecRendering'


class Spectrum:
  def __init__(self, spec_file: Union[str, dict]):
    self.name: str
    self.type: str
    if type(spec_file) == str:
      with open(spec_file) as f:
        data = json.load(f)
      self.name: str = data.get('name')
      self.type: str = data.get('type')
      self.start_nm: int = data.get('start_nm')
      self.end_nm: int = data.get('end_nm')
      self._resolution: int = data.get('resolution')
      self.rgb: List[float] = data.get('rgb')
      self.xyz: List[float] = data.get('xyz')
      self.type_max = data.get('type_max')
      self.data: List[float] = [x / data.get('type_max') for x in data.get('data')]
    elif type(spec_file) == dict:
      self.name: str = spec_file.get('name')
      self.type: str = spec_file.get('type')
      self.start_nm: int = spec_file.get('start_nm')
      self.end_nm: int = spec_file.get('end_nm')
      self._resolution: int = spec_file.get('resolution')
      self.rgb: List[float] = spec_file.get('rgb')
      self.type_max = spec_file.get('type_max')
      self.xyz: List[float] = spec_file.get('xyz')
      self.data: List[float] = [x / spec_file.get('type_max') for x in spec_file.get('data')]
  
  def __getitem__(self, item):
    if isinstance(item, slice):
      if item.start < self.start_nm or item.stop > self.end_nm:
        raise ArithmeticError("nm not in range")
      start_i = (item.start - self.start_nm) // self.resolution
      end_i = (item.stop - self.start_nm) // self.resolution
      print(self.data[start_i:end_i])
      return self.data[start_i:end_i]
  
  @property
  def dict(self):
    rv = {
      'name': self.name,
      'type': self.type,
      'start_nm': self.start_nm,
      'end_nm': self.end_nm,
      'resolution': self._resolution,
      'rgb': self.rgb,
      'xyz': self.xyz,
      'data': self.data,
      'type_max': self.type_max
    }
    return rv
  
  @property
  def json(self):
    rv = self.dict
    return json.dumps(rv)
  
  def dump(self, output: str):
    pass
  
  @property
  def resolution(self):
    return self._resolution


Lights: Dict[str, Spectrum] = {
  'd50': Spectrum('spec/d50.json'),
  'd65': Spectrum('spec/d65.json'),
  'illC': Spectrum('spec/illC.json'),
  'illA': Spectrum('spec/illA.json')
}
