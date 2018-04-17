import abc
import hashlib
import io
import logging
import os
from typing import List, Optional, Mapping, Iterable, Set, Any, Dict

import flask
import flask_login
from flask import current_app, abort, Blueprint, render_template, jsonify, request
from p2k16.core import P2k16UserException, auth, account_management, badge_management, models, event_management
from p2k16.core.membership_management import member_set_credit_card, member_get_details, member_set_membership
from p2k16.core.models import Account, Circle, Company, CompanyEmployee, CircleMember, BadgeDescription, \
    CircleManagementStyle
from p2k16.core.models import AccountBadge
from p2k16.core.models import db
from p2k16.web.utils import validate_schema, require_circle_membership, DataServiceTool, ResourcesTool

logger = logging.getLogger(__name__)

id_type = {"type": "number", "min": 1}
nonempty_string = {"type": "string", "minLength": 1}
string_type = {"type": "string"}
management_style_type = {"enum": ["ADMIN_CIRCLE", "SELF_ADMIN"]}

register_account_form = {
    "type": "object",
    "properties": {
        "username": nonempty_string,
        "email": {"type": "string", "format": "email", "minLength": 1},
        "name": nonempty_string,
        "password": {"type": "string", "minLength": 3},
        "phone": {"type": "string"},
    },
    "required": ["email", "username", "password"]
}

start_reset_password_form = {
    "type": "object",
    "properties": {
        "username": nonempty_string
    },
    # "required": ["username"]
}

login_form = {
    "type": "object",
    "properties": {
        "username": nonempty_string,
        "password": nonempty_string,
    },
    "required": ["username", "password"]
}

modify_circle_form = {
    "type": "object",
    "properties": {
        "circleId": id_type,
        "accountId": id_type,
        "accountUsername": nonempty_string,
        "comment": nonempty_string
    },
    "oneOf": [{
        "required": [
            "circleId",
            "accountId",
        ],
    }, {
        "required": [
            "circleId",
            "accountUsername",
        ],
    }, ],
}

add_circle_form = {
    "type": "object",
    "properties": {
        "name": nonempty_string,
        "description": string_type,
        "managementStyle": management_style_type,
        "adminCircle": nonempty_string,
        "username": nonempty_string,
    },
    "required": [
        "name",
        "managementStyle",
    ]
}

single_company_form = {
    "type": "object",
    "properties": {
        "name": nonempty_string,
        "contact": id_type,
        "active": {"type": "boolean"},
    },
    "required": ["name", "contact"]
}


def model_to_json(obj) -> dict:
    d = {}

    if hasattr(obj, "id"):
        d["id"] = int(obj.id)

    if isinstance(obj, models.CreatedAtMixin):
        d["createdAt"] = obj.created_at

    if isinstance(obj, models.UpdatedAtMixin):
        d["updatedAt"] = obj.updated_at

    if isinstance(obj, models.CreatedByMixin):
        d["createdBy"] = obj.created_by.username

    if isinstance(obj, models.UpdatedByMixin):
        d["updatedBy"] = obj.updated_by.username

    return d


def circle_member_to_json(cm: CircleMember):
    return {**model_to_json(cm), **{
        "account_id": cm.account.id,
        "account_username": cm.account.username,
        "circle_id": cm.circle.id,
        "circle_name": cm.circle.name,
        "comment": cm.comment
    }}


def circle_to_json(circle: Circle, include_members=False):
    d = {**model_to_json(circle), **{
        "name": circle.name,
        "description": circle.description,
        "managementStyle": circle.management_style.name,
        "adminCircle": circle.admin_circle_id,
        "memberIds": [m.id for m in circle.members]
    }}

    embedded = {}
    if include_members:
        embedded["members"] = [circle_member_to_json(cm) for cm in circle.members]

    if len(embedded):
        d["_embedded"] = embedded

    return d


def account_to_json(account: Account, circles: List[Circle], badges: Optional[List[AccountBadge]]):
    from .badge_blueprint import badge_to_json

    return {**model_to_json(account), **{
        "id": account.id,
        "username": account.username,
        "avatar": create_avatar_url(account.email or account.username),
        "email": account.email,
        "name": account.name,
        "phone": account.phone,
        "circles": {c.id: {"id": c.id, "name": c.name} for c in circles},
        "badges": {b.id: badge_to_json(b) for b in badges} if badges else None
    }}


def create_avatar_url(email):
    hash = hashlib.md5(email.encode("utf-8")).hexdigest()
    return "https://www.gravatar.com/avatar/{}".format(hash)


def company_to_json(c: Company, include_employees=False):
    def ce(e: CompanyEmployee):
        return {**model_to_json(e), **{
            "account_id": e.account_id,
            "account": {
                "username": e.account.username
            },
            "company_id": e.company_id
        }}

    ret = {**model_to_json(c), **{
        "name": c.name,
        "contact": c.contact,
        "active": c.active,
    }}

    if include_employees:
        ret["employees"] = [ce(e) for e in c.employees]
    return ret


