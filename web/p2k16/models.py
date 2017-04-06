import string
import uuid
from datetime import datetime, timedelta
from typing import Optional

import flask_bcrypt
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from p2k16.database import db


class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    _password = Column('password', String(100))
    first_name = Column(String(50), unique=True, nullable=True)
    last_name = Column(String(50), unique=True, nullable=True)
    phone = Column(String(50), unique=True, nullable=True)

    reset_token = Column(String(50), unique=True)
    reset_token_validity = Column(DateTime)

    auth_events = relationship("AuditRecord", back_populates="user")
    membership = relationship("Membership", back_populates="user")
    group_memberships = relationship("GroupMember", back_populates="user", foreign_keys="[GroupMember.user_id]")

    def __init__(self, username, email, first_name=None, last_name=None, phone=None, password=None):
        self.username = username
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone

    def display_name(self):
        return self.username

    def create_new_reset_token(self):
        self.reset_token = str(uuid.uuid4())
        self.reset_token_validity = datetime.now() + timedelta(hours=24)

    def is_valid_reset_token(self, reset_token):
        return self.reset_token == reset_token and datetime.now() < self.reset_token_validity

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        pw = flask_bcrypt.generate_password_hash(plaintext)
        self._password = pw.decode('utf-8')
        self.reset_token = None
        self.reset_token_validity = None

    def valid_password(self, password) -> bool:
        bs = bytes(self._password, 'utf-8')
        return flask_bcrypt.check_password_hash(bs, password)

    def __repr__(self):
        return '<User:%r, username=%s>' % (self.id, self.username)

    @staticmethod
    def find_user_by_id(_id) -> Optional['User']:
        return User.query.filter(User.id == _id).one_or_none()

    @staticmethod
    def find_user_by_username(username) -> Optional['User']:
        return User.query.filter(User.username == username).one_or_none()

    @staticmethod
    def find_user_by_email(email) -> Optional['User']:
        return User.query.filter(User.email == email).one_or_none()

    @staticmethod
    def find_user_by_reset_token(reset_token) -> Optional['User']:
        return User.query.filter(User.reset_token == reset_token).one_or_none()


class Group(db.Model):
    __tablename__ = 'user_group'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(50), unique=True, nullable=False)
    members = relationship("GroupMember", back_populates="group")

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __repr__(self):
        return '<Group:%s>' % self.id

    @staticmethod
    def find_by_id(id) -> Optional["Group"]:
        return Group.query.filter(Group.id == id).one_or_none()

    @staticmethod
    def find_by_name(name) -> Optional["Group"]:
        return Group.query.filter(Group.name == name).one_or_none()

    @staticmethod
    def get_by_name(name) -> "Group":
        return Group.query.filter(Group.name == name).one()


class GroupMember(db.Model):
    __tablename__ = 'group_member'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('user_group.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    issuer_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    db.UniqueConstraint(group_id, user_id)

    group = relationship("Group")
    user = relationship("User", foreign_keys=[user_id])
    issuer = relationship("User", foreign_keys=[issuer_id])

    def __init__(self, group: Group, user: User, issuer: User):
        self.group_id = group.id
        self.user_id = user.id
        self.issuer_id = issuer.id

    def __repr__(self):
        return '<GroupMember:%s, group=%s, user=%s>' % (self.id, self.group_id, self.user_id)


class AuditRecord(db.Model):
    __tablename__ = 'audit_record'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, nullable=False)
    object = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)

    user = relationship("User", back_populates="auth_events")

    def __init__(self, user_id: int, object: string, action: string):
        self.timestamp = datetime.now()
        self.user_id = user_id
        self.object = object
        self.action = action

    def __repr__(self):
        return '<AuditRecord:%r, user=%s>' % (self.id, self.user_id)


class Membership(db.Model):
    __tablename__ = 'membership'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    first_membership = Column(DateTime, nullable=False)
    start_membership = Column(DateTime, nullable=False)
    fee = Column(Integer, nullable=False)

    user = relationship("User", back_populates="membership")

    def __init__(self, user, fee):
        self.user_id = user.id
        self.fee = fee
        self.first_membership = datetime.now()
        self.start_membership = self.first_membership

    def __repr__(self):
        return '<Membership:%r, fee=%r>' % (self.user_id, self.fee)
