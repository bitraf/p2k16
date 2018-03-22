import io
import logging
import os
from typing import List, Optional

import flask
import flask_login
from flask import current_app, abort, Blueprint, render_template, jsonify, request
from p2k16.core import P2k16UserException, auth, account_management, badge_management, models, event_management
from p2k16.core.membership_management import member_set_credit_card, member_get_details, member_set_membership
from p2k16.core.models import Account, Circle, Company, CompanyEmployee
from p2k16.core.models import AccountBadge
from p2k16.core.models import db
from p2k16.web.utils import validate_schema, DataServiceTool, ResourcesTool

logger = logging.getLogger(__name__)

id_type = {"type": "number", "min": 1}
nonempty_string = {"type": "string", "minLength": 1}

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

single_circle_form = {
    "type": "object",
    "properties": {
        "circle_id": id_type,
    },
    "required": ["circle_id"]
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


def circle_to_json(circle: Circle):
    return {**model_to_json(circle), **{
        "name": circle.name
    }}


def account_to_json(account: Account, circles: List[Circle], badges: Optional[List[AccountBadge]]):
    from .badge_blueprint import badge_to_json

    return {**model_to_json(account), **{
        "id": account.id,
        "username": account.username,
        "email": account.email,
        "name": account.name,
        "phone": account.phone,
        "circles": {c.id: {"id": c.id, "name": c.name} for c in circles},
        "badges": {b.id: badge_to_json(b) for b in badges} if badges else None
    }}


def company_to_json(c: Company, employees: List[CompanyEmployee]):
    def ce(e: CompanyEmployee):
        return {**model_to_json(e), **{
            "account_id": e.account_id,
            "account": {
                "username": e.account.username
            },
            "company_id": e.company_id
        }}

    return {**model_to_json(c), **{
        "name": c.name,
        "contact": c.contact,
        "active": c.active,
        "employees": [ce(e) for e in employees]
    }}


def check_is_in_circle(circle_name: str):
    """
    TODO: implement
    """
    pass


core = Blueprint('core', __name__, template_folder='templates')
registry = DataServiceTool("CoreDataService", "core-data-service.js", core)


@registry.route('/service/authz/log-in', methods=['POST'])
@validate_schema(login_form)
def service_authz_login():
    username = request.json["username"]
    account = Account.find_account_by_username(username)
    password = request.json['password']

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


# This is not very optimal at all
@registry.route('/data/account')
def data_account_list():
    accounts_plus_plus = [(account,
                           account_management.get_circles_for_account(account.id),
                           badge_management.badges_for_account(account.id))
                          for account in Account.query.all()]
    accounts = [account_to_json(account, circles, badges) for (account, circles, badges) in accounts_plus_plus]
    return jsonify(accounts)


@registry.route('/data/account/<int:account_id>')
def data_account(account_id):
    account = Account.find_account_by_id(account_id)

    if account is None:
        abort(404)

    circles = account_management.get_circles_for_account(account.id)

    return jsonify(account_to_json(account, circles, None))


@registry.route('/data/account-summary/<int:account_id>')
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


@registry.route('/data/account/<int:account_id>/cmd/remove-membership', methods=["POST"])
@validate_schema(single_circle_form)
def remove_membership(account_id):
    return _manage_membership(account_id, False)


@registry.route('/data/account/<int:account_id>/cmd/create-membership', methods=["POST"])
@validate_schema(single_circle_form)
def create_membership(account_id):
    return _manage_membership(account_id, True)


###############################################################################
# Membership


def _manage_membership(account_id: int, create: bool):
    account = Account.find_account_by_id(account_id)

    if account is None:
        abort(404)

    circle_id = request.json["circle_id"]
    a = flask_login.current_user.account

    if create:
        account_management.add_account_to_circle(account.id, circle_id, a.id)
    else:
        account_management.remove_account_from_circle(account.id, circle_id, a.id)

    circles = account_management.get_circles_for_account(account.id)
    badges = badge_management.badges_for_account(account.id)

    db.session.commit()
    return jsonify(account_to_json(account, circles, badges))


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


@registry.route('/data/circle')
def data_circle_list():
    circles = Circle.query.all()
    return jsonify([circle_to_json(c) for c in circles])


###############################################################################
# Company


@registry.route('/data/company')
def data_company_list():
    companies = Company.query.all()
    return jsonify([company_to_json(c, []) for c in companies])


@registry.route('/data/company/<int:company_id>')
def data_company(company_id: int):
    company = Company.find_by_id(company_id)

    if company is None:
        abort(404)

    employees = CompanyEmployee.list_by_company(company_id)

    return jsonify(company_to_json(company, employees))


@registry.route('/data/company/<int:company_id>/cmd/add-employee', methods=["POST"])
def data_company_add_employee(company_id):
    return _data_company_change_employee(company_id, True)


@registry.route('/data/company/<int:company_id>/cmd/remove-employee', methods=["POST"])
def data_company_remove_employee(company_id):
    return _data_company_change_employee(company_id, False)


def _data_company_change_employee(company_id, add: bool):
    check_is_in_circle("admin")

    company = Company.find_by_id(company_id)

    if company is None:
        abort(404)

    account_id = request.json["account_id"]
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

    employees = CompanyEmployee.list_by_company(company_id)
    db.session.commit()

    return jsonify(company_to_json(company, employees))


@registry.route('/data/company', methods=["POST"])
@validate_schema(single_company_form)
def data_company_add():
    return _data_company_save()


@registry.route('/data/company', methods=["PUT"])
@validate_schema(single_company_form)
def data_company_update():
    return _data_company_save()


def _data_company_save():
    check_is_in_circle("admin")

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
    employees = CompanyEmployee.list_by_company(company.id)
    db.session.commit()
    return jsonify(company_to_json(company, employees))


###############################################################################
# HTML Pages


@core.route('/')
def index():
    if flask_login.current_user.is_authenticated:
        account = flask_login.current_user.account
        circles = account_management.get_circles_for_account(account.id)
        badges = badge_management.badges_for_account(account.id)
        account = account_to_json(account, circles, badges)
    else:
        account = None

    return render_template("index.html", account=account)


@core.route('/logout', methods=['GET'])
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for('core.index'))


@core.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        show_message = flask.request.args.get('show_message') or ''
        username = flask.request.args.get('username') or ''
        return render_template('login.html', show_message=show_message, username=username)

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
        return render_template('reset-password.html', reset_token=reset_token, account=account_to_json(account, [], []))

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


@core.route('/core-data-service.js')
def core_service():
    content = core_service.content

    if not content:
        content = flask.Response(registry.generate(), content_type='application/javascript')
        core_service.content = content

    return content


core_service.content = None


@core.route("/p2k16_resources.js")
def p2k16_resources():
    static = os.path.normpath(current_app.static_folder)
    buf = io.StringIO()
    ResourcesTool.run(static, buf)

    return flask.Response(buf.getvalue(), content_type='application/javascript')
