import crypt
import string
import uuid
from datetime import datetime, timedelta
from typing import Optional

import flask_bcrypt
from p2k16.core import P2k16TechnicalException
from p2k16.core.database import db
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Numeric, Boolean
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship


class ModelSupport(object):
    def __init__(self):
        self.stack = []

    def push(self, account: "Account"):
        if not account:
            raise P2k16TechnicalException("account is None")

        db.session.flush()  # Make sure all callbacks are executed before modifying the stack
        self.stack.append(account)

    def pop(self):
        db.session.flush()  # Make sure all callbacks are executed before modifying the stack
        self.stack.pop()

    def run_as(self, account: "Account"):
        this = self

        class RunAs(object):
            def __enter__(self):
                this.push(account)

            def __exit__(self, exc_type, exc_val, exc_tb):
                this.pop()

        return RunAs()

    @property
    def current_account(self) -> "Account":
        if len(self.stack) == 0:
            raise P2k16TechnicalException("No current account")

        return self.stack[-1]

    def before_flush(self, obj):
        if isinstance(obj, TimestampMixin):
            print("TimestampMixin: created={}, updated={}".format(obj.created_at, obj.updated_at))
            obj.created_at = datetime.now()
            obj.updated_at = datetime.now()

        if isinstance(obj, ModifiedByMixin):
            account = model_support.current_account
            print("ModifiedByMixin: created={}, updated={}, ca={}".
                  format(obj.created_by_id, obj.updated_by_id, account.username if account else "None"))

            obj.created_by_id = account.id if account else None
            obj.updated_by_id = account.id if account else None


model_support = ModelSupport()


class P2k16Mixin(object):
    id = Column(Integer, primary_key=True)


class TimestampMixin(object):
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    def __init__(self):
        super().__init__()


class ModifiedByMixin(object):

    @declared_attr
    def created_by_id(cls):
        return Column("created_by", Integer, ForeignKey('account.id'))

    @declared_attr
    def updated_by_id(cls):
        return Column("updated_by", Integer, ForeignKey('account.id'))

    @declared_attr
    def created_by(cls):
        return relationship("Account", foreign_keys=[cls.created_by_id])

    @declared_attr
    def updated_by(cls):
        return relationship("Account", foreign_keys=[cls.updated_by_id])

    def __init__(self):
        super().__init__()
        self.created_by_id = None
        self.updated_by_id = None


class Account(TimestampMixin, P2k16Mixin, db.Model):
    __tablename__ = 'account'
    __versioned__ = {}

    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    _password = Column('password', String(100))
    name = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)

    reset_token = Column(String(50), unique=True)
    reset_token_validity = Column(DateTime)

    # This class should be kept relation-free to keep the number of direct dependencies on Account to a minimum.
    # The alternative is that almost all models depend on Account which leads to a 'big ball of mud'
    # (https://en.wikipedia.org/wiki/Big_ball_of_mud) - trygvis

    # audit_records = relationship("AuditRecord", foreign_keys="AuditRecord.created_by_id", back_populates="created_by")
    # membership = relationship("Membership", foreign_keys="Membership.created_by_id", back_populates="account")
    # circle_memberships = relationship("CircleMember", foreign_keys="CircleMember.account_id", back_populates="account")
    # membership_payments = relationship("MembershipPayment", foreign_keys="MembershipPayment.account_id",
    #                                    back_populates="account")

    def __init__(self, username, email, name=None, phone=None, password=None):
        super().__init__()
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
        if self.password.startswith("$2b$"):
            bs = bytes(self._password, 'utf-8')
            return flask_bcrypt.check_password_hash(bs, password)
        if self.password.startswith("$6$"):
            salt = self.password
            crypted = crypt.crypt(password, salt)
            return crypted == self._password
        return False

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


class Circle(TimestampMixin, ModifiedByMixin, P2k16Mixin, db.Model):
    __tablename__ = 'circle'
    __versioned__ = {}

    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(50), unique=True, nullable=False)
    members = relationship("CircleMember", back_populates="circle")

    def __init__(self, name, description):
        super().__init__()
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


class CircleMember(TimestampMixin, ModifiedByMixin, P2k16Mixin, db.Model):
    __tablename__ = 'circle_member'
    __versioned__ = {}

    circle_id = Column("circle", Integer, ForeignKey('circle.id'), nullable=False)
    account_id = Column("account", Integer, ForeignKey('account.id'), nullable=False)

    db.UniqueConstraint(circle_id, account_id)

    circle = relationship("Circle")
    account = relationship("Account", foreign_keys=[account_id])

    def __init__(self, circle: Circle, account: Account):
        super().__init__()
        self.circle_id = circle.id
        self.account_id = account.id

    def __repr__(self):
        return '<CircleMember:%s, circle=%s, account=%s>' % (self.id, self.circle_id, self.account_id)


