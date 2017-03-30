from datetime import datetime
import flask_bcrypt
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from p2k16.database import db


class User(db.Model):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    _password = Column('password', String(100))
    first_name = Column(String(50), unique=True, nullable=False)
    last_name = Column(String(50), unique=True, nullable=False)
    phone = Column(String(50), unique=True, nullable=True)

    auth_events = relationship("AuthEvent", back_populates="user")
    membership = relationship("Membership", back_populates="user")
    group_memberships = relationship("GroupMember", back_populates="user", foreign_keys="[GroupMember.user_id]")

    def __init__(self, username, email, first_name, last_name, phone=None, password=None):
        self.username = username
        self.email = email
        self._password = password
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone


    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = flask_bcrypt.generate_password_hash(plaintext)

    def __repr__(self):
        return '<User:%r, username=%s>' % (self.id, self.username)

    @staticmethod
    def find_user_by_id(id):
        return User.query.filter(User.id == id).one_or_none()

    @staticmethod
    def find_user_by_username(username):
        return User.query.filter(User.username == username).one_or_none()


class Group(db.Model):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(50), unique=True, nullable=False)
    members = relationship("GroupMember", back_populates="group")

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __repr__(self):
        return '<Group:%s>' % self.id


class Group(db.Model):
    __tablename__ = 'group'

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
    def find_by_id(id) -> "Group":
        return Group.query.filter(Group.id == id).one_or_none()

    @staticmethod
    def find_by_name(name) -> "Group":
        return Group.query.filter(Group.name == name).one_or_none()


class GroupMember(db.Model):
    __tablename__ = 'group_member'

    id = Column(Integer, primary_key=True)
    group_id = Column(String(50), ForeignKey('group.id'), unique=True, nullable=False)
    user_id = Column(String(50), ForeignKey('user.id'), unique=True, nullable=False)
    issuer_id = Column(String(50), ForeignKey('user.id'), nullable=False)

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


class AuthEvent(db.Model):
    __tablename__ = 'auth_event'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    timestamp = Column(DateTime, nullable=False)
    location = Column(String(50), nullable=False)

    user = relationship("User", back_populates="auth_events")

    def __init__(self):
        self.timestamp = None

    def __repr__(self):
        return '<AuthEvent:%r, user=%s>' % (self.id, self.user_id)


class Membership(db.Model):
    __tablename__ = 'membership'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
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
