from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Numeric

import flask_bcrypt
import string
import uuid
from datetime import datetime, timedelta
from p2k16.core.database import db
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from typing import Optional


class Account(db.Model):
    __tablename__ = 'account'
    __versioned__ = {}

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    _password = Column('password', String(100))
    name = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)

    reset_token = Column(String(50), unique=True)
    reset_token_validity = Column(DateTime)

    auth_events = relationship("AuditRecord", back_populates="account")
    membership = relationship("Membership", back_populates="account")
    circle_memberships = relationship("CircleMember", back_populates="account",
                                      foreign_keys="[CircleMember.account_id]")
    membership_payments = relationship("MembershipPayment", back_populates="account")

    def __init__(self, username, email, name=None, phone=None, password=None):
        self.username = username
        self.email = email
        self.password = password
        self.name = name
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
        return '<Account:%r, username=%s>' % (self.id, self.username)

    @staticmethod
    def find_account_by_id(_id) -> Optional['Account']:
        return Account.query.filter(Account.id == _id).one_or_none()

    @staticmethod
    def find_account_by_username(username) -> Optional['Account']:
        return Account.query.filter(Account.username == username).one_or_none()

    @staticmethod
    def find_account_by_email(email) -> Optional['Account']:
        return Account.query.filter(Account.email == email).one_or_none()

    @staticmethod
    def find_account_by_reset_token(reset_token) -> Optional['Account']:
        return Account.query.filter(Account.reset_token == reset_token).one_or_none()


class Circle(db.Model):
    __tablename__ = 'circle'
    __versioned__ = {}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(50), unique=True, nullable=False)
    members = relationship("CircleMember", back_populates="circle")

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __repr__(self):
        return '<Circle:%s>' % self.id

    @staticmethod
    def find_by_id(id) -> Optional["Circle"]:
        return Circle.query.filter(Circle.id == id).one_or_none()

    @staticmethod
    def find_by_name(name) -> Optional["Circle"]:
        return Circle.query.filter(Circle.name == name).one_or_none()

    @staticmethod
    def get_by_name(name) -> "Circle":
        return Circle.query.filter(Circle.name == name).one()


class CircleMember(db.Model):
    __tablename__ = 'circle_member'
    __versioned__ = {}

    id = Column(Integer, primary_key=True)
    circle_id = Column(Integer, ForeignKey('circle.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    issuer_id = Column(Integer, ForeignKey('account.id'), nullable=False)

    db.UniqueConstraint(circle_id, account_id)

    circle = relationship("Circle")
    account = relationship("Account", foreign_keys=[account_id])
    issuer = relationship("Account", foreign_keys=[issuer_id])

    def __init__(self, circle: Circle, account: Account, issuer: Account):
        self.circle_id = circle.id
        self.account_id = account.id
        self.issuer_id = issuer.id

    def __repr__(self):
        return '<CircleMember:%s, circle=%s, account=%s>' % (self.id, self.circle_id, self.account_id)


class AuditRecord(db.Model):
    __tablename__ = 'audit_record'
    __versioned__ = {}

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('account.id'))
    timestamp = Column(DateTime, nullable=False)
    object = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)

    account = relationship("Account", back_populates="auth_events")

    def __init__(self, account_id: int, object: string, action: string):
        self.timestamp = datetime.now()
        self.account_id = account_id
        self.object = object
        self.action = action

    def __repr__(self):
        return '<AuditRecord:%r, account=%s>' % (self.id, self.account_id)


class Membership(db.Model):
    __tablename__ = 'membership'
    __versioned__ = {}

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    first_membership = Column(DateTime, nullable=False)
    start_membership = Column(DateTime, nullable=False)
    fee = Column(Integer, nullable=False)

    account = relationship("Account", back_populates="membership")

    def __init__(self, account, fee):
        self.account_id = account.id
        self.fee = fee
        self.first_membership = datetime.now()
        self.start_membership = self.first_membership

    def __repr__(self):
        return '<Membership:%r, fee=%r>' % (self.account_id, self.fee)


class MembershipPayment(db.Model):
    __tablename__ = 'membership_payment'
    __versioned__ = {}

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    membership_id = Column(String(50), unique=True, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    amount = Column(Numeric(8, 2), nullable=False)
    payment_date = Column(DateTime, nullable=True)

    account = relationship("Account", back_populates="membership_payments")

    def __init__(self, account: Account, membership_id, start_date, end_date, amount, payment_date):
        self.account_id = account.id

        self.membership_id = membership_id
        self.start_date = start_date
        self.end_date = end_date
        self.amount = amount
        self.payment_date = payment_date

    def __repr__(self):
        return '<MembershipPayment:%r, %r, start_date=%r, end_date=%r, amount=%r>' % (
            self.id, self.account_id, self.start_date, self.end_date, self.amount)
