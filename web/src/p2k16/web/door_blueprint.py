import logging

import flask
import flask_login
import p2k16.core.door
from flask import Blueprint, jsonify, request
from p2k16.core import P2k16UserException, event_management
from p2k16.core.door import DoorClient
from p2k16.core.models import db
from p2k16.web.utils import validate_schema, DataServiceTool

logger = logging.getLogger(__name__)

door = Blueprint('door', __name__, template_folder='templates')
registry = DataServiceTool("DoorDataService", "door-data-service.js", door)

door_form = {
    "type": "object",
    "properties": {
        "doors": {"type": "array", "minLength": 1, "items": {"type": "string"}},
    },
    "required": ["doors"]
}


@registry.route('/service/door/recent-events', methods=['GET'])
def recent_events():
    from datetime import datetime, timedelta
    start = datetime.now() - timedelta(hours=24)
    return jsonify([e.to_dict() for e in event_management.get_public_recent_events(start)])


@registry.route('/service/door/open', methods=['POST'])
@validate_schema(door_form)
@flask_login.login_required
def open_door():
    a = flask_login.current_user.account

    dc = flask.current_app.config.door_client  # type: DoorClient

    doors = []

    for key in request.json["doors"]:
        if key in p2k16.core.door.doors:
            doors.append(p2k16.core.door.doors[key])
        else:
            raise P2k16UserException("Unknown door: {}".format(key))

    dc.open_doors(a, doors)
    db.session.commit()
    return jsonify(dict())


@registry.route('/door-data-service.js')
def door_service():
    content = door_service.content

    if not content:
        content = registry.generate()
        door_service.content = content

    return content, 'application/javascript'


door_service.content = None
