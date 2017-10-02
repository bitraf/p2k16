import flask
import flask_login
from flask import abort, Blueprint, render_template, jsonify, request
from p2k16 import app
from p2k16 import auth, user_management
from p2k16.database import db
from p2k16.models import User
from p2k16_web.utils import validate_schema


RegisterUserForm = {
    "type": "object",
    "properties": {
        "username": {"type": "string", "minLength": 1},
        "email": {"type": "string", "format": "email", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "password": {"type": "string", "minLength": 3},
        "phone": {"type": "string"},
    },
    "required": ["email", "username", "password"]
}

core = Blueprint('core', __name__, template_folder='templates')


def user_to_json(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }


@core.route('/service/register-user', methods=['POST'])
@validate_schema(RegisterUserForm)
def register_user():
    u = user_management.register_user(request.json["username"],
                                      request.json["email"],
                                      request.json.get("name", None),
                                      request.json["password"],
                                      request.json.get("phone", None))
    db.session.commit()
    print("new user: {}/{}".format(u.username, u.id))
    return jsonify({})


@core.route('/data/user')
def data_user():
    users = [user_to_json(user) for user in User.query.all()]
    return jsonify(users)


@core.route('/data/user/<int:user_id>', methods=['POST'])
def data_user_port(user_id):
    user = User.find_user_by_id(user_id)

    if user is None:
        abort(404)

    user.password = request.json.password

    return user_to_json(user)


@core.route('/')
def index():
    user = flask_login.current_user.is_authenticated and user_to_json(flask_login.current_user.user)

    return render_template('index.html', user=user)


@core.route('/logout', methods=['GET'])
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for('core.index'))


@core.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        show_message = flask.request.args.get('show_message') or ''
        username = flask.request.args.get('username') or ''
        return render_template('login.html', show_message=show_message, username=username)

    username = flask.request.form['username']
    user = User.find_user_by_username(username)
    password = flask.request.form['password']

    if user.valid_password(password):
        app.logger.info("user {} logged in".format(username))
        authenticated_user = auth.AuthenticatedUser(user)
        flask_login.login_user(authenticated_user)
        return flask.redirect(flask.url_for('core.index'))

    return flask.redirect(flask.url_for('.login', show_message='bad-login', username=username))


@core.route('/start-reset-password', methods=['POST'])
def start_reset_password():
    username = flask.request.form['username']
    user = user_management.start_reset_password(username)
    if user:
        db.session.commit()

    return flask.redirect(flask.url_for('.login', show_message='recovery', username=username))


@core.route('/reset-password-form', methods=['GET'])
def reset_password_form():
    reset_token = flask.request.args['reset_token']
    user = User.find_user_by_reset_token(reset_token)

    if user and user.is_valid_reset_token(reset_token):
        return render_template('reset-password.html', reset_token=reset_token, user=user_to_json(user))

    return flask.redirect(flask.url_for('.login', show_message='recovery-invalid-request'))


@core.route('/set-new-password', methods=['POST'])
def set_new_password():
    reset_token = flask.request.form['reset_token']
    user = User.find_user_by_reset_token(reset_token)

    if not user or not user.is_valid_reset_token(reset_token):
        return flask.redirect(flask.url_for('.login', show_message='recovery-invalid-request'))

    password = flask.request.form['password']
    user.password = password
    app.logger.info('Updating password for user={}'.format(user))
    db.session.commit()
    return flask.redirect(flask.url_for('.login'))


@core.route('/protected')
@flask_login.login_required
def protected():
    u = flask_login.current_user.user
    return 'Logged in as: ' + str(u.id) + ", username=" + u.username