class P2k16Control(object):
    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass


class InvalidateCollectionControl(P2k16Control):
    def __init__(self, collection: str):
        self.collection = collection

    def to_dict(self):
        return {"type": "invalidate-collection", "collection": self.collection}


class ReplaceCollectionControl(P2k16Control):
    def __init__(self, collection: str, data: List[Any]):
        self.collection = collection
        self.data = data

    def to_dict(self):
        return {"type": "replace-collection", "collection": self.collection, "data": self.data}


class P2k16Response(object):
    def __init__(self):
        self.controls = []  # type: List[P2k16Control]
        pass

    def add_control(self, ctrl: P2k16Control):
        self.controls.append(ctrl)
        return self

    def to_dict(self) -> Dict[str, Any]:
        d = {}

        if len(self.controls):
            d["_controls"] = [c.to_dict() for c in self.controls]

        return d


core = Blueprint("core", __name__, template_folder="templates")
registry = DataServiceTool("CoreDataService", "core-data-service.js", core)


@registry.route("/service/authz/log-in", methods=["POST"])
@validate_schema(login_form)
def service_authz_login():
    username = request.json["username"]
    account = Account.find_account_by_username(username)
    password = request.json["password"]

    if not account:
        logger.info("Login: Bad login attempt, no such user: {}".format(username))
        raise P2k16UserException("Invalid credentials")
    if not account.valid_password(password):
        logger.info("Login: Bad login attempt, wrong password: {}".format(username))
        raise P2k16UserException("Invalid credentials")
    circles = account_management.get_circles_for_account(account.id)
    badges = badge_management.badges_for_account(account.id)

    logger.info("Login: username={}, circles={}".format(username, circles))

    authenticated_account = auth.AuthenticatedAccount(account, circles)
    flask_login.login_user(authenticated_account)

    return jsonify(account_to_json(account, circles, badges))


@registry.route('/service/authz/log-out', methods=['POST'])
def service_authz_logout():
    flask_login.logout_user()
    return jsonify({})


###############################################################################
# Account


@registry.route('/service/register-account', methods=['POST'])
@validate_schema(register_account_form)
def register_account():
    u = account_management.register_account(request.json["username"],
                                            request.json["email"],
                                            request.json.get("name", None),
                                            request.json["password"],
                                            request.json.get("phone", None))
    db.session.commit()
    logger.info("new account: {}/{}".format(u.username, u.id))
    return jsonify({})


# This shouldn't return that much data, it should only return circle ids and badge descriptor ids.
@registry.route('/data/account')
def data_account_list():
    accounts = {a.id: a for a in Account.query.all()}  # type:Mapping[int, Account]
    account_ids = [a for a in accounts]
    from itertools import groupby

    account_badges = AccountBadge.query.filter(AccountBadge.account_id.in_(account_ids))
    account_badges = sorted(account_badges, key=lambda ab: ab.account_id)
    badges_by_account = {_id: list(abs) for _id, abs in
                         groupby(account_badges, lambda ab: ab.account_id)}  # type: Mapping[int, List[AccountBadge]]

    cms = CircleMember.query.filter(CircleMember.account_id.in_(account_ids))
    cms = sorted(cms, key=lambda cm: cm.account_id)
    cms_by_account = groupby(cms, lambda cm: cm.account_id)  # type: Iterable[(int, List[CircleMember])]

    circles_by_account = {_id: {cm.circle for cm in cms} for _id, cms in
                          cms_by_account}  # type: Mapping[int, Set[Circle]]

    accounts = [account_to_json(a, circles_by_account.get(id, []), badges_by_account.get(id, [])) for id, a in
                accounts.items()]

    return jsonify(accounts)


@registry.route("/data/account/<int:account_id>")
def data_account(account_id):
    account = Account.find_account_by_id(account_id)

    if account is None:
        abort(404)

    circles = account_management.get_circles_for_account(account.id)

    return jsonify(account_to_json(account, circles, None))


@registry.route("/data/account-summary/<int:account_id>")
def data_account_summary(account_id):
    account = Account.find_account_by_id(account_id)

    if account is None:
        abort(404)

    circles = account_management.get_circles_for_account(account.id)
    badges = badge_management.badges_for_account(account.id)

    open_door_event = event_management.last_door_open(account)

    from .badge_blueprint import badge_to_json
    summary = {
        "account": account_to_json(account, circles, None),
        "badges": [badge_to_json(b) for b in badges],
        "lastDoorOpen": open_door_event.to_dict() if open_door_event else None
    }
    return jsonify(summary)


