import os
import json
from scipy import spatial
from typing import List, Dict
from ColorSpace import Spectrum

SPECTRUM_SCALE = 5
SPEC_LENGTH = 61
ROOT_PATH = '/home/hao/ownCloud' if os.environ.get('P_HOME') != '1' else '/mnt/e/ownCloud'

REFLECTANCE: List[Spectrum] = [Spectrum(x) for x in json.load(open('spec/database/reflectance.json'))]
REFLECTANCE_KDD = spatial.KDTree([v.np_xyz / sum(v.np_xyz) for v in REFLECTANCE])

ILLUMINANT: List[Spectrum] = [Spectrum(x) for x in json.load(open('spec/database/illuminant.json'))]
ILLUMINANT_KDD = spatial.KDTree([v.np_xyz / sum(v.np_xyz) for v in ILLUMINANT])
