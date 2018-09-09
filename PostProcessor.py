import os
import CONSTANT
from typing import Dict
import numpy as np
from PIL import Image
from ColorSpace import Spectrum, XYZ, RGB
import warnings
import os
import argparse


class PostProcessor:
  def __init__(self, folder: str):
    self.folder = folder
    self.img_shape = None
    self.spectrum = None
    
    all_files = os.listdir(folder)
    # The image should be named like _400_405_410_nm.png
    self.all_images = [x for x in all_files if x.endswith("nm.png") and not x.startswith('.')]
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
    # interpolate the spectrum from 60 values to 61 values
    spectrum = np.append(spectrum, wave_length_map[sorted_waves[-1]], axis=2)
    
    self.spectrum = spectrum
  
  def output_as_srgb(self, output: str = None):
    if self.spectrum is None:
      raise ValueError("Spectrum is none")
    xyz_image = np.zeros((*self.img_shape, 3), dtype=np.double)
    for i in range(self.img_shape[0]):
      for j in range(self.img_shape[1]):
        xyz = Spectrum.spec_to_xyz(self.spectrum[i, j, :])
        xyz_image[i, j, :] = xyz.np_xyz
    max_xyz = np.amax(xyz_image)
    xyz_image /= max_xyz
    
    rgb_image = np.zeros((*self.img_shape, 3), dtype=np.uint8)
    for i in range(self.img_shape[0]):
      for j in range(self.img_shape[1]):
        rgb = XYZ(*xyz_image[i, j, :]).to_srgb()
        rgb_image[i, j, :] = rgb.to_uint8()
    img = Image.fromarray(rgb_image, "RGB")
    
    if output is None:
      dir_path, base_name = os.path.split(self.folder)
      output = f'{dir_path[:-1]}_{base_name}.png'
    img.save(output)


def arg_parse():
  parser = argparse.ArgumentParser(description="Compose a set of source images to full spectrum images")
  parser.add_argument("-i", "--input", required=True)
  parser.add_argument("-o", "--output", required=False)
  args = vars(parser.parse_args())
  input_path = args["input"]
  if not os.path.isdir(input_path):
    raise ValueError("input should be a directory")
  processor = PostProcessor(input_path)
  processor.compose()
  processor.output_as_srgb()


if __name__ == "__main__":
  arg_parse()
