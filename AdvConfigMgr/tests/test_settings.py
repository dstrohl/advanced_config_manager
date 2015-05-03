__author__ = 'dstrohl'

import os
from AdvConfigMgr.config_preload_django import dcm_factory

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
INI_FILE = os.path.join(PROJECT_ROOT, 'cfg_test.ini')

DJANGO_CONFIGURATION_MANAGER = dcm_factory.get_dcm(INI_FILE)
DCM = DJANGO_CONFIGURATION_MANAGER

DCM_SETTINGS = DCM['settings']


SECRET_KEY = 'fake-key'
INSTALLED_APPS = [
    "tests", "AdvConfigMgr.config_django"
]