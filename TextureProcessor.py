from PIL import Image
import numpy as np
from ColorSpace import Spectrum, SpecType, RGB
import pickle
import os
import CONSTANT
import argparse

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
  
  def to_spectrum(self, output: str = ''):
    rv_texture = np.zeros((*self.img_shape, CONSTANT.SPEC_LENGTH), dtype=np.uint8)
    for i in range(self.img_shape[0]):
      for j in range(self.img_shape[1]):
        rgb = RGB(*(self.img[i, j] / 255))
        spectrum, scale = rgb.to_spectrum()
        # d_orgb = Spectrum.spec_to_xyz(np.multiply(spectrum.data, CONSTANT.COMMON_LIGHTS["d65"].data))
        #
        scaled_value = spectrum.data * scale / 2 * 255 * CONSTANT.SPECTRUM_SCALE
        rv_texture[i, j] = np.rint(scaled_value).clip(0, 255).astype(np.uint8)
        # new_rgb = Spectrum.spec_to_xyz(
        #   np.multiply(rv_texture[0, 0] / 255 / CONSTANT.SPECTRUM_SCALE, CONSTANT.COMMON_LIGHTS["d65"].data)).to_srgb()
      print("[to spectrum]: now at line: ", i)
    
    if output == '':
      dir_path, base_name = os.path.split(self.path)
      file_name = f"{base_name.split('.')[0]}.st"
      output = os.path.join(dir_path, file_name)
    
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


def arg_parse():
  parser = argparse.ArgumentParser(description="Texture processing")
  parser.add_argument("-i", "--input", required=True)
  parser.add_argument("-a", "--action", required=False)
  parser.add_argument("-o", "--output", required=False)
  parser.add_argument("-l", "--light", required=False)
  args = vars(parser.parse_args())
  
  input_file = args["input"]
  output = args.get("output")
  action = args.get("action")
  if action is None and output is None:
    file_type = input_file.split(".")[-1]
    if file_type == "jpg":
      RGBProcessor(file_path=input_file).to_spectrum()
    elif file_type == "st":
      light_str: str = args.get("light")
      if light_str is None:
        light: Spectrum = CONSTANT.COMMON_LIGHTS["d65"]
      elif light_str in CONSTANT.COMMON_LIGHTS:
        light: Spectrum = CONSTANT.COMMON_LIGHTS[light_str]
      else:
        raise NotImplementedError("Unsupported light")
      SpectrumProcessor(file_path=input_file).preview_under_light(light=light)
    else:
      raise NotImplementedError()
  print(args)


if __name__ == '__main__':
  arg_parse()
