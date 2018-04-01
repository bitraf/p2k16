import logging
import string
from typing import Optional, List

import flask
from p2k16.core import P2k16UserException, mail, P2k16TechnicalException
from p2k16.core.models import db, Account, Circle, CircleMember, CircleManagementStyle
from sqlalchemy.orm import aliased

logger = logging.getLogger(__name__)


def accounts_in_circle(circle_id):
    return Account.query. \
        join(CircleMember, CircleMember.account_id == Account.id). \
        filter(CircleMember.circle_id == circle_id). \
        all()


def is_account_in_circle(account: Account, circle: Circle):
    q = Account.query. \
        join(CircleMember, CircleMember.account_id == Account.id). \
        filter(CircleMember.circle_id == circle.id). \
        filter(Account.id == account.id)
    return db.session.query(db.literal(True)).filter(q.exists()).scalar()


def get_circles_for_account(account_id: int) -> List[Circle]:
    return Circle.query. \
        join(CircleMember, CircleMember.circle_id == Circle.id). \
        filter(CircleMember.account_id == account_id). \
        all()


def get_circles_with_admin_access(account_id: int) -> List[Circle]:
    """
    SELECT
      management_style,
      c_name
    FROM (
           SELECT
             'SELF_ADMIN'       AS management_style,
             c.management_style AS c_management_style,
             c.admin_circle     AS c_admin_circle,
             c.created_by       AS c_created_by,
             c.updated_by       AS c_updated_by,
             c.id               AS c_id,
             c.created_at       AS c_created_at,
             c.updated_at       AS c_updated_at,
             c.name             AS c_name,
             c.description      AS c_description
           FROM circle AS c
             JOIN circle_member ON c.id = circle_member.circle
           WHERE C.management_style = 'SELF_ADMIN' AND circle_member.account = 5
           UNION
           SELECT
             'ADMIN_CIRCLE'      AS management_style,
             c.management_style AS c_management_style,
             c.admin_circle     AS c_admin_circle,
             c.created_by       AS c_created_by,
             c.updated_by       AS c_updated_by,
             c.id               AS c_id,
             c.created_at       AS c_created_at,
             c.updated_at       AS c_updated_at,
             c.name             AS c_name,
             c.description      AS c_description
           FROM circle AS ac
             JOIN circle AS C ON C.admin_circle = ac.id
             JOIN circle_member ON C.id = circle_member.circle
           WHERE C.management_style = 'ADMIN_CIRCLE' AND circle_member.account = 5
         ) AS anon_1
    """
    ac = aliased(Circle, name="ac")
    c = aliased(Circle, name="c")

    self_admin = db.session.query(c). \
        join(c.members). \
        filter(CircleMember.account_id == account_id). \
        filter(c._management_style == CircleManagementStyle.SELF_ADMIN.name)

    admin_circle = db.session.query(c). \
        join(ac, c.admin_circle_id == ac.id). \
        join(c.members). \
        filter(c._management_style == CircleManagementStyle.ADMIN_CIRCLE.name). \
        filter(CircleMember.account_id == account_id)

    return self_admin.union(admin_circle).all()


def _load_circle_admin(account_id, circle_id, admin_id):
    account = Account.find_account_by_id(account_id)
    admin = Account.find_account_by_id(admin_id)
    circle = Circle.find_by_id(circle_id)

    if account is None or admin is None or circle is None:
        raise P2k16UserException('Bad values')

    return account, admin, circle


def can_admin_circle(account: Account, circle: Circle):
    if circle.management_style == CircleManagementStyle.ADMIN_CIRCLE:
        admin_circle = circle.admin_circle

        if admin_circle is None:
            raise P2k16TechnicalException("There is no admin circle for circle {} configured".format(circle.name))

        return is_account_in_circle(account, admin_circle)
    elif circle.management_style == CircleManagementStyle.SELF_ADMIN:
        return is_account_in_circle(account, circle)
    else:
        raise P2k16TechnicalException("Unknown circle management style: {}".format(circle.management_style.name))


def _assert_can_admin_circle(admin: Account, circle: Circle):
    if can_admin_circle(admin, circle):
        return

    if circle.management_style == CircleManagementStyle.ADMIN_CIRCLE:
        raise P2k16UserException("{} is not in the admin circle ({}) for circle {}".
                                 format(admin.username, circle.admin_circle.name, circle.name))
    elif circle.management_style == CircleManagementStyle.SELF_ADMIN:
        raise P2k16UserException("%s is not an admin of %s".format(admin.username, circle.name))


def add_account_to_circle(account: Account, circle: Circle, admin: Account):
    logger.info("Adding %s to circle %s, admin=%s" % (account.username, circle.name, admin.username))

    _assert_can_admin_circle(admin, circle)

    db.session.add(CircleMember(circle, account))


def remove_account_from_circle(account: Account, circle: Circle, admin: Account):
    logger.info("Removing %s from circle %s, admin=%s" % (account.username, circle.name, admin.username))

    _assert_can_admin_circle(admin, circle)

    cm = CircleMember.query.filter_by(account_id=account.id, circle_id=circle.id).one_or_none()

    logger.info("cm={}".format(cm))

    if cm:
        db.session.delete(cm)


def start_reset_password(username: string) -> Optional[Account]:
    logger.info('Resetting password for {}'.format(username))

    account = Account.find_account_by_username(username)

    if account is None:
        account = Account.find_account_by_email(username)

    if account is None:
        logger.info('Could not find account by username or email: {}'.format(username))
        return None

    account.create_new_reset_token()

    url = flask.url_for('core.reset_password_form', reset_token=account.reset_token, _external=True)
    logger.info('Reset URL: {}'.format(url))

    mail.send_password_recovery(account, url)

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