class AuditRecord(TimestampMixin, ModifiedByMixin, P2k16Mixin, db.Model):
    __tablename__ = 'audit_record'
    __versioned__ = {}

    timestamp = Column(DateTime, nullable=False)
    object = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)

    def __init__(self, object: string, action: string):
        super().__init__()
        self.timestamp = datetime.now()
        self.object = object
        self.action = action

    def __repr__(self):
        return '<AuditRecord:%r, account=%s>' % (self.id, self.created_by)


class Membership(TimestampMixin, ModifiedByMixin, P2k16Mixin, db.Model):
    __tablename__ = 'membership'
    __versioned__ = {}

    first_membership = Column(DateTime, nullable=False)
    start_membership = Column(DateTime, nullable=False)
    fee = Column(Integer, nullable=False)

    def __init__(self, fee):
        super().__init__()
        self.fee = fee
        self.first_membership = datetime.now()
        self.start_membership = self.first_membership

    def __repr__(self):
        return '<Membership:%r, fee=%r>' % (self.id, self.fee)


class MembershipPayment(TimestampMixin, ModifiedByMixin, P2k16Mixin, db.Model):
    __tablename__ = 'membership_payment'
    __versioned__ = {}

    stripe_id = Column("stripe_id", String(50), unique=True, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    amount = Column(Numeric(8, 2), nullable=False)
    payment_date = Column(DateTime, nullable=True)

    def __init__(self, stripe_id, start_date, end_date, amount, payment_date):
        super().__init__()
        self.stripe_id = stripe_id
        self.start_date = start_date
        self.end_date = end_date
        self.amount = amount
        self.payment_date = payment_date

    def __repr__(self):
        return '<MembershipPayment:%r, %r, start_date=%r, end_date=%r, amount=%r>' % (
            self.id, self.created_by_id, self.start_date, self.end_date, self.amount)


class StripeCustomer(TimestampMixin, ModifiedByMixin, P2k16Mixin, db.Model):
    __tablename__ = 'stripe_customer'
    __versioned__ = {}

    stripe_id = Column("stripe_id", String(50), unique=True, nullable=False)

    def __init__(self, stripe_id):
        super().__init__()
        self.stripe_id = stripe_id

    def __repr__(self):
        return '<StripeCustomer:%r, %r, stripe_id=%r>' % (
            self.id, self.created_by_id, self.stripe_id)


class Company(TimestampMixin, ModifiedByMixin, P2k16Mixin, db.Model):
    __tablename__ = 'company'
    __versioned__ = {}

    name = Column(String(50), unique=True, nullable=False)
    active = Column(Boolean, nullable=False)

    contact_id = Column("contact", Integer, ForeignKey('account.id'), nullable=False)
    contact = relationship("Account", foreign_keys=[contact_id])

    def __init__(self, name, contact: Account, active: bool):
        self.name = name
        self.contact_id = contact.id
        self.active = active

    def __repr__(self):
        return '<Company:%r, name=%r>' % (self.id, self.name)

    @staticmethod
    def find_by_id(_id) -> Optional['Company']:
        return Company.query.filter(Company.id == _id).one_or_none()


class CompanyEmployee(TimestampMixin, ModifiedByMixin, P2k16Mixin, db.Model):
    __tablename__ = 'company_employee'
    __versioned__ = {}

    company_id = Column("company", Integer, ForeignKey('company.id'), nullable=False)
    company = relationship("Company", foreign_keys=[company_id])
    account_id = Column("account", Integer, ForeignKey('account.id'), nullable=False)
    account = relationship("Account", foreign_keys=[account_id])

    def __init__(self, company: Company, account: Account):
        self.company_id = company.id
        self.account_id = account.id

    def __repr__(self):
        return '<CompanyEmployee:%r, company=%r, account=%r>' % (self.id, self.company_id, self.account_id)

    @staticmethod
    def list_by_company(company_id: int) -> Optional['Company']:
        return CompanyEmployee.query.filter(Company.id == company_id).all()

    @staticmethod
    def find_by_company_and_account(company_id: int, account_id: int) -> Optional['Company']:
        return CompanyEmployee.query. \
            filter(CompanyEmployee.company_id == company_id,
                   CompanyEmployee.account_id == account_id) \
            .one_or_none()
