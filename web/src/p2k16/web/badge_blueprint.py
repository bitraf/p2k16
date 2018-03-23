import logging
from typing import List

import flask
import flask_login
from flask import Blueprint, jsonify, request
from p2k16.core import account_management, badge_management, P2k16UserException
from p2k16.core.models import Account, AccountBadge, BadgeDescription
from p2k16.core.models import db
from p2k16.web.core_blueprint import model_to_json, account_to_json
from p2k16.web.utils import validate_schema, DataServiceTool

logger = logging.getLogger(__name__)

id_type = {"type": "number", "min": 1}
nonempty_string = {"type": "string", "minLength": 1}

create_badge_form = {
    "type": "object",
    "properties": {
        "title": nonempty_string,
        "recipient": nonempty_string
    },
    "required": ["title"],
    "additionalProperties": False,
}

badge = Blueprint('badge', __name__, template_folder='templates')
registry = DataServiceTool("BadgeDataService", "badge-data-service.js", badge)


def badge_to_json(b: AccountBadge):
    return {**model_to_json(b), **{
        "account_id": b.account_id,
        "account_username": b.account.username,
        "awarded_by_id": b.awarded_by_id,
        "awarded_by_username": b.awarded_by.username if b.awarded_by else None,
        "description_id": b.description_id
    }}


def badge_description_to_json(bd: BadgeDescription):
    return {**model_to_json(bd), **{
        "title": bd.title,
        "description": bd.description,
        "slug": bd.slug,
        "icon": bd.icon,
        "color": bd.color,
        "certification_circle_id": bd.certification_circle_id
    }}


@registry.route('/badge/badge-descriptions', methods=["GET"])
def badge_descriptions():
    bds = BadgeDescription.query.all()
    return jsonify({bd.id: badge_description_to_json(bd) for bd in bds})


@registry.route('/badge/create-badge', methods=["POST"])
@validate_schema(create_badge_form)
def create():
    account = flask_login.current_user.account  # type: Account

    title = request.json["title"]
    recipient_username = request.json.get("recipient", None)

    if recipient_username:
        recipient = Account.find_account_by_username(recipient_username)

        if not recipient:
            raise P2k16UserException("No such username: {}".format(recipient_username))
    else:
        recipient = account

    badge_management.create_badge(recipient, account, title)

    circles = account_management.get_circles_for_account(account.id)
    badges = badge_management.badges_for_account(account.id)

    db.session.commit()

    return jsonify(account_to_json(account, circles, badges))


@registry.route('/badge/recent-badges', methods=["GET"])
def recent_badges():
    badges = AccountBadge.query. \
        order_by(AccountBadge.created_at.desc()).limit(20). \
        all()  # type: List[AccountBadge]
    return jsonify([badge_to_json(b) for b in badges])


@registry.route('/badge/badges-for-user/<int:account_id>', methods=["GET"])
def badges_for_user(account_id):
    account = Account.find_account_by_id(account_id)

    badges = AccountBadge.query. \
        filter(AccountBadge.account == account). \
        all()  # type: List[AccountBadge]
    return jsonify([badge_to_json(b) for b in badges])


@badge.route('/badge-data-service.js')
def badge_service():
    content = badge_service.content

    if not content:
        content = flask.Response(registry.generate(), content_type='application/javascript')
        badge_service.content = content

    return content


badge_service.content = None
