import string
from typing import Optional, List

import flask
from p2k16 import P2k16UserException, app
from p2k16.database import db
from p2k16.models import User, Group, GroupMember


def users_in_group(group_id):
    return User.query. \
        join(GroupMember, GroupMember.user_id == User.id). \
        filter(GroupMember.group_id == group_id). \
        all()


def is_user_in_group(group: Group, user: User):
    q = User.query. \
        join(GroupMember, GroupMember.user_id == User.id). \
        filter(GroupMember.group_id == group.id). \
        filter(User.id == user.id)
    return db.session.query(db.literal(True)).filter(q.exists()).scalar()


def groups_by_user(user_id: int) -> List[Group]:
    return Group.query.\
        join(GroupMember, GroupMember.group_id == Group.id).\
        filter(GroupMember.user_id == user_id).\
        all()


def add_user_to_group(user_id, group_id, admin_id):
    user = User.find_user_by_id(user_id)
    admin = User.find_user_by_id(admin_id)
    group = Group.find_by_id(group_id)

    if user is None or admin is None or group is None:
        raise P2k16UserException('Bad values')

    group_admin = Group.find_by_name(group.name + '-admin')

    if group_admin is None:
        raise P2k16UserException('No admin-group for group "%s"' % group.name)

    if not is_user_in_group(group_admin, admin):
        raise P2k16UserException('User %s is not an administrator of %s' % (admin.username, group.description))

    db.session.add(GroupMember(group, user, admin))


def start_reset_password(username: string) -> Optional[User]:
    app.logger.info('Resetting password for {}'.format(username))

    user = User.find_user_by_username(username)

    if user is None:
        user = User.find_user_by_email(username)

    if user is None:
        app.logger.info('Could not find user by username or email: {}'.format(username))
        return None

    user.create_new_reset_token()

    url = flask.url_for('core.reset_password_form', reset_token=user.reset_token, _external=True)
    app.logger.info('Reset URL: {}'.format(url))

    # TODO: send email
    return user


def register_user(username: str, email: str, name: str, password: str, phone: str) -> User:
    user = User.find_user_by_username(username)
    if user:
        raise P2k16UserException("Username is taken")

    user = User.find_user_by_email(email)
    if user:
        raise P2k16UserException("Email is already registered")

    user = User(username, email, name, phone, password)
    db.session.add(user)
    return user
