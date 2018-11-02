import os
import CONSTANT
from typing import Dict
import numpy
import numpy as np
from PIL import Image
from ColorSpace import Spectrum, XYZ, RGB
import os
import logging
import argparse
import utils
import OpenEXR, Imath
from joblib import Parallel, delayed

logger = logging.getLogger(__name__)

CHANNELS=["Composite.Combined.R","Composite.Combined.G","Composite.Combined.B"]

class PostProcessor:
  def __init__(self, folder: str):
    self.folder = folder
    self.img_shape = None
    self.spectrum = None
    
    all_files = os.listdir(folder)
    # The image should be named like _400_405_410_nm.png
    self.all_images = [x for x in all_files if x.startswith("_")]

    if self.all_images[0].endswith('.png'):
      self.file_type='png'
    elif self.all_images[0].endswith('.exr'):
      self.file_type='exr'

    if len(self.all_images) != CONSTANT.SPEC_LENGTH // 3:
      raise AssertionError(f'Invalid spectrum folder: {folder}')

  def png_data_loader(self):
    wave_length_map: Dict[int, np.ndarray] = {}
    for f in self.all_images:
      waves = [int(x) for x in f.split("_")[1:4]]
      tmp_img: np.ndarray = np.array(Image.open(os.path.join(self.folder, f))) / 255
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
  
  def exr_data_loader(self):
    wave_length_map:Dict[int,np.ndarray] = {}
    pixel_type=Imath.PixelType(Imath.PixelType.HALF)
    for f in self.all_images:
      waves = [int(x) for x in f.split("_")[1:4]]
      tmp_img=OpenEXR.InputFile(os.path.join(self.folder,f))
      if self.img_shape is None:
        dw = tmp_img.header()['dataWindow']
        self.img_shape=(dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)
      for i,w in enumerate(waves):
        buffed=tmp_img.channel(CHANNELS[i],pixel_type)
        channel_data=np.frombuffer(buffed,dtype=np.float16).astype(np.float32)
        channel_data.shape=self.img_shape
        wave_length_map[w]=channel_data.reshape((*self.img_shape,1))
    sorted_waves=sorted(wave_length_map.keys())
    spectrum=wave_length_map[sorted_waves[0]]
    for key in sorted_waves[1:]:
      spectrum=np.append(spectrum, wave_length_map[key], axis=2)
    spectrum=np.append(spectrum, wave_length_map[sorted_waves[-1],axis=2])
    self.spectrum=spectrum


  
  def compose(self):
    wave_length_map: Dict[int, np.ndarray] = {}
    for f in self.all_images:
      waves = [int(x) for x in f.split("_")[1:4]]
      tmp_img: np.ndarray = np.array(Image.open(os.path.join(self.folder, f))) / 255
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
  
  @staticmethod
  def _undo_gamma_correction(spectrum: np.ndarray):
    return utils.np_gamma_correct_rev(spectrum)
  
  def output_as_srgb(self, output: str = None, verbose=False):
    if self.spectrum is None:
      raise ValueError("Spectrum is none")
    xyz_image = np.zeros((self.img_shape[0], self.img_shape[1], 3), dtype=np.double)
    self.spectrum = utils.np_gamma_correct_rev(self.spectrum)
    
    for i in range(self.img_shape[0]):
      for j in range(self.img_shape[1]):
        xyz = Spectrum.spec_to_xyz(self.spectrum[i, j, :])
        xyz_image[i, j, :] = xyz.np_xyz
    max_xyz = np.amax(xyz_image)
    xyz_image /= max_xyz
    
    rgb_image = np.zeros((self.img_shape[0], self.img_shape[1], 3), dtype=np.uint8)
    for i in range(self.img_shape[0]):
      for j in range(self.img_shape[1]):
        rgb = XYZ(*xyz_image[i, j, :]).to_srgb()
        rgb_image[i, j, :] = rgb.to_uint8(verbose)
    img = Image.fromarray(rgb_image, "RGB")
    
    if output is None:
      dir_path, base_name = os.path.split(self.folder)
      output = '{}/{}.png'.format(dir_path, base_name)
    img.save(output)


def parallel_output(f):
  try:
    processor = PostProcessor(f)
    processor.compose()
    processor.output_as_srgb(verbose=False)
  except AssertionError as e:
    logger.error(e)

def arg_parse():
  logging.basicConfig(filename="PostProcess.log", level=logging.WARNING)
  parser = argparse.ArgumentParser(description="Compose a set of source images to full spectrum images")
  parser.add_argument("-i", "--input", required=True)
  parser.add_argument("-o", "--output", required=False)
  parser.add_argument("-v", "--verbose", action='store_true')
  parser.add_argument("-d", "--dir", action='store_true')
  args = vars(parser.parse_args())
  input_path = args["input"]
  if not os.path.isdir(input_path):
    raise ValueError("input should be a directory")
  if args['dir']:
    sorted_dir = sorted(os.listdir(input_path))
    dirs = [os.path.join(input_path, x) for x in sorted_dir if
            os.path.isdir(os.path.join(input_path, x))]
    Parallel(n_jobs=8)(delayed(parallel_output)(x) for x in dirs)
  else:
    processor = PostProcessor(input_path)
    processor.compose()
    processor.output_as_srgb(verbose=args['verbose'])


if __name__ == "__main__":
  arg_parse()
