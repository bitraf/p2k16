import flask
import flask_login
from flask import abort, Blueprint, render_template, jsonify, request

from p2k16 import auth
from p2k16.models import User

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
        return '''
               <form action='login' method='POST'>
                <input type='text' name='username' id='username' placeholder='username'></input>
                <input type='password' name='pw' id='pw' placeholder='password'></input>
                <input type='submit' name='submit'></input>
               </form>
               '''

    username = flask.request.form['username']
    user = User.find_user_by_username(username)

    if flask.request.form['pw'] == user.password:
        authenticated_user = auth.AuthenticatedUser(user)
        flask_login.login_user(authenticated_user)
        return flask.redirect(flask.url_for('api.index'))

    return 'Bad login'


@api.route('/protected')
@flask_login.login_required
def protected():
    u = flask_login.current_user.user
    return 'Logged in as: ' + str(u.id) + ", username=" + u.username
