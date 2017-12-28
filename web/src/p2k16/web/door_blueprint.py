import flask_login
import p2k16.core.door
import flask
from flask import Blueprint, jsonify, request
from p2k16.core import P2k16UserException
from p2k16.core.models import db
from p2k16.web.utils import validate_schema, DataServiceTool

door = Blueprint('door', __name__, template_folder='templates')
registry = DataServiceTool("DoorDataService", "door-data-service.js", door)

door_form = {
    "type": "object",
    "properties": {
        "door": {"type": "string", "minLength": 1},
    },
    "required": ["door"]
}


@registry.route('/service/door/open', methods=['POST'])
@validate_schema(door_form)
@flask_login.login_required
def open_door():
    a = flask_login.current_user.account

    door_name = request.json["door"]

    for door in p2k16.core.door.doors:
        if door.key == door_name:
            p2k16.core.door.open_door(a, door)

            db.session.commit()
            return jsonify(dict())

    raise P2k16UserException("Unknown door: {}".format(door_name))


@registry.route('/door-data-service.js')
def door_service():
    content = door_service.content

    if not content:
        content = flask.Response(registry.generate(), content_type='application/javascript')
        door_service.content = content

    return content


door_service.content = None
