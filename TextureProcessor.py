from PIL import Image
import numpy as np
from ColorSpace import Spectrum, SpecType, RGB
import pickle
import os
import CONSTANT
import argparse
from joblib import Parallel, delayed

ROOT_PATH = CONSTANT.ROOT_PATH
TEXTURE_SCALE = 3


class RGBProcessor:
  def __init__(self, file_path: str, texture_type: SpecType = SpecType.REFLECTANCE):
    self.path = file_path
    self.texture_type = texture_type
    self.img: np.ndarray = np.asarray(Image.open(file_path))
    if len(self.img[0, 0]) != 3:
      raise NotImplementedError("Only jpg format is supported")
    self.img_shape = self.img.shape[:-1]
  
  def _parallel_to_spectrum_line(self, i):
    print("[to spectrum]: now at line: ", i)
    line_result = np.zeros((self.img_shape[1], CONSTANT.SPEC_LENGTH), dtype=np.uint8)
    for j in range(self.img_shape[1]):
      rgb = RGB(*(self.img[i, j] / 255))
      spectrum, scale = rgb.to_spectrum()
      scaled_value = spectrum.data * scale * 255 * CONSTANT.SPECTRUM_SCALE
      line_result[j] = np.rint(scaled_value).clip(0, 255).astype(np.uint8)
    return line_result
  
  def to_spectrum(self, output: str = '', parallel=None):
    rv_texture = np.zeros((*self.img_shape, CONSTANT.SPEC_LENGTH), dtype=np.uint8)
    if parallel is None:
      results = Parallel(n_jobs=CONSTANT.CPU_CORES)(
        delayed(self._parallel_to_spectrum_line)(i) for i in range(self.img_shape[0]))
    else:
      results = parallel(delayed(self._parallel_to_spectrum_line)(i) for i in range(self.img_shape[0]))
    for i in range(self.img_shape[0]):
      rv_texture[i, :, :] = results[i]
    
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
  
  def preview_under_light(self, light: Spectrum = None, output: str = None):
    if light is None:
      light = CONSTANT.COMMON_LIGHTS["d65"]
    rv_img = np.zeros((*self.img_shape, 3), dtype=np.uint8)
    for i in range(self.img_shape[0]):
      for j in range(self.img_shape[1]):
        spec_data = np.multiply(self.spectrum[i, j], light.data) / 255 / CONSTANT.SPECTRUM_SCALE
        rgb = Spectrum.spec_to_xyz(spec_data).to_srgb(norm=False).to_uint8()
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
    
    for wave_len in range(0, CONSTANT.SPEC_LENGTH - 1, 3):
      print("[expand] Now output wavelength: ", wave_len)
      result = self.spectrum[:, :, wave_len:wave_len + 3]
      
      output_wavelength = 400 + wave_len * 5
      Image.fromarray(result).save(
        f'{output_path}/_{output_wavelength}_{output_wavelength+5}_{output_wavelength+10}_nm.jpg'
      )
    print("[expand] Done.")


def cli_handle_st(args: dict):
  light = CONSTANT.COMMON_LIGHTS.get(args.get("light"))
  action = args.get("action")
  if action is None or action == "preview":
    SpectrumProcessor(file_path=args["input"]).preview_under_light(light=light)
  elif action == "expand":
    SpectrumProcessor(file_path=args["input"]).expand_texture()
  else:
    raise NotImplementedError()


def cli_handle_jpg(args: dict):
  RGBProcessor(file_path=args["input"]).to_spectrum()


def cli_handle_dir(dirname: str, args: dict):
  action = args.get('action')
  if action is None or action == 'jpg':
    all_pics_jpg = [p for p in os.listdir(dirname)
                    if p.endswith('jpg') and not p.startswith('.')]
    with Parallel(n_jobs=CONSTANT.CPU_CORES) as parallel:
      for x in all_pics_jpg:
        print(f"working on {x}")
        RGBProcessor(file_path=os.path.join(dirname, x)).to_spectrum(parallel=parallel)
  elif action == 'expand':
    all_pics_st = [p for p in os.listdir(dirname)
                   if p.endswith('.st') and not p.startswith('.')]
    prefix, basename = os.path.split(dirname)
    output = os.path.join(prefix, f'{basename}_expanded')
    if not os.path.exists(output):
      os.mkdir(output)
    for p in all_pics_st:
      print(p)
      SpectrumProcessor(file_path=os.path.join(dirname, p)).expand_texture(
        os.path.join(output, p.split('.')[0]))
  else:
    raise NotImplementedError()


def arg_parse():
  parser = argparse.ArgumentParser(description="Texture processing")
  parser.add_argument("-i", "--input", required=True)
  parser.add_argument("-a", "--action", required=False)
  parser.add_argument("-o", "--output", required=False)
  parser.add_argument("-l", "--light", required=False, choices=CONSTANT.COMMON_LIGHTS.keys())
  parser.add_argument("-t", "--type", required=False, choices=["illuminant", "reflectance"])
  args = vars(parser.parse_args())
  
  input_file: str = args["input"]
  if os.path.isdir(input_file):
    return cli_handle_dir(input_file, args)
  
  file_type = input_file.split(".")[-1]
  if file_type == "st":
    cli_handle_st(args)
  elif file_type == "jpg":
    cli_handle_jpg(args)
  else:
    raise NotImplementedError("Unsupported file extension")


if __name__ == '__main__':
  arg_parse()
