import flask_login
import p2k16.door
from flask import Blueprint, jsonify, request
from p2k16 import P2k16UserException
from p2k16.models import db
from p2k16_web.utils import validate_schema

door = Blueprint('door', __name__, template_folder='templates')

door_form = {
    "type": "object",
    "properties": {
        "door": {"type": "string", "minLength": 1},
    },
    "required": ["door"]
}


@door.route('/service/door/open', methods=['POST'])
@validate_schema(door_form)
@flask_login.login_required
def open():
    u = flask_login.current_user.user

    door_name = request.json["door"]

    for door in p2k16.door.doors:
        if door.key == door_name:
            p2k16.door.open_door(u, door)

            db.session.commit()
            return jsonify(dict())

    raise P2k16UserException("Unknown door: {}".format(door_name))
