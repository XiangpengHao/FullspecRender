from PIL import Image
import numpy as np
import Database
from ColorSpace import Spectrum, SpecType, RGB
from typing import List, Tuple
import pickle
import utils
import multiprocessing as mp
from itertools import product
import warnings
import os
import json
import CONSTANT

ROOT_PATH = CONSTANT.ROOT_PATH
TEXTURE_SCALE = 3

SPEC_LENGTH = 60


class RGBProcessor:
  def __init__(self, file_path: str, texture_type: SpecType = SpecType.REFLECTANCE):
    self.path = file_path
    self.texture_type = texture_type
    self.img: np.ndarray = np.asarray(Image.open(file_path))
    if len(self.img[0, 0]) != 3:
      raise NotImplementedError("Only jpg format is supported")
    self.img_shape = self.img.shape[:-1]
  
  def to_spectrum(self, output: str):
    rv_texture = np.zeros((*self.img_shape, CONSTANT.SPEC_LENGTH), dtype=np.uint8)
    for i in range(self.img_shape[0]):
      for j in range(self.img_shape[1]):
        rgb = RGB(*(self.img[i, j] / 255))
        spectrum, scale = rgb.to_spectrum()
        scaled_value = spectrum.data * scale * 255 * CONSTANT.SPECTRUM_SCALE
        rv_texture[i, j] = np.rint(scaled_value).clip(0, 255).astype(np.uint8)
      print("[to spectrum]: now at line: ", i)
    with open(output, 'wb') as f:
      output_dict = {
        "source_path": self.path,
        "texture_type": self.texture_type,
        "spectrum": rv_texture
      }
      pickle.dump(output_dict, f, pickle.HIGHEST_PROTOCOL)


class SpectrumProcessor:
  def __init__(self, file_path: str):
    with open(file_path, 'rb') as f:
      data = pickle.load(f)
    self.path: str = file_path
    self.source_path: str = data["source_path"]
    self.texture_type: SpecType = data["texture_type"]
    self.spectrum: np.ndarray = data["spectrum"]
    self.img_shape: (float, float) = self.spectrum.shape[:-1]
  
  def preview_under_light(self, light: Spectrum = CONSTANT.COMMON_LIGHTS["d65"], output: str = None):
    rv_img = np.zeros((*self.img_shape, 3), dtype=np.uint8)
    for i in range(self.img_shape[0]):
      for j in range(self.img_shape[1]):
        spec_data = np.multiply(self.spectrum[i, j], light.data) / 255 / CONSTANT.SPECTRUM_SCALE
        rgb = Spectrum.spec_to_xyz(spec_data).to_srgb().to_uint8()
        rv_img[i, j:] = rgb
    img = Image.fromarray(rv_img)
    if output is None:
      dir_path, base_name = os.path.split(self.path)
      file_name = f"{base_name.split('.')[0]}_{light.name}.jpg"
      output_path = os.path.join(dir_path, file_name)
    else:
      output_path = output
    img.save(output_path)
  
  def expand_texture(self, output: str = None):
    if output is None:
      dir_path, base_name = os.path.split(self.path)
      file_name = base_name.split('.')[0]
      output_path = os.path.join(dir_path, file_name)
    else:
      output_path = output
    if not os.path.exists(output_path):
      os.mkdir(output_path)
    
    result = np.zeros((*self.img_shape, 3), dtype=np.uint8)
    for wave_len in range(0, CONSTANT.SPEC_LENGTH, 3):
      print("[expand] Now output wavelength: ", wave_len)
      for i in range(self.img_shape[0]):
        for j in range(self.img_shape[1]):
          tmp = self.spectrum[i, j, wave_len:wave_len + 3]
          result[i, j] = tmp
      
      output_wavelength = 400 + wave_len * 5
      Image.fromarray(result).save(
        f'{output_path}/_{output_wavelength}_{output_wavelength+5}_{output_wavelength+10}_nm.jpg'
      )
    print("[expand] Done.")


