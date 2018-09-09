import numpy as np
from PIL import Image
import os
import os.path
import pickle
from typing import Tuple, List, Dict
import utils
import warnings
import CONSTANT

ROOT_PATH = '/home/hao/ownCloud/FullSpecRendering/' if os.name == 'posix' else \
  '/mnt/e/ownCloud/FullSpecRendering'


class SpecImage:
  def __init__(self):
    self.img_shape: Tuple[int, int] = None
    self.spectrum: np.ndarray = None
    self.wave_interval: Tuple[int, int] = None
    self.xyz_data: np.ndarray = None
    self._relative_dir: str = os.path.dirname(__file__)
    self._load_xyz()
  
  def _load_xyz(self):
    self.xyz_data = np.loadtxt('spec/color_match.csv')
  
  def load_spec_from_dir(self, path: str):
    all_images = os.listdir(path)
    rv = {}
    for f in all_images:
      if not f.endswith('nm.png'):
        continue
      lengths = [int(x) for x in f.split('_')[1:4]]
      tmp_img = Image.open(os.path.join(path, f))
      np_img = np.array(tmp_img)
      if self.img_shape is None:
        # shape is (h, w, rgba)
        # now it's (h, w)
        self.img_shape = np_img.shape[:-1]
      elif self.img_shape != np_img.shape[:-1]:
        raise ArithmeticError("The images should be save shape")
      rv[lengths[0]] = np_img[:, :, 0].reshape((*self.img_shape, 1))
      rv[lengths[1]] = np_img[:, :, 1].reshape((*self.img_shape, 1))
      rv[lengths[2]] = np_img[:, :, 2].reshape((*self.img_shape, 1))
    sorted_keys = sorted(rv.keys())
    spectrum = rv[sorted_keys[0]]
    for key in sorted_keys[1:]:
      spectrum = np.append(spectrum, rv[key], axis=2)
    self.spectrum = spectrum
    self.wave_interval = (sorted_keys[0], sorted_keys[-1])
  
  def save_spec_to_fsi(self, path: str):
    if self.spectrum is None:
      raise ArithmeticError("The spectrum data is None")
    serialized = {
      'shape': self.img_shape,
      'wave_interval': self.wave_interval,
      'spectrum': self.spectrum
    }
    with open(path, 'wb') as f:
      pickle.dump(serialized, f, pickle.HIGHEST_PROTOCOL)
  
  def load_from_fsi(self, path: str):
    with open(path, 'rb') as f:
      data = pickle.load(f)
    self.img_shape = data['shape']
    self.spectrum = data['spectrum']
    self.wave_interval = data['wave_interval']
  
  def spec_to_rgb(self, path: str):
    if self.spectrum is None:
      raise ArithmeticError("Spectrum is None")
    rgb_data = np.zeros((*self.img_shape, 3), dtype=np.uint8)
    for i in range(self.img_shape[0]):
      for j in range(self.img_shape[1]):
        xyz = utils.spec_to_xyz(self.spectrum[i, j, :] / 512)
        rgb = utils.xyz_to_srgb(np.asarray(xyz))
        if min(rgb) < 0 or max(rgb) > 1:
          warnings.warn(f"unexpected rgb: {rgb}", stacklevel=2)
        rgb_data[i, j, :] = np.asarray(
          [int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)])
    img = Image.fromarray(rgb_data, 'RGB')
    img.save(path)
  
  def spec_to_xyz_to_rgb(self, path: str):
    if self.spectrum is None:
      raise ValueError('Spectrum is none')
    xyz_data = np.zeros((*self.img_shape, 3), dtype=np.double)
    for i in range(self.img_shape[0]):
      for j in range(self.img_shape[1]):
        xyz = utils.spec_to_xyz(self.spectrum[i, j, :])
        xyz_data[i, j, :] = xyz
    max_xyz = np.amax(xyz_data) * 1
    xyz_data /= max_xyz
    rgb_data = np.zeros((*self.img_shape, 3), dtype=np.uint8)
    for i in range(self.img_shape[0]):
      for j in range(self.img_shape[1]):
        cur_xyz = xyz_data[i, j, :]
        rgb = utils.xyz_to_srgb(cur_xyz)
        if min(rgb) < 0 or max(rgb) > 1:
          warnings.warn(f"unexpected rgb: {rgb}, xyz in srgb: {utils.xyz_in_srgb(cur_xyz)}", stacklevel=1)
          rgb = np.clip(rgb, 0, 1)
        rgb_data[i, j, :] = np.asarray(
          [int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)])
    img = Image.fromarray(rgb_data, 'RGB')
    img.save(path)


if __name__ == '__main__':
  spec_img = SpecImage()
  # sequence = 15
  model = 'pavillon'
  for v in range(11, 12):
    vp = f'vp_{v}'
    spec_img.load_spec_from_dir(os.path.join(CONSTANT.ROOT_PATH, f"rendered/{model}/{vp}"))
    spec_img.save_spec_to_fsi(f'rendered/fsi/test{vp}.fsi')
    spec_img.load_from_fsi(f'rendered/fsi/test{vp}.fsi')
    print("now rendering ", vp)
    spec_img.spec_to_xyz_to_rgb(os.path.join(CONSTANT.ROOT_PATH, 'rendered', model, f'test_{vp}.png'))
