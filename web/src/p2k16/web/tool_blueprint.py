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

tool = Blueprint('tool', __name__, template_folder='templates')
registry = DataServiceTool("ToolDataService", "tool-data-service.js", tool)

tool_form = {
    "type": "object",
    "properties": {
        "tool": {"type": "string"},
    },
    "required": ["tool"]
}


@registry.route('/service/tool/checkout', methods=['POST'])
@validate_schema(tool_form)
@flask_login.login_required
def checkout_tool():
    account = flask_login.current_user.account
    client = flask.current_app.config.tool_client  # type: DoorClient
    tool = request.json["tool"]
    client.checkout_tool(account, tool)
    db.session.commit()
    return jsonify(dict())

@registry.route('/service/tool/checkin', methods=['POST'])
@validate_schema(tool_form)
@flask_login.login_required
def checkin_tool():
    account = flask_login.current_user.account
    client = flask.current_app.config.tool_client  # type: DoorClient
    tool = request.json["tool"]
    client.checkin_tool(account, tool)
    db.session.commit()
    return jsonify(dict())

@registry.route('/tool-data-service.js')
def door_service():
    content = door_service.content

    if not content:
        content = registry.generate()
        door_service.content = content

    return content, 'application/javascript'


door_service.content = None
