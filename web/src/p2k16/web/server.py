import logging
import os
from datetime import date

import flask
import flask_bower
import flask_login
import werkzeug.exceptions
from json import JSONEncoder
from p2k16.core import P2k16UserException, P2k16TechnicalException, membership_management
from p2k16.core import make_app, auth, door, mail, tool, label
from p2k16.core.log import P2k16LoggingFilter
from p2k16.core.models import db, model_support, P2k16Mixin
from p2k16.web import utils
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

logger = logging.getLogger(__name__)

app = make_app()


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
    return _handle_p2k16_exception(error.msg, error, False)


@app.errorhandler(P2k16UserException)
def handle_p2k16_user_exception(error: P2k16UserException):
    return _handle_p2k16_exception(error.msg, error, True)


def _handle_p2k16_exception(msg, ex, is_user):
    db.session.rollback()

    if is_user:
        logger.info("User error: {}".format(msg), exc_info=ex)
    else:
        logger.info("Internal error: {}".format(msg), exc_info=ex)

    response = flask.jsonify({"message": msg})
    response.status_code = 400 if is_user else 500
    response.content_type = 'application/vnd.error+json'
    return response


@app.errorhandler(SQLAlchemyError)
def handle_sqlalchemy_error(error: SQLAlchemyError):
    if isinstance(error, NoResultFound):
        # This happens when Foo.query...one() is called and the object is not found.
        msg = "Object not found"
        status_code = 404
    else:
        # Handle any other SQLAlchemy error as 500 errors
        logger.warning("Got exception", exc_info=error)
        msg = "Got unexpected error from database. Probably some constraint was broken."
        status_code = 500

    response = flask.jsonify({"message": msg})
    response.status_code = status_code
    response.content_type = 'application/vnd.error+json'
    return response


# @app.errorhandler(werkzeug.exceptions.HTTPException)
def handle_generic_http_code(e: werkzeug.exceptions.HTTPException):
    # msg = "{}: {}".format(e.name, e.description)
    if hasattr(e, "name") and hasattr(e, "description"):
        msg = "{}: {}".format(e.name, e.description)
    else:
        msg = "Unknown exception: {}".format(type(e))

    response = flask.jsonify({"message": msg})
    response.status_code = e.code
    response.content_type = 'application/vnd.error+json'
    return response


for e in [werkzeug.exceptions.Forbidden,
          werkzeug.exceptions.InternalServerError,
          werkzeug.exceptions.NotFound,
          werkzeug.exceptions.Unauthorized]:
    app.register_error_handler(e, handle_generic_http_code)


@app.errorhandler(Exception)
def handle_all_other_exceptions(e: Exception):
    logger.warning("Unknown exception type: {}".format(type(e)), exc_info=e)

    response = flask.jsonify({"message": "Unknown internal error"})
    response.status_code = 500
    response.content_type = 'application/vnd.error+json'
    return response


@app.before_request
def session_management():
    flask.session.permanent = True


@app.before_request
def modified_by_mixing_before_request():
    cu = flask_login.current_user

    if not cu or not hasattr(cu, "account"):
        return

    account = cu.account

    P2k16LoggingFilter.set(username=account.username, method=flask.request.method, path=flask.request.path)

    logger.info("before: request: account={}".format(account.username))
    model_support.push(account)
    flask.g.model_pushed = True


@app.after_request
def modified_by_mixing_after_request(response):
    return _after_request(response, False)


@app.teardown_request
def modified_by_mixing_after_request(response):
    return _after_request(response, True)


def _after_request(response, failed: bool):
    P2k16LoggingFilter.clear()

    if hasattr(flask.g, "model_pushed"):
        del flask.g.model_pushed
        # logger.info("after: failed={}, request: {}".format(failed, type(response)))
        model_support.pop()
        if not model_support.is_empty():
            raise P2k16TechnicalException("The model_support stack is not empty.")

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
auth.debug_signals(app)
db.init_app(app)

app.json_encoder = P2k16JSONEncoder
app.config.door_client = door.create_client(app.config)
app.config.tool_client = tool.create_client(app.config)
app.config.label_client = label.create_client(app.config)

from p2k16.web import badge_blueprint, core_blueprint, door_blueprint, tool_blueprint, membership_blueprint, label_blueprint, api_blueprint

# Inject stripe config parameters
membership_blueprint.setup_stripe(app.config)
core_blueprint.setup_stripe(app.config)

app.register_blueprint(badge_blueprint.badge)
app.register_blueprint(core_blueprint.core)
app.register_blueprint(door_blueprint.door)
app.register_blueprint(tool_blueprint.tool)
app.register_blueprint(label_blueprint.label)
app.register_blueprint(membership_blueprint.membership)
app.register_blueprint(api_blueprint.api)

_env = app.config.get("P2K16_ENV", None)

if _env == "local":
    for registry in [badge_blueprint.registry, core_blueprint.registry, door_blueprint.registry, tool_blueprint.registry]:
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

mail.setup(app.config)
