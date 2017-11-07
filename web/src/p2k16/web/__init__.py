import flask
import flask_bower
import flask_login
import os
from datetime import date
from flask.json import JSONEncoder
from p2k16.core import P2k16UserException, P2k16TechnicalException, app
from p2k16.core.database import db
from p2k16.core.models import model_support
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


@app.before_request
def modified_by_mixing_before_request():
    cu = flask_login.current_user

    if not cu or not hasattr(cu, "account"):
        return

    account = cu.account
    flask.current_app.logger.info("before: request: account={}, {}".format(account, flask.request))
    model_support.push(account)
    flask.g.model_pushed = True


@app.after_request
def modified_by_mixing_after_request(response):
    return _after_request(response, False)


@app.teardown_request
def modified_by_mixing_after_request(response):
    return _after_request(response, True)


def _after_request(response, failed: bool):
    if hasattr(flask.g, "model_pushed"):
        del flask.g.model_pushed
        flask.current_app.logger.info("after: failed={}, request: {}".format(failed, flask.request))
        model_support.pop()

    return response


# We want dates to be ISO formatted.
# https://stackoverflow.com/a/43663918/245614

class P2k16JSONEncoder(JSONEncoder):

    def default(self, obj):
        try:
            if isinstance(obj, date):
                return obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)

app.json_encoder = P2k16JSONEncoder

app.register_blueprint(core_blueprint.core)
app.register_blueprint(door_blueprint.door)
app.register_blueprint(membership_blueprint.membership)

with open(os.path.join(app.static_folder, core_blueprint.registry.jsName), "w") as f:
    # print("app.static_folder={}".format(app.static_folder))
    f.write(core_blueprint.registry.generate())

flask_bower.Bower(app)