@registry.route('/data/account/remove-membership', methods=["POST"])
@validate_schema(modify_circle_form)
def remove_account_from_circle():
    return _manage_circle_membership(False)


@registry.route('/service/circle/create-membership', methods=["POST"])
@validate_schema(modify_circle_form)
def add_account_to_circle():
    return _manage_circle_membership(True)


def _manage_circle_membership(create: bool):
    username = request.json.get("accountUsername", None)

    if username is not None:
        account = Account.get_by_username(username)
    else:
        account = Account.get_by_id(request.json["accountId"])

    circle = Circle.get_by_id(request.json["circleId"])

    admin = flask_login.current_user.account

    if create:
        comment = request.json.get("comment", "")
        account_management.add_account_to_circle(account, circle, admin, comment)
    else:
        account_management.remove_account_from_circle(account, circle, admin)

    db.session.commit()
    return jsonify(circle_to_json(circle, include_members=True))


###############################################################################
# Membership


@registry.route('/membership/set-stripe-token', methods=["POST"])
def membership_set_stripe_token():
    account = flask_login.current_user.account
    stripe_token = request.json['id']

    return jsonify(member_set_credit_card(account, stripe_token))


@registry.route('/membership/details')
def membership_details():
    return jsonify(member_get_details(flask_login.current_user.account))


@registry.route('/membership/set-membership', methods=["POST"])
def membership_set_membership():
    account = flask_login.current_user.account

    membership_plan = request.json['plan']
    membership_price = request.json['price']

    return jsonify(member_set_membership(account, membership_plan, membership_price))


###############################################################################
# Circle


@registry.route('/data/circle')
def data_circle_list():
    circles = Circle.query.all()
    return jsonify([circle_to_json(c) for c in circles])


@registry.route('/data/circle/<int:circle_id>')
def data_circle(circle_id):
    circle = Circle.get_by_id(circle_id)
    return jsonify(circle_to_json(circle, include_members=True))


@registry.route('/data/circle', methods=["POST"])
@validate_schema(add_circle_form)
def create_circle():
    name = request.json["name"]
    description = request.json.get("description", "")
    management_style = CircleManagementStyle[request.json["managementStyle"]]
    admin_circle = request.json.get("adminCircle", None)
    username = request.json.get("username", None)

    c = account_management.create_circle(name, description, management_style, admin_circle_name=admin_circle,
                                         username=username)
    db.session.commit()

    circles = [circle_to_json(c) for c in db.session.query(Circle).all()]

    return jsonify({**circle_to_json(c), **P2k16Response().
                   add_control(ReplaceCollectionControl("circles", circles)).to_dict()})


###############################################################################
# Company


@registry.route('/data/company')
def data_company_list():
    companies = Company.query.all()
    return jsonify([company_to_json(c, include_employees=False) for c in companies])


@registry.route('/data/company/<int:company_id>')
def data_company(company_id: int):
    company = Company.find_by_id(company_id)

    if company is None:
        abort(404)

    return jsonify(company_to_json(company, include_employees=True))


@registry.route('/data/company/<int:company_id>/cmd/add-employee', methods=["POST"])
def data_company_add_employee(company_id):
    return _data_company_change_employee(company_id, True)


@registry.route('/data/company/<int:company_id>/cmd/remove-employee', methods=["POST"])
def data_company_remove_employee(company_id):
    return _data_company_change_employee(company_id, False)


@require_circle_membership("despot")
def _data_company_change_employee(company_id, add: bool):
    company = Company.get_by_id(company_id)

    account_id = request.json["accountId"]
    account = Account.find_account_by_id(account_id)
    if account is None:
        abort(404)

    if add:
        db.session.add(CompanyEmployee(company, account))
    else:
        ce = CompanyEmployee.find_by_company_and_account(company_id, account_id)
        if ce is None:
            abort(404)
        db.session.delete(ce)

    db.session.commit()

    return jsonify(company_to_json(company, include_employees=True))


@registry.route('/data/company', methods=["POST"])
@validate_schema(single_company_form)
def data_company_add():
    return _data_company_save()


@registry.route('/data/company', methods=["PUT"])
@validate_schema(single_company_form)
def data_company_update():
    return _data_company_save()


@require_circle_membership("despot")
def _data_company_save():
    contact_id = request.json["contact"]
    contact = Account.find_account_by_id(contact_id)
    if not contact:
        raise P2k16UserException("No such account: {}".format(contact_id))

    _id = request.json.get("id", None)

    if _id:
        company = Company.find_by_id(_id)

        if company is None:
            abort(404)

        logger.info("Updating company: {}".format(company))
        company.name = request.json["name"]
        company.contact_id = contact.id
        company.active = request.json["active"]
    else:
        name = request.json["name"]
        active = request.json["active"]
        logger.info("Registering new company: {}".format(name))
        company = Company(name, contact, active)

    db.session.add(company)
    db.session.commit()

    return jsonify(company_to_json(company, include_employees=True))


