import flask
import flask_bower
import os
from p2k16.core import P2k16UserException, P2k16TechnicalException, app
from p2k16.core.database import db
from p2k16.web import core_blueprint, door_blueprint, membership_blueprint


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


@app.errorhandler(P2k16TechnicalException)
def handle_p2k16_technical_exception(error: P2k16TechnicalException):
    return _handle_p2k16_exception(error.msg, False)


@app.errorhandler(P2k16UserException)
def handle_p2k16_user_exception(error: P2k16UserException):
    return _handle_p2k16_exception(error.msg, True)


def _handle_p2k16_exception(msg, is_user):
    import traceback

    db.session.rollback()

    app.logger.info("Account error: {}".format(msg))
    # traceback.print_exc(file=sys.stdout)
    traceback.print_exc()

    response = flask.jsonify({"message": msg})
    response.status_code = 400 if is_user else 500
    response.content_type = 'application/vnd.error+json'
    return response


app.register_blueprint(core_blueprint.core)
app.register_blueprint(door_blueprint.door)
app.register_blueprint(membership_blueprint.membership)

with open(os.path.join(app.static_folder, core_blueprint.registry.jsName), "w") as f:
    # print("app.static_folder={}".format(app.static_folder))
    f.write(core_blueprint.registry.generate())

flask_bower.Bower(app)
