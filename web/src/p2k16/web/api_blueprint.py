import logging

import flask
from flask import Blueprint, jsonify, request, abort

from p2k16.core import account_management
from p2k16.core.membership_management import \
    get_membership, get_membership_month_count
from p2k16.core.models import Account, Company, \
    StripePayment, Circle

logger = logging.getLogger(__name__)

webhook_secret = None

api = Blueprint("api", __name__, template_folder="templates")


@api.route('/api/memberinfo', methods=['GET'])
def memberinfo():
    a = flask.request.authorization

    if a is None:
        abort(401)

    account = Account.find_account_by_username(a.username)

    if account is None:
        abort(403)

    if not account.valid_password(a.password):
        abort(403)

    circle = Circle.get_by_name('api')
    if not account_management.is_account_in_circle(account, circle):
        return abort(403)

    username = request.args.get("username")

    account = Account.find_account_by_username(username)

    if account is None:
        abort(404)

    paying_member = StripePayment.is_account_paying_member(account.id)
    month_count = get_membership_month_count(account)

    response = {
        "username": username,
        "paying_member": paying_member,
        "month_count": month_count,
        "email": account.email,
    }

    membership = get_membership(account)
    if membership is not None:
        response['fee'] = membership.fee
        response['first_membership'] = membership.first_membership
        response['start_membership'] = membership.start_membership

    response['employment'] = Company.is_account_employed(account.id)
    return jsonify(response)