###############################################################################
# HTML Pages


@core.route('/')
def index():
    from .badge_blueprint import badge_description_to_json
    kwargs = {
        "circles": [circle_to_json(c) for c in Circle.query.all()],
        "badge_descriptions": [badge_description_to_json(bd) for bd in BadgeDescription.query.all()]
    }

    if flask_login.current_user.is_authenticated:
        account = flask_login.current_user.account  # type: Account
        circles = account_management.get_circles_for_account(account.id)
        badges = badge_management.badges_for_account(account.id)
        circles_with_admin_access = account_management.get_circles_with_admin_access(account.id)

        account_json = account_to_json(account, circles, badges)
        circles_with_admin_access_json = [circle_to_json(c) for c in circles_with_admin_access]

        kwargs["account"] = account_json
        kwargs["circles_with_admin_access"] = circles_with_admin_access_json

    return render_template("index.html", **kwargs)


@core.route('/logout', methods=['GET'])
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for('core.index'))


@core.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        show_message = flask.request.args.get('show_message') or ''
        username = flask.request.args.get('username') or ''
        return render_template("login.html", show_message=show_message, username=username)

    username = flask.request.form['username']
    account = Account.find_account_by_username(username)
    password = flask.request.form['password']

    if account.valid_password(password):
        circles = account_management.get_circles_for_account(account.id)
        logger.info("User {} logged in, circles={}".format(username, circles))
        authenticated_account = auth.AuthenticatedAccount(account, circles)
        flask_login.login_user(authenticated_account)
        return flask.redirect(flask.url_for('core.index'))

    return flask.redirect(flask.url_for('.login', show_message='bad-login', username=username))


@registry.route('/service/start-reset-password', methods=['POST'])
@validate_schema(start_reset_password_form)
def service_start_reset_password():
    username = flask.request.json['username']
    account = account_management.start_reset_password(username)
    if account:
        db.session.commit()

    response = {"message": "If we found your user in our systems we have sent an email to your registered email."}
    return jsonify(response)


@core.route('/reset-password-form', methods=['GET'])
def reset_password_form():
    reset_token = flask.request.args['reset_token']
    account = Account.find_account_by_reset_token(reset_token)

    if account and account.is_valid_reset_token(reset_token):
        return render_template("reset-password.html", reset_token=reset_token, account=account_to_json(account, [], []))

    return flask.redirect(flask.url_for('.login', show_message='recovery-invalid-request'))


@core.route('/set-new-password', methods=['POST'])
def set_new_password():
    reset_token = flask.request.form['reset_token']
    account = Account.find_account_by_reset_token(reset_token)

    if not account or not account.is_valid_reset_token(reset_token):
        return flask.redirect(flask.url_for('.login', show_message='recovery-invalid-request'))

    password = flask.request.form['password']
    account.password = password
    logger.info('Updating password for account={}'.format(account))
    db.session.commit()
    return flask.redirect(flask.url_for('core.index'))


@core.route('/protected')
@flask_login.login_required
def protected():
    a = flask_login.current_user.account
    return 'Logged in as: ' + str(a.id) + ", username=" + a.username


@core.route('/core/ldap/users.ldif')
def core_ldif():
    from ldif3 import LDIFWriter
    import io
    f = io.BytesIO()
    writer = LDIFWriter(f)

    for a in Account.query.all():
        dn = "uid={},ou=People,dc=bitraf,dc=no".format(a.username)

        writer.unparse(dn, {"changetype": ["delete"]})

        object_class = ["top", "inetOrgPerson"]

        d = {
            "objectClass": object_class,
            "changetype": ["add"],
        }

        parts = a.name.split()

        if len(parts) < 1:
            # bad name
            continue

        d["cn"] = [a.name]
        d["sn"] = [parts[-1]]
        if a.email:
            d["mail"] = [a.email]

        # posixAccount: http://ldapwiki.com/wiki/PosixAccount
        object_class.append("posixAccount")
        d["uid"] = [a.username]
        d["uidNumber"] = ["1000"]
        d["gidNumber"] = ["1000"]
        d["homeDirectory"] = ["/home/{}".format(a.username)]
        d["userPassword"] = [a.password]
        d["gecos"] = [a.name]

        writer.unparse(dn, d)

    s = f.getvalue()
    print(str(s))
    return s


@core.route("/core-data-service.js")
def core_service():
    content = core_service.content

    if not content:
        content = registry.generate()
        core_service.content = content

    return content, "application/javascript"


core_service.content = None


@core.route("/p2k16_resources.js")
def p2k16_resources():
    static = os.path.normpath(current_app.static_folder)
    buf = io.StringIO()
    ResourcesTool.run(static, buf)

    return buf.getvalue(), "application/javascript"
