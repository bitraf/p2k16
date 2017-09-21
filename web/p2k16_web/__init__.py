import os

import flask
import flask_bower
import p2k16.database
from p2k16_web import core_blueprint, door_blueprint

app = p2k16.app


@app.url_defaults
def hashed_url_for_static_file(endpoint, values):
    if 'static' == endpoint or endpoint.endswith('.static'):
        filename = values.get('filename')
        if filename:
            if '.' in endpoint:  # has higher priority
                blueprint = endpoint.rsplit('.', 1)[0]
            else:
                blueprint = flask.request.blueprint  # can be None too

            static_folder = None
            if blueprint:
                static_folder = app.blueprints[blueprint].static_folder

            if not static_folder:
                static_folder = app.static_folder

            param_name = 'h'
            while param_name in values:
                param_name = '_' + param_name

            values[param_name] = static_file_hash(os.path.join(static_folder, filename))


def static_file_hash(filename):
    return int(os.stat(filename).st_mtime)  # or app.config['last_build_timestamp'] or md5(filename) or etc...


app.register_blueprint(core_blueprint.core)
app.register_blueprint(door_blueprint.door)

flask_bower.Bower(app)
