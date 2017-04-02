import flask
import flask_login
from flask import abort, Blueprint, render_template, jsonify, request

from p2k16 import auth, user_management
from p2k16.database import db
from p2k16.models import User
from p2k16 import app

api = Blueprint('api', __name__, template_folder='templates')


def user_to_json(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }


@api.route('/data/user')
def data_user():
    users = [user_to_json(user) for user in User.query.all()]
    return jsonify(users)


@api.route('/data/user/<int:user_id>', methods=['POST'])
def data_user_port(user_id):
    user = User.find_user_by_id(user_id)

    if user is None:
        abort(404)

    user.password = request.json.password

    return user_to_json(user)


@api.route('/')
def index():
    user = flask_login.current_user.is_authenticated and user_to_json(flask_login.current_user.user)

    return render_template('index.html', user=user)


@api.route('/logout', methods=['GET'])
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for('api.index'))


@api.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        show_message = flask.request.args.get('show_message') or ''
        username = flask.request.args.get('username') or ''
        return render_template('login.html', show_message=show_message, username=username)

    username = flask.request.form['username']
    user = User.find_user_by_username(username)

    if flask.request.form['password'] == user.password:
        app.logger.info("user {} logged in".format(username))
        authenticated_user = auth.AuthenticatedUser(user)
        flask_login.login_user(authenticated_user)
        return flask.redirect(flask.url_for('api.index'))

    return flask.redirect(flask.url_for('.login', show_message='bad-login', username=username))


@api.route('/reset-password', methods=['POST'])
def reset_password():
    username = flask.request.form.get('username')
    if username is not None:
        user = user_management.reset_password(username)
        if user is not None:
            db.session.commit()


    return flask.redirect(flask.url_for('.login', show_message='recovery', username=username))


@api.route('/protected')
@flask_login.login_required
def protected():
    u = flask_login.current_user.user
    return 'Logged in as: ' + str(u.id) + ", username=" + u.username
