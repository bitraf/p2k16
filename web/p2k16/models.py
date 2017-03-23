from datetime import datetime
import flask_bcrypt
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from p2k16.database import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    _password = Column('password', String(100))

    auth_events = relationship("AuthEvent", back_populates="user")
    membership = relationship("Membership", back_populates="user")

    def __init__(self, username, email, password=None):
        self.username = username
        self.email = email
        self._password = password

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = flask_bcrypt.generate_password_hash(plaintext)

    def __repr__(self):
        return '<User %r>' % self.username


def find_user_by_id(id):
    return User.query.filter(User.id == id).one_or_none()


def find_user_by_email(email):
    return User.query.filter(User.email == email).one_or_none()


class AuthEvent(Base):
    __tablename__ = 'auth_event'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    timestamp = Column(DateTime, nullable=False)
    location = Column(String(50), nullable=False)

    user = relationship("User", back_populates="auth_events")

    def __init__(self):
        self.timestamp = None

    def __repr__(self):
        return '<AuthEvent %r>' % self.user_id


class Membership(Base):
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
