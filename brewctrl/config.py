"""
config.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'brewctrl.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True

DEBUG = True
SECRET_KEY = 'my secret key'

# update time in seconds
REFRESH_TIME = 1.0
DELTA_TEMP = 1.0