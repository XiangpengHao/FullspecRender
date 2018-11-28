import os
import OpenEXR
import Imath
import logging
import argparse
import numpy as np

LAYER_MAPPING = [
    {
        'name': 'depth',
        'layers': ['RenderLayer.Depth.Z'],
        'outputs':['Y']
    },
    {
        'name': 'normal',
        'layers': ['RenderLayer.Normal.X', 'RenderLayer.Normal.Y', 'RenderLayer.Normal.Z'],
        'outputs':['R', 'G', 'B']
    }
]
float_pixel = Imath.PixelType(Imath.PixelType.FLOAT)
half_pixel = Imath.PixelType(Imath.PixelType.HALF)


class GroundTruth:
    def __init__(self, input_path: str):
        self.input_path = input_path
        dir_path, base_name = os.path.split(input_path)
        self.output_path = f'{dir_path}/{base_name}' + '{vp}_{postfix}.exr'
        print(self.output_path)
        self.all_files = [x for x in os.listdir(
            input_path) if len(x.split('_')) == 2]
        self.img_shape = None

    def compose(self):
        for f in self.all_files:
            tmp_img = OpenEXR.InputFile(os.path.join(self.input_path, f))
            if self.img_shape is None:
                dw = tmp_img.header()['dataWindow']
                self.img_shape = (dw.max.y - dw.min.y + 1,
                                  dw.max.x - dw.min.x + 1)
            self._compose_one(tmp_img, f)

    def _compose_one(self, exr_img, filename: str)-> np.ndarray:
        for output in LAYER_MAPPING:
            data = {}
            for index, channel in enumerate(output['layers']):
                buffed = exr_img.channel(channel, float_pixel)
                data[output['outputs'][index]] = buffed

            header = OpenEXR.Header(self.img_shape[1], self.img_shape[0])
            float_chan = Imath.Channel(float_pixel)
            header['channels'] = dict([(c, float_chan)
                                       for c in output['outputs']])
            exr = OpenEXR.OutputFile(
                self.output_path.format(vp=filename.split('.')[0], postfix=output['name']), header)
            exr.writePixels(data)
            exr.close()


def arg_parse():
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser(
        description='Compose a set of groundtruth images')
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=False)

    args = vars(parser.parse_args())
    input_path = args['input']
    if not os.path.isdir(input_path):
        raise ValueError('Input should be a directory')

    processor = GroundTruth(input_path)
    processor.compose()


if __name__ == "__main__":
    arg_parse()
