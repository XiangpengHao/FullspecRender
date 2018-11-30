import numpy as np
import OpenEXR
import logging
import argparse
import os
import Imath
from typing import Dict

from ColorSpace import Spectrum, XYZ, RGB

pixel_type = Imath.PixelType(Imath.PixelType.HALF)


class Converter:
    def __init__(self, input_file):
        assert 'exr' in input_file
        self.input_file = input_file
        self.exr_file = OpenEXR.InputFile(input_file)
        self.channels = self.exr_file.header()['channels']

        dw = self.exr_file.header()['dataWindow']
        self.img_shape = (dw.max.y - dw.min.y + 1, dw.max.x - dw.min.x + 1)
        self.spectrum = self.load_data()

    def load_data(self):
        wave_length_map: Dict[int, np.ndarray] = {}
        for channel, _ in self.channels.items():
            buffed = self.exr_file.channel(channel, pixel_type)
            channel_data = np.frombuffer(buffed, dtype=np.float16)
            channel_data.shape = self.img_shape
            wave_length_map[int(channel)] = channel_data.reshape(
                (*self.img_shape, 1))

        sorted_waves = sorted(wave_length_map.keys())
        spectrum = wave_length_map[sorted_waves[0]]
        for key in sorted_waves[1:]:
            spectrum = np.append(spectrum, wave_length_map[key], axis=2)
        spectrum = np.append(
            spectrum, wave_length_map[sorted_waves[-1]], axis=2)
        return spectrum

    def convert(self):
        rgb_image = np.zeros(
            (self.img_shape[0], self.img_shape[1], 3), dtype=np.double)
        for i in range(self.img_shape[0]):
            for j in range(self.img_shape[1]):
                xyz = Spectrum.spec_to_xyz(self.spectrum[i, j, :])
                rgb_image[i, j, :] = xyz.to_linear_rgb().np_rgb

        dir_path, base_name = os.path.split(self.input_file)
        output = f'{dir_path}/{base_name}_rgb.exr'

        header = OpenEXR.Header(self.img_shape[1], self.img_shape[0])
        half_chan = Imath.Channel(pixel_type)
        header['channels'] = dict([(c, half_chan) for c in 'RGB'])
        exr = OpenEXR.OutputFile(output, header)
        exr.writePixels({'R': rgb_image[:, :, 0].astype(np.float16).tostring(),
                         'G': rgb_image[:, :, 1].astype(np.float16).tostring(),
                         'B': rgb_image[:, :, 2].astype(np.float16).tostring()})
        exr.close()


def arg_parse():
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser(
        description='Compose a set of groundtruth images')
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=False)

    args = vars(parser.parse_args())
    input_path = args['input']
    if os.path.isdir(input_path):
        raise ValueError('Input should not be a directory')

    processor = Converter(input_path)
    processor.convert()


if __name__ == '__main__':
    arg_parse()
