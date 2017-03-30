import os


import p2k16.config as config
from flask import Flask

app = Flask(__name__, static_folder="../p2k16_web/static")

app.config.BOWER_KEEP_DEPRECATED = False
app.config['BOWER_COMPONENTS_ROOT'] = '../p2k16_web/bower_components'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if os.getenv('P2K16_CONFIG') is not None:
    app.config.from_envvar('P2K16_CONFIG')

config.from_env(app)

class P2k16UserException(Exception):
    """Exception that happened because the user did something silly. The message will be shown to the user"""

    def __init__(self, msg):
        self.msg = msg


class P2k16TechnicalException(Exception):
    """Exception for unexpected stuff."""
    pass
