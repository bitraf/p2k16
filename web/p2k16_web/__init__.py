from flask import Flask, render_template
from flask_bower import Bower
from flask import jsonify

from p2k16.database import Base, init_db, db_session
from p2k16.models import User

app = Flask(__name__)
Bower(app)

init_db()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/data/user')
def data_user():
    users = [{"id": user.id, "email": user.email} for user in User.query.all()]
    return jsonify(users)


@app.route('/')
def index():
    return render_template('index.html')
