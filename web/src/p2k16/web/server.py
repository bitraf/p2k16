import logging
import os
import sys
from datetime import date

import flask
import flask_bower
import flask_login
from flask.json import JSONEncoder

from p2k16.core import P2k16UserException, P2k16TechnicalException
from p2k16.core import make_app, auth, door
from p2k16.core.models import db, model_support, P2k16Mixin
from p2k16.web import utils

logger = logging.getLogger(__name__)


def configure_logging():
    l = logging.getLogger("p2k16")

    log_format = '[%(asctime)s] [%(name)-30s] [%(levelname)-8s] %(message)s'
    formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S %z')
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    l.addHandler(handler)
    l.setLevel(logging.DEBUG)

    l = logging.getLogger("sqlalchemy.engine.base.Engine")
    l.addHandler(handler)


app = make_app()

configure_logging()


@app.url_defaults
def hashed_url_for_static_file(endpoint, values):
    def create_hash(path):
        t = flask.current_app.config.get("RESOURCE_HASH_TYPE", None)

        if t == "mtime":
            return int(os.stat(path).st_mtime)

    # print("hashed_url_for_static_file: endpoint={}, values={}".format(endpoint, values))
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

            hash = create_hash(os.path.join(static_folder, filename))

            if hash:
                param_name = 'h'
                while param_name in values:
                    param_name = '_' + param_name

                values[param_name] = hash


@app.errorhandler(P2k16TechnicalException)
def handle_p2k16_technical_exception(error: P2k16TechnicalException):
    return _handle_p2k16_exception(error.msg, False)


@app.errorhandler(P2k16UserException)
def handle_p2k16_user_exception(error: P2k16UserException):
    return _handle_p2k16_exception(error.msg, True)


def _handle_p2k16_exception(msg, is_user):
    import traceback

    db.session.rollback()

    logger.info("Account error: {}".format(msg))
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
    logger.info("before: request: account={}, {}".format(account, flask.request))
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
        logger.info("after: failed={}, request: {}".format(failed, flask.request))
        model_support.pop()

    return response


# We want dates to be ISO formatted: https://stackoverflow.com/a/43663918/245614

class P2k16JSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, date):
                return obj.isoformat()
            if isinstance(obj, P2k16Mixin):
                return obj.id
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


auth.login_manager.init_app(app)
db.init_app(app)

app.json_encoder = P2k16JSONEncoder
app.door_client = door.create_client(app.config)

from p2k16.web import core_blueprint, door_blueprint, membership_blueprint

app.register_blueprint(core_blueprint.core)
app.register_blueprint(door_blueprint.door)
app.register_blueprint(membership_blueprint.membership)

_env = app.config.get("P2K16_ENV", None)

if _env == "local":
    for registry in [core_blueprint.registry, door_blueprint.registry]:
        with open(os.path.join(app.static_folder, registry.jsName), "w") as f:
            # print("app.static_folder={}".format(app.static_folder))
            f.write(registry.generate())

    with app.test_request_context():
        static = os.path.normpath(app.static_folder)

        resource_hash_type = flask.current_app.config.get("RESOURCE_HASH_TYPE", None)

        try:
            flask.current_app.config["RESOURCE_HASH_TYPE"] = None
            with open(os.path.join(app.static_folder, "{}/p2k16_resources.js".format(static)), "w") as f:
                utils.ResourcesTool.run(static, f)
        finally:
            flask.current_app.config["RESOURCE_HASH_TYPE"] = resource_hash_type

flask_bower.Bower(app)
