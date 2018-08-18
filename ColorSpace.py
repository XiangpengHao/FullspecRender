from __future__ import annotations
from typing import List, Union, Dict
import json
import numpy as np
import utils
from enum import Enum
import CONSTANT


class SpecType(Enum):
  REFLECTANCE = 0
  ILLUMINANT = 1
  COLOR_MATCH = 2


class RGB:
  def __init__(self, r: float, g: float, b: float, spec_type: SpecType = SpecType.REFLECTANCE):
    self.r: float = r
    self.g: float = g
    self.b: float = b
    self.spec_type: SpecType = spec_type
    self.np_rgb: np.ndarray = np.asarray([r, g, b])
  
  def to_xyz(self) -> XYZ:
    rgb_gamma_rev = [utils.gamma_correct_rev(v) for v in self.np_rgb]
    xyz = np.matmul(utils.RGB2XYZ, rgb_gamma_rev)
    return XYZ(xyz[0], xyz[1], xyz[2])
  
  def to_spectrum(self) -> (Spectrum, float):
    xyz = self.to_xyz()
    return xyz.to_spectrum()


class XYZ:
  def __init__(self, x: float, y: float, z: float, spec_type: SpecType = SpecType.REFLECTANCE):
    self.x: float = x
    self.y: float = y
    self.z: float = z
    self.spec_type: SpecType = spec_type
    self.np_xyz: np.ndarray = np.asarray([x, y, z])
  
  def norm(self) -> XYZ:
    xyz_sum = sum(self.np_xyz)
    return XYZ(self.x / xyz_sum, self.y / xyz_sum, self.z / xyz_sum)
  
  def to_srgb(self) -> RGB:
    rgb = np.matmul(utils.XYZ2RGB, self.np_xyz)
    return RGB(utils.gamma_correct(rgb[0]),
               utils.gamma_correct(rgb[1]),
               utils.gamma_correct(rgb[2]))
  
  def to_spectrum(self) -> (Spectrum, float):
    xyz = self.norm()
    if self.spec_type == SpecType.REFLECTANCE:
      _, index = CONSTANT.REFLECTANCE_KDD.query(xyz)
      return CONSTANT.REFLECTANCE[index], xyz.y / CONSTANT.REFLECTANCE[index].xyz.y
    elif self.spec_type == SpecType.ILLUMINANT:
      _, index = CONSTANT.ILLUMINANT_KDD.query(xyz)
      return CONSTANT.ILLUMINANT[index], xyz.y / CONSTANT.ILLUMINANT[index].xyz.y
    else:
      raise NotImplementedError()


class Spectrum:
  def __init__(self, spec_file: Union[str, dict]):
    self.name: str
    self.type: str
    if type(spec_file) == str:
      with open(spec_file) as f:
        data = json.load(f)
    else:
      data = spec_file
    self.name: str = data.get('name')
    self.type: str = data.get('type')
    self.start_nm: int = data.get('start_nm')
    self.end_nm: int = data.get('end_nm')
    self._resolution: int = data.get('resolution')
    self.rgb: RGB = RGB(*data.get('rgb'))
    self.xyz: XYZ = XYZ(*data.get('xyz'))
    self.np_xyz: np.ndarray = self.xyz.np_xyz
    self.np_rgb: np.ndarray = self.rgb.np_rgb
    self.type_max = data.get('type_max')
    self.data: List[float] = [x / data.get('type_max') for x in data.get('data')]
  
  def __getitem__(self, item):
    if isinstance(item, slice):
      if item.start < self.start_nm or item.stop > self.end_nm:
        raise ArithmeticError("nm not in range")
      start_i = (item.start - self.start_nm) // self.resolution
      end_i = (item.stop - self.start_nm) // self.resolution
      print(self.data[start_i:end_i])
      return self.data[start_i:end_i]
  
  def to_xyz(self) -> XYZ:
    x_data: float = np.dot(self.data, ColorMatch['x'].data)
    y_data: float = np.dot(self.data, ColorMatch['y'].data)
    z_data: float = np.dot(self.data, ColorMatch['z'].data)
    return XYZ(*[x_data, y_data, z_data])
  
  def to_rgb(self):
    xyz = self.to_xyz()
    return xyz.to_srgb()
  
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

ColorMatch: Dict[str, Spectrum] = {
  "x": Spectrum("spec/x.json"),
  "y": Spectrum("spec/y.json"),
  "z": Spectrum("spec/z.json")
}
