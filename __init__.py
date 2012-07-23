# Copied from: http://stackoverflow.com/questions/5987466/cant-access-google-appengine-external-libraries

import sys
import os

# locate app-engine SDK
AE_PATH = "/usr/local/google_appengine/"

# path to app code
APP_PATH = os.path.abspath(".")

# load the AE paths (as stolen from dev_appserver.py)
EXTRA_PATHS = [
    APP_PATH,
    AE_PATH,
    os.path.join(AE_PATH, 'lib', 'antlr3'),
    os.path.join(AE_PATH, 'lib', 'django'),
    os.path.join(AE_PATH, 'lib', 'ipaddr'),
    os.path.join(AE_PATH, 'lib', 'webob'),
    os.path.join(AE_PATH, 'lib', 'yaml', 'lib'),
    os.path.join(AE_PATH, 'lib', 'fancy_urllib'), # issue[1]
]
sys.path = EXTRA_PATHS + sys.path

