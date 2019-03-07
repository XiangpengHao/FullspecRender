import os
import subprocess
import numpy as np
import logging
import argparse
import Imath
import OpenEXR
from joblib import Parallel, delayed

LAYER_MAPPING = [
    {
        'name': 'combined',
        'layers': ['RenderLayer.Combined.R', 'RenderLayer.Combined.G', 'RenderLayer.Combined.B'],
    },
    {
        'name': 'diffuse_color',
        'layers': ['RenderLayer.DiffCol.R', 'RenderLayer.DiffCol.G', 'RenderLayer.DiffCol.B']
    }, {
        'name': 'diffuse_direct',
        'layers': ['RenderLayer.DiffDir.R', 'RenderLayer.DiffDir.G', 'RenderLayer.DiffDir.B']
    }, {
        'name': 'diffuse_indirect',
        'layers': ['RenderLayer.DiffInd.R', 'RenderLayer.DiffInd.G', 'RenderLayer.DiffInd.B']
    }, {
        'name': 'glossy_color',
        'layers': ['RenderLayer.GlossCol.R', 'RenderLayer.GlossCol.G', 'RenderLayer.GlossCol.B']
    }, {
        'name': 'glossy_direct',
        'layers': ['RenderLayer.GlossDir.R', 'RenderLayer.GlossDir.G', 'RenderLayer.GlossDir.B']
    }, {
        'name': 'glossy_indirect',
        'layers': ['RenderLayer.GlossInd.R', 'RenderLayer.GlossInd.G', 'RenderLayer.GlossInd.B']
    }
]
half_pixel = Imath.PixelType(Imath.PixelType.HALF)


class Extractor:
    def __init__(self, input_path):
        self.folder = input_path
        self.base_path, self.filename = os.path.split(input_path)
        self.all_files = [x for x in os.listdir(input_path) if 'exr' in x]
        self.img_shape = None

    def compose_all(self, layers):
        for layer in layers:
            self.compose_one(layer)

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
                buffed = tmp_img.channel(layer['layers'][i], half_pixel)
                wave_data[w] = buffed

        header = OpenEXR.Header(self.img_shape[1], self.img_shape[0])
        half_channel = Imath.Channel(half_pixel)
        header['compression'] = Imath.Compression(
            Imath.Compression.PIZ_COMPRESSION)
        header['channels'] = dict([(x, half_channel)
                                   for x in wave_data.keys()])
        exr = OpenEXR.OutputFile(os.path.join(self.base_path, f"{self.filename}_{layer['name']}.exr"),
                                 header)
        exr.writePixels(wave_data)
        exr.close()


def clean_up(base_path):
    os.mkdir(os.path.join(base_path, 'combined'))
    os.mkdir(os.path.join(base_path, 'diffuse'))
    os.mkdir(os.path.join(base_path, 'glossy'))
    subprocess.run(
        [f'mv {base_path}/vp*_combined.exr {base_path}/combined'], shell=True)
    subprocess.run(
        [f'mv {base_path}/vp*diffuse*.exr {base_path}/diffuse'], shell=True)
    subprocess.run(
        [f'mv {base_path}/vp*glossy*.exr {base_path}/glossy'], shell=True)


def parallel_job(d):
    print("working on ", d)
    processor = Extractor(d)
    processor.compose_all(LAYER_MAPPING)


def arg_parse():
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser(
        description='Compose a set of groundtruth images')
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=False)
    parser.add_argument("-d", "--dir", action="store_true")

    args = vars(parser.parse_args())
    input_path = args['input']
    if not os.path.isdir(input_path):
        raise ValueError('Input should be a directory')

    if args['dir']:
        sorted_dir = sorted(os.listdir(input_path))
        dirs = [os.path.join(input_path, x) for x in sorted_dir if
                os.path.isdir(os.path.join(input_path, x))]
        Parallel(n_jobs=10)(delayed(parallel_job)(d) for d in dirs)
        clean_up(input_path)
    else:
        processor = Extractor(input_path)
        processor.compose_all(LAYER_MAPPING)


if __name__ == '__main__':
    arg_parse()
