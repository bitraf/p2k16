import logging

import flask
import flask_login
from flask import Blueprint, jsonify, request
from p2k16.core import P2k16UserException
from p2k16.core.models import db, Account
from p2k16.web.utils import validate_schema, DataServiceTool

logger = logging.getLogger(__name__)

label = Blueprint('label', __name__, template_folder='templates')
registry = DataServiceTool("LabelService", "label-service.js", label)

box_label_form = {
    "type": "object",
    "properties": {
        "user": {"type": "integer"}
        },
    "required": ["user"]
}

@registry.route('/service/label/print_box_label', methods=['POST'])
@validate_schema(box_label_form)
@flask_login.login_required
def print_box_label():
    a = flask_login.current_user.account

    client = flask.current_app.config.label_client # type: LabelClient

    user = Account.find_account_by_id(request.json["user"])

    client.print_box_label(user)

    return jsonify(dict())


@registry.route('/label-service.js')
def service():
    content = service.content

    if not content:
        content = registry.generate()
        service.content = content

    return content, 'application/javascript'

service.content = None

