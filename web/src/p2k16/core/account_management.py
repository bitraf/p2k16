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
             JOIN circle AS C ON c.admin_circle = ac.id
             JOIN circle_member ON ac.id = circle_member.circle
           WHERE c.management_style = 'ADMIN_CIRCLE' AND circle_member.account = 5
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
        join(ac.members). \
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
        raise P2k16UserException("{} is not an admin of {}".format(admin.username, circle.name))


def add_account_to_circle(account: Account, circle: Circle, admin: Account, comment: str):
    logger.info("Adding %s to circle %s, admin=%s" % (account.username, circle.name, admin.username))

    _assert_can_admin_circle(admin, circle)

    if is_account_in_circle(account, circle):
        raise P2k16UserException("Account is already a member of the cirlce, cannot be added again")

    circle.add_member(account, comment)


def remove_account_from_circle(account: Account, circle: Circle, admin: Account):
    logger.info("Removing %s from circle %s, admin=%s" % (account.username, circle.name, admin.username))

    _assert_can_admin_circle(admin, circle)

    if not is_account_in_circle(account, circle):
        raise P2k16UserException("Account isn't a member of the circle, cannot be removed")

    circle.remove_member(account)


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

    if name is None:
        raise P2k16UserException("Name cannot be empty.")

    if "@" in username:
        raise P2k16UserException("Username looks like an email, it should be a simple string")

    account = Account(username, email, name, phone, password)
    db.session.add(account)
    return account


# This function raises technical exceptions as a last resort. Methods using this function should check the token or
# password before calling this.
def set_password(account: Account, new_password: str, old_password: Optional[str] = None,
                 reset_token: Optional[str] = None):
    if reset_token is not None:
        if not account.is_valid_reset_token(reset_token):
            raise P2k16TechnicalException("Invalid reset token")
    elif old_password is not None:
        if not account.valid_password(old_password):
            raise P2k16TechnicalException("Bad password")
    else:
        raise P2k16TechnicalException("Either old_password or reset_token has to be set.")

    account.password = new_password
    logger.info('Updating password for account={}'.format(account))


def create_circle(name: str, description: str, comment_required_for_membership, management_style: CircleManagementStyle,
                  admin_circle_name: Optional[str] = None, username: Optional[str] = None,
                  comment: Optional[str] = None) -> Circle:
    c = Circle(name, description, comment_required_for_membership, management_style)

    if management_style == CircleManagementStyle.ADMIN_CIRCLE:
        if admin_circle_name is None:
            raise P2k16UserException("An admin circle is required when management style is set to ADMIN_CIRCLE")

        admin_circle = Circle.find_by_name(admin_circle_name)

        if admin_circle is None:
            raise P2k16UserException("No such circle: {}".format(admin_circle_name))

        c.admin_circle = admin_circle

    elif management_style == CircleManagementStyle.SELF_ADMIN:
        if username is None:
            raise P2k16UserException("An initial member's username is required when management style is set to "
                                     "SELF_ADMIN")

        account = Account.find_account_by_username(username)

        if account is None:
            raise P2k16UserException("No such account: {}".format(username))

        c.add_member(account, comment or "")

    db.session.add(c)

    return c
