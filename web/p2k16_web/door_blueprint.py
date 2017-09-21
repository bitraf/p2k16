import flask_login
import p2k16.door
from flask import Blueprint, jsonify
from p2k16.models import db

door = Blueprint('door', __name__, template_folder='templates')


@door.route('/door/open', methods=['POST'])
@flask_login.login_required
def open():
    u = flask_login.current_user.user
    p2k16.door.open_door(u, p2k16.door.FRONT_DOOR)

    db.session.commit()
    return jsonify(dict())
