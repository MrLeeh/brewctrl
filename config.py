"""
config.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""
import os
import logging
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    BOOTSTRAP_SERVE_LOCAL = True
    BOOTSTRAP_USE_MINIFIED = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'my secret key'

    SQLALCHEMY_COMMIT_ON_TEARDOWN = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # update time in seconds
    REFRESH_TIME = 1.0
    DELTA_TEMP = 1.0

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    LOGGING_LEVEL = logging.DEBUG
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class DeploymentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')


class TestConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + \
                              os.path.join(basedir, 'data-test.sqlite')


config = {
    'development': DevelopmentConfig,
    'deployment': DeploymentConfig,
    'default': DevelopmentConfig,
    'testing': TestConfig
}
