import string
from typing import Optional, List

import flask
from p2k16 import P2k16UserException, app
from p2k16.database import db
from p2k16.models import Account, Circle, CircleMember


def accounts_in_circle(circle_id):
    return Account.query. \
        join(CircleMember, CircleMember.account_id == Account.id). \
        filter(CircleMember.circle_id == circle_id). \
        all()


def is_account_in_circle(circle: Circle, account: Account):
    q = Account.query. \
        join(CircleMember, CircleMember.account_id == Account.id). \
        filter(CircleMember.circle_id == circle.id). \
        filter(Account.id == account.id)
    return db.session.query(db.literal(True)).filter(q.exists()).scalar()


def get_circles_for_account(account_id: int) -> List[Circle]:
    return Circle.query.\
        join(CircleMember, CircleMember.circle_id == Circle.id).\
        filter(CircleMember.account_id == account_id).\
        all()


def add_account_to_circle(account_id, circle_id, admin_id):
    account = Account.find_account_by_id(account_id)
    admin = Account.find_account_by_id(admin_id)
    circle = Circle.find_by_id(circle_id)

    if account is None or admin is None or circle is None:
        raise P2k16UserException('Bad values')

    circle_admin = Circle.find_by_name(circle.name + '-admin')

    if circle_admin is None:
        raise P2k16UserException('No admin-circle for circle "%s"' % circle.name)

    if not is_account_in_circle(circle_admin, admin):
        raise P2k16UserException('Account %s is not an administrator of %s' % (admin.username, circle.description))

    db.session.add(CircleMember(circle, account, admin))


def start_reset_password(username: string) -> Optional[Account]:
    app.logger.info('Resetting password for {}'.format(username))

    account = Account.find_account_by_username(username)

    if account is None:
        account = Account.find_account_by_email(username)

    if account is None:
        app.logger.info('Could not find account by username or email: {}'.format(username))
        return None

    account.create_new_reset_token()

    url = flask.url_for('core.reset_password_form', reset_token=account.reset_token, _external=True)
    app.logger.info('Reset URL: {}'.format(url))

    # TODO: send email
    return account


def register_account(username: str, email: str, name: str, password: str, phone: str) -> Account:
    account = Account.find_account_by_username(username)
    if account:
        raise P2k16UserException("Username is taken")

    account = Account.find_account_by_email(email)
    if account:
        raise P2k16UserException("Email is already registered")

    account = Account(username, email, name, phone, password)
    db.session.add(account)
    return account
