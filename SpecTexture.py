from PIL import Image
import numpy as np
import RGBMatcher
from Spectrum import Spectrum, Lights
from typing import List, Tuple
import pickle
import utils
import multiprocessing as mp
from itertools import product
import warnings
import os
from os import path
import json
import CONSTANT

ROOT_PATH = CONSTANT.ROOT_PATH
TEXTURE_SCALE = 3

SPEC_LENGTH = 60


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
        closet_spec, scale = RGBMatcher.find_nearest_reflectance(cur_rbg)
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


def test_texture():
  input_prefix = r'C:\Users\haoxi\Dropbox\CupSimple\WoodFine26\3K'
  output_prefix = 'rendered/results'
  images = ['cool_small.png', 'nrm_small.png']
  with mp.Pool(len(images)) as p:
    p.starmap(texture_rgb2spec, [(f'{input_prefix}/{x}', f'{output_prefix}/{x}.st') for x in images])


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
  test_expand_texture()
