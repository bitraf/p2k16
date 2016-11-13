import flask
import flask_login
from flask import abort, Blueprint, render_template, jsonify, request

from p2k16 import auth
from p2k16.models import User, find_user_by_id

api = Blueprint('api', __name__, template_folder='templates')


def user_to_json(user):
    return {"id": user.id, "email": user.email}


@api.route('/data/user')
def data_user():
    users = [user_to_json(user) for user in User.query.all()]
    return jsonify(users)


@api.route('/data/user/<int:user_id>', methods=['POST'])
def data_user_port(user_id):
    user = find_user_by_id(user_id)

    if user is None:
        abort(404)

    user.password = request.json.password

    return user_to_json(user)


@api.route('/')
def index():
    return render_template('index.html')


@api.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
               <form action='login' method='POST'>
                <input type='text' name='email' id='email' placeholder='email'></input>
                <input type='password' name='pw' id='pw' placeholder='password'></input>
                <input type='submit' name='submit'></input>
               </form>
               '''

    email = flask.request.form['email']
    users = User.query.all()
    # print(users)
    users = dict([(user.email, user) for user in users])
    # print(users)
    # print(users['trygvis@inamo.no'])

    if flask.request.form['pw'] == users[email].password:
        authenticated_user = auth.AuthenticatedUser(users[email].id, email)
        flask_login.login_user(authenticated_user)
        return flask.redirect(flask.url_for('api.protected'))

    return 'Bad login'


@api.route('/protected')
@flask_login.login_required
def protected():
    u = flask_login.current_user
    return 'Logged in as: ' + str(u.id) + ", email=" + u.email