class SpecTexture:
  img_path: str
  rgb_img: np.ndarray
  img_shape: Tuple[int, int]
  spectrum: np.ndarray
  
  def __init__(self):
    pass
  
  def load_spec(self, path: str):
    with open(path, 'rb') as f:
      data = pickle.load(f)
    self.img_shape = data.shape[:-1]
    self.spectrum = data
  
  def load_rgb(self, path: str):
    self.img_path = path
    self.rgb_img = np.asarray(Image.open(path).convert('RGB'))
    assert len(self.rgb_img[0, 0]) == 3
    self.img_shape = self.rgb_img.shape[:-1]
  
  def expand_spec(self, output_dir: str, ext: str):
    """
    self.spectrum is in [0, 255]
    """
    if not os.path.exists(output_dir):
      os.mkdir(output_dir)
    
    result = np.zeros((*self.img_shape, 3), dtype=np.uint8)
    for wave_len in range(0, SPEC_LENGTH, 3):
      print(f"Now output wave_len: {wave_len}")
      for i in range(self.img_shape[0]):
        for j in range(self.img_shape[1]):
          tmp = self.spectrum[i, j, wave_len:wave_len + 3]
          result[i, j] = tmp
      Image.fromarray(result, 'RGB').save(
        f'{output_dir}/_{400+wave_len*5}_{400+wave_len*5+5}_{400+wave_len*5+10}_nm.{ext}')
  
  def spec_to_pixel_rgb(self, output: str, light: Spectrum):
    result = np.zeros((*self.img_shape, 3), dtype=np.uint8)
    for i in range(self.img_shape[0]):
      for j in range(self.img_shape[1]):
        dot_data = np.multiply(self.spectrum[i, j], light.data) / 255 / CONSTANT.SPECTRUM_SCALE
        rgb = np.asarray(utils.spec_to_rgb(dot_data))
        if np.min(rgb) < 0 or np.max(rgb) > 1:
          rgb = np.clip(rgb, 0, 1)
          print(f'normed rgb: {rgb}')
        result[i, j, :] = np.asarray([int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)]).astype(np.uint8)
      print(f'now: {i}')
    img = Image.fromarray(result, 'RGB')
    img.save(output)
  
  def rgb_to_spec(self, file_name: str):
    spec = np.zeros((*self.img_shape, SPEC_LENGTH), dtype=np.uint8)
    warnings.warn(f'check rgb value: {self.rgb_img[10,10]}')
    for i in range(self.img_shape[0]):
      for j in range(self.img_shape[1]):
        cur_rbg = self.rgb_img[i, j] / 255
        closet_spec, scale = Database.find_nearest_reflectance(cur_rbg)
        tmp = np.asarray(closet_spec.data) * scale * CONSTANT.SPECTRUM_SCALE * 255
        spec[i, j] = np.rint(tmp).astype(np.uint8)
      print(f'now line: {i}')
    self.spectrum = spec
    with open(file_name, 'wb') as f:
      pickle.dump(spec, f, pickle.HIGHEST_PROTOCOL)
  
  @staticmethod
  def rgb_to_y(rgb: np.ndarray) -> float:
    return rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114


def texture_rgb2spec(img: str, output: str):
  texture_0 = SpecTexture()
  texture_0.load_rgb(img)
  texture_0.rgb_to_spec(output)
  print(f'job done {output}')


def expand_texture(st_file: str, output: str, ext='jpg'):
  texture = SpecTexture()
  texture.load_spec(st_file)
  texture.expand_spec(output, ext)


def texture_under_light(st_file: str, output: str, light: Spectrum):
  texture = SpecTexture()
  texture.load_spec(st_file)
  texture.spec_to_pixel_rgb(output, light)


model_path = 'Barce279/3d'


def test_expand_texture():
  abs_model_path = os.path.join(ROOT_PATH, model_path)
  path2config = os.path.join(abs_model_path, 'config.json')
  model_config = json.load(open(path2config))
  
  with mp.Pool(mp.cpu_count() - 1) as p:
    p.starmap(expand_texture, [(
      path.join(abs_model_path, model_config['texturePath'], x),
      path.join(abs_model_path, f"intermediate/{x.split('.')[0]}"),
      'jpg'
    ) for x in model_config['textures']])


if __name__ == '__main__':
  # texture_under_light('/home/hao/ownCloud/Barce279/3d/full_texture/leaf-veins.jpg.st',
  #                     'rendered/results/aa.jpg', Spectrum('spec/d65.json'))
  texture_rgb2spec(
    "/Volumes/Shared/ownCloud/Barce279/3d/origin/DSC_8129.jpg",
    "/Volumes/Shared/ownCloud/Barce279/3d/origin/DSC_8129.jpg.st")
