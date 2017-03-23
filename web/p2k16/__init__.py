import os

from flask import Flask

app = Flask(__name__, static_folder="../p2k16_web/static")

app.config.BOWER_KEEP_DEPRECATED = False
app.config['BOWER_COMPONENTS_ROOT'] = '../p2k16_web/bower_components'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if os.getenv('P2K16_CONFIG') is not None:
    app.config.from_envvar('P2K16_CONFIG')
