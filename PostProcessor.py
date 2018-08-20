import os
import CONSTANT
from typing import Dict
import numpy as np
from PIL import Image


class PostProcessor:
  def __init__(self, folder: str):
    self.folder = folder
    self.img_shape = None
    self.spectrum = None
    
    all_files = os.listdir(folder)
    # The image should be named like _400_405_410_nm.png
    self.all_images = [x for x in all_files if x.endswith("nm.png")]
    assert len(self.all_images) == CONSTANT.SPEC_LENGTH // 3
  
  def compose(self):
    wave_length_map: Dict[int, np.ndarray] = {}
    for f in self.all_images:
      waves = [int(x) for x in f.split("_")[1:4]]
      tmp_img: np.ndarray = np.array(Image.open(os.path.join(self.folder, f)))
      if self.img_shape is None:
        self.img_shape = tmp_img.shape[:-1]
      elif self.img_shape != tmp_img.shape[:-1]:
        raise ArithmeticError("The image shapes don't match")
      wave_length_map[waves[0]] = tmp_img[:, :, 0].reshape((*self.img_shape, 1))
      wave_length_map[waves[1]] = tmp_img[:, :, 1].reshape((*self.img_shape, 1))
      wave_length_map[waves[2]] = tmp_img[:, :, 2].reshape((*self.img_shape, 1))
    sorted_waves = sorted(wave_length_map.keys())
    spectrum = wave_length_map[sorted_waves[0]]
    for key in sorted_waves[1:]:
      spectrum = np.append(spectrum, wave_length_map[key], axis=2)
    self.spectrum = spectrum
