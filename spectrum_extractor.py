import os
import numpy as np
import logging
import argparse
import Imath
import OpenEXR

LAYER_MAPPING = [
    {
        'name': 'combined',
        'layers': ['RenderLayer.Combined.R', 'RenderLayer.Combined.G', 'RenderLayer.Combined.B'],
    },
    {
        'name': 'diffuse_color',
        'layer': ['RenderLayer.DiffCol.R', 'RenderLayer.DiffCol.G', 'RenderLayer.DiffCol.B']
    }, {
        'name': 'diffuse_direct',
        'layer': ['RenderLayer.DiffDir.R', 'RenderLayer.DiffDir.G', 'RenderLayer.DiffDir.B']
    }, {
        'name': 'diffuse_indirect',
        'layer': ['RenderLayer.DiffInd.R', 'RenderLayer.DiffInd.G', 'RenderLayer.DiffInd.B']
    }, {
        'name': 'glossy_color',
        'layer': ['RenderLayer.GlossCol.R', 'RenderLayer.GlossCol.G', 'RenderLayer.GlossCol.B']
    }, {
        'name': 'glossy_direct',
        'layer': ['RenderLayer.GlossDir.R', 'RenderLayer.GlossDir.G', 'RenderLayer.GlossDir.B']
    }, {
        'name': 'glossy_indirect',
        'layer': ['RenderLayer.GlossInd.R', 'RenderLayer.GlossInd.G', 'RenderLayer.GlossInd.B']
    }
]
half_pixel = Imath.PixelType(Imath.PixelType.HALF)


class Extractor:
    def __init__(self, input_path):
        self.folder = input_path
        self.base_path, self.filename = os.path.split(input_path)
        all_files = [x for x in os.listdir(self.input_path) if 'exr' in x]
        self.img_shape = None

    def compose_one(self, layer):
        wave_data = {}
        for f in self.all_files:
            waves = [x for x in f.split('_')[1:4]]
            tmp_img = OpenEXR.InputFile(os.path.join(self.folder, f))

            if self.img_shape is None:
                dw = tmp_img.header()['dataWindow']
                self.img_shape = (dw.max.y - dw.min.y + 1,
                                  dw.max.x - dw.min.x + 1)
            for i, w in enumerate(waves):
                buffed = tmp_img.channel(layer['layer'], half_pixel)
                wave_data[w] = buffed

        header = OpenEXR.Header(self.img_shape[1], self.img_shape[0])
        half_channel = Imath.Channel(half_pixel)
        header['channels'] = dict([(x, half_channel)
                                   for x in wave_data.keys()])
        exr = OpenEXR.OutputFile(os.path.join(self.base_path, f"{self.filename}_{layer['name']}.exr"),
                                 header)
        exr.writePixel(wave_data)
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

    processor = Extractor(input_path)
    processor.compose()


if __name__ == '__main__':
    pass