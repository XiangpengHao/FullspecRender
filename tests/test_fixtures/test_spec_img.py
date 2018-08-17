from AssembleImage import SpecImage
import pickle
import unittest
import os.path
from PIL import Image
import numpy as np


class TestSpecImage(unittest.TestCase):
    spec_img = SpecImage()

    def test_xyz_data(self):
        self.assertEqual(self.spec_img.xyz_data.shape, (60, 3))
        self.assertAlmostEqual(self.spec_img.xyz_data[0, 0], 2.214302E-02)

    def test_load_spec_from_source(self):
        self.spec_img.load_spec_from_dir(
            os.path.abspath('tests/test_fixtures'))

        with open(os.path.abspath('tests/test_fixtures/test01.fsi'), 'rb') as f:
            test_data = pickle.load(f)

        self.assertEqual(self.spec_img.wave_interval,
                         test_data['wave_interval'])
        self.assertEqual(self.spec_img.img_shape,
                         test_data['shape'])
        self.assertEqual(self.spec_img.spectrum[0, 0, 0],
                         test_data['spectrum'][0, 0, 0])

    def test_fsi_to_rgb(self):
        self.spec_img.load_from_fsi('tests/test_fixtures/test01.fsi')
        self.spec_img.spec_to_rgb(
            'tests/test_tmp/test_tmp.png', GAMMA=True, MAGIC_NORM=7600)
        self.spec_img.spec_to_rgb(
            'tests/test_tmp/test_tmp_gama.png', GAMMA=True, MAGIC_NORM=7600)

        test_without_gama = np.array(Image.open('tests/test_tmp/test_tmp.png'))
        test_gama = np.array(Image.open('tests/test_tmp/test_tmp_gama.png'))
