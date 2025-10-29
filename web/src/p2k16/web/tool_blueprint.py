import logging

import flask
import flask_login

import p2k16.core.door
from flask import Blueprint, jsonify, request, abort
from p2k16.core import P2k16UserException, event_management
from p2k16.core.door import DoorClient
from p2k16.core.models import db, ToolDescription, ToolCheckout, Circle
from p2k16.web.utils import validate_schema, DataServiceTool, require_circle_membership
from p2k16.web.core_blueprint import model_to_json, circle_to_json

logger = logging.getLogger(__name__)

tool = Blueprint('tool', __name__, template_folder='templates')
registry = DataServiceTool("ToolDataService", "tool-data-service.js", tool)

tool_form = {
    "type": "object",
    "properties": {
        "tool": {"type": "integer"},
    },
    "required": ["tool"]
}


@registry.route('/service/tool/recent-events', methods=['GET'])
def recent_events():
    from datetime import datetime, timedelta
    start = datetime.now() - timedelta(days=7)
    return jsonify([e.to_dict() for e in event_management.get_tool_recent_events(start)])


@registry.route('/service/tool/checkout', methods=['POST'])
@validate_schema(tool_form)
@flask_login.login_required
def checkout_tool():
    account = flask_login.current_user.account
    client = flask.current_app.config.tool_client  # type: DoorClient
    tool = ToolDescription.find_by_id(request.json["tool"])
    client.checkout_tool(account, tool)
    db.session.commit()
    return data_tool_list()


@registry.route('/service/tool/checkin', methods=['POST'])
@validate_schema(tool_form)
@flask_login.login_required
def checkin_tool():
    account = flask_login.current_user.account
    client = flask.current_app.config.tool_client  # type: DoorClient
    tool = ToolDescription.find_by_id(request.json["tool"])
    client.checkin_tool(account, tool)
    db.session.commit()
    return data_tool_list()


def tool_to_json(tool: ToolDescription):
    checkout = ToolCheckout.find_by_tool(tool)

    checkout_model = {}
    if checkout is not None:
        checkout_model = {
            "active": True,
            "started": checkout.started,
            "account": checkout.account.id,
            "username": checkout.account.username,
        }
    else:
        checkout_model = {
            "active": False,
        }

    return {**model_to_json(tool), **{
        "name": tool.name,
        "description": tool.description,
        "circles": [circle_to_json(c, include_members=False) for c in tool.circles],
        "checkout": checkout_model,
    }}


@registry.route('/data/tool')
def data_tool_list():
    tools = ToolDescription.query.all()

    return jsonify([tool_to_json(tool) for tool in tools])


@registry.route('/data/tool/<int:tool_id>')
def data_tool(tool_id: int):
    tool = ToolDescription.find_by_id(tool_id)

    if tool is None:
        abort(404)

    return jsonify(tool_to_json(tool))


@registry.route('/data/tool', methods=["PUT"])
def data_tool_update():
    return _data_tool_save()


@registry.route('/data/tool', methods=["POST"])
def data_tool_add():
    return _data_tool_save()


@require_circle_membership("despot")
def _data_tool_save():
    _id = request.json.get("id", None)

    if _id:
        tool = ToolDescription.find_by_id(_id)

        if tool is None:
            abort(404)

        logger.info("Updating tool: {}".format(tool))
        tool.name = request.json["name"]
        tool.description = request.json["description"]
    else:
        logger.info("New tool: {}".format(request.json["name"]))
        tool = ToolDescription(request.json["name"], request.json["description"])

    circles = request.json["circles"]
    if not circles:
        circles = []

    logger.info("Resolving circles")
    for c in circles:
        obj = Circle.find_by_id(c["id"])
        logger.info("circle={}".format(obj))
        if obj is None:
            raise P2k16UserException("No such circle: {}".format(c.id))
        tool.circles.append(obj)

    db.session.add(tool)
    db.session.commit()
    db.session.flush()
    logger.info("Update tool: {}".format(tool.name))

    return jsonify(tool_to_json(tool))


@registry.route('/data/tool/<int:tool_id>/circle-requirements/<int:circle_id>', methods=["POST"])
@require_circle_membership("despot")
def add_tool_circle_requirement(tool_id: int, circle_id: int):
    tool = ToolDescription.find_by_id(tool_id)
    circle = Circle.find_by_id(circle_id)
    logger.info("Adding circle requirement to tool: {}, {}".format(tool, circle))

    # for c in tool.circles:
    #     logger.info("Circle requirement on tool: {}, {}".format(c, circle))
    #     if c.id == circle_
    tool.circles.append(circle)

    db.session.add(tool)
    db.session.commit()

    return jsonify(tool_to_json(tool))


@registry.route('/data/tool/<int:tool_id>/circle-requirements/<int:circle_id>', methods=["DELETE"])
@require_circle_membership("despot")
def remove_tool_circle_requirement(tool_id: int, circle_id: int):
    tool = ToolDescription.find_by_id(tool_id)
    circle = Circle.find_by_id(circle_id)
    logger.info("Removing circle requirement from tool: {}, {}".format(tool, circle))
    #
    # for c in tool.circles:
    #     logger.info("Circle requirement on tool: {}, {}".format(c, circle))
    #     if c.id == circle_

    tool.circles = [c for c in tool.circles if c.id != circle_id]

    db.session.add(tool)
    db.session.commit()

    return jsonify(tool_to_json(tool))


@registry.route('/tool-data-service.js')
def tool_service():
    content = tool_service.content

    if not content:
        content = registry.generate()
        tool_service.content = content

    return content, {'Content-Type': 'application/javascript'}


tool_service.content = None
