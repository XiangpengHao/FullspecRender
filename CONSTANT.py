import os
import json
from scipy import spatial
from typing import List, Dict
from ColorSpace import Spectrum
import numpy as np

SPECTRUM_SCALE = 10
SPEC_LENGTH = 61
ROOT_PATH = '/home/hao/ownCloud' if os.environ.get('P_HOME') != '1' else '/mnt/e/ownCloud'

REFLECTANCE: List[Spectrum] = [Spectrum(x) for x in json.load(open('spec/database/reflectance.json'))]
REFLECTANCE_KDD = spatial.KDTree([v.np_xyz / sum(v.np_xyz) for v in REFLECTANCE])

ILLUMINANT: List[Spectrum] = [Spectrum(x) for x in json.load(open('spec/database/illuminant.json'))]
ILLUMINANT_KDD = spatial.KDTree([v.np_xyz / sum(v.np_xyz) for v in ILLUMINANT])

COMMON_LIGHTS: Dict[str, Spectrum] = {
  'd50': Spectrum('spec/d50.json'),
  'd65': Spectrum('spec/d65.json'),
  'illC': Spectrum('spec/illC.json'),
  'illA': Spectrum('spec/illA.json')
}

COLOR_MATCH: Dict[str, Spectrum] = {
  "x": Spectrum("spec/x.json"),
  "y": Spectrum("spec/y.json"),
  "z": Spectrum("spec/z.json")
}

R_xy = np.asarray((0.6400, 0.3300))
G_xy = np.asarray((0.3000, 0.6000))
B_xy = np.asarray((0.1500, 0.0600))
