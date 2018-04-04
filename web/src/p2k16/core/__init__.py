import logging
import os

from flask import Flask
from flask_env import MetaFlaskEnv

logger = logging.getLogger(__name__)


class Configuration(metaclass=MetaFlaskEnv):
    pass


class P2k16UserException(Exception):
    """Exception that happened because the user did something silly. The message will be shown to the user"""

    def __init__(self, msg):
        self.msg = msg


class P2k16TechnicalException(Exception):
    """Exception for unexpected stuff."""

    def __init__(self, msg=None):
        self.msg = msg


def make_app():
    app = Flask("p2k16", static_folder="web/static")

    app.config.BOWER_KEEP_DEPRECATED = False
    app.config['BOWER_COMPONENTS_ROOT'] = '../web/bower_components'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    p2k16_config = os.getenv('P2K16_CONFIG')
    if p2k16_config:
        p2k16_config = os.path.abspath(p2k16_config)

        config_default = os.path.join(os.path.dirname(p2k16_config), "config-default.cfg")
        config_default = os.path.abspath(config_default)

        logger.info("Loading defaults from {}".format(config_default))
        app.config.from_pyfile(config_default)

        logger.info("Loading config from {}".format(p2k16_config))
        app.config.from_pyfile(p2k16_config)

    # Allow the environment variables to override by loading them lastly
    app.config.from_object(Configuration)

    return app
