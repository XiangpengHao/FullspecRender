from AssembleImage import SpecImage
import pickle
import unittest
import os.path
from PIL import Image
import numpy as np
from numpy.testing import assert_array_equal


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
        assert_array_equal(self.spec_img.spectrum[0, 0],
                           test_data['spectrum'][0, 0])
        assert_array_equal(self.spec_img.spectrum[240, 320],
                           test_data['spectrum'][240, 320])

    def test_fsi_to_rgb(self):
        self.spec_img.load_from_fsi('tests/test_fixtures/test01.fsi')
        self.spec_img.spec_to_rgb(
            'tests/test_tmp/test_tmp_on.png', GAMMA=True, MAGIC_NORM=7600)
        self.spec_img.spec_to_rgb(
            'tests/test_tmp/test_tmp_off.png', GAMMA=False, MAGIC_NORM=7600)

        test_with_gama = np.array(Image.open(
            'tests/test_tmp/test_tmp_on.png'))
        test_without_gama = np.array(
            Image.open('tests/test_tmp/test_tmp_off.png'))

        fixture_with_gama = np.array(Image.open(
            'tests/test_fixtures/test_7600_on.png'))
        fixture_without_gama = np.array(Image.open(
            'tests/test_fixtures/test_7600_off.png'))

        assert_array_equal(
            test_with_gama[0, 0, :], fixture_with_gama[0, 0, :])
        assert_array_equal(
            test_with_gama[240, 320, :], fixture_with_gama[240, 320, :])
        assert_array_equal(
            test_with_gama[100, 100, :], fixture_with_gama[100, 100, :])

        assert_array_equal(
            test_without_gama[0, 0, :], fixture_without_gama[0, 0, :])
        assert_array_equal(
            test_without_gama[240, 320, :], fixture_without_gama[240, 320, :])
        assert_array_equal(
            test_without_gama[100, 100, :], fixture_without_gama[100, 100, :])
