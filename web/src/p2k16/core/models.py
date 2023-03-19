import crypt
import enum
import logging
import uuid
from datetime import datetime, timedelta, timezone
from itertools import chain
from typing import Optional, List, Iterable

import flask_bcrypt
from flask_sqlalchemy import SQLAlchemy
from p2k16.core import P2k16TechnicalException, P2k16UserException
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Numeric, Boolean, Sequence, event, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

logger = logging.getLogger(__name__)

db = SQLAlchemy()

from sqlalchemy_continuum.plugins import FlaskPlugin
from sqlalchemy_continuum import make_versioned

make_versioned(plugins=[FlaskPlugin()], user_cls=None)


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

    def is_empty(self):
        return len(self.stack) == 0

    @property
    def current_account(self) -> "Account":
        if len(self.stack) == 0:
            raise P2k16TechnicalException("No current account")

        return self.stack[-1]

    def before_flush(self, obj):
        if isinstance(obj, CreatedAtMixin):
            obj.created_at = datetime.now()

        if isinstance(obj, UpdatedAtMixin):
            obj.updated_at = datetime.now()

        if isinstance(obj, CreatedByMixin):
            account = self.current_account

            obj.created_by_id = account.id if account else None

        if isinstance(obj, UpdatedByMixin):
            account = self.current_account

            obj.updated_by_id = account.id if account else None


model_support = ModelSupport()


class P2k16Mixin(object):
    id_seq = Sequence('id_seq', metadata=db.Model.metadata)
    id = Column(Integer, id_seq, primary_key=True)


class CreatedAtMixin(object):
    created_at = Column(DateTime, nullable=False)

    def __init__(self):
        super().__init__()


class UpdatedAtMixin(object):
    updated_at = Column(DateTime, nullable=False)

    def __init__(self):
        super().__init__()


class CreatedByMixin(object):

    @declared_attr
    def created_by_id(cls):
        return Column("created_by", Integer, ForeignKey('account.id'))

    @declared_attr
    def created_by(cls):
        return relationship("Account", foreign_keys=[cls.created_by_id])

    def __init__(self):
        super().__init__()
        self.created_by_id = None


class UpdatedByMixin(object):

    @declared_attr
    def updated_by_id(cls):
        return Column("updated_by", Integer, ForeignKey('account.id'))

    @declared_attr
    def updated_by(cls):
        return relationship("Account", foreign_keys=[cls.updated_by_id])

    def __init__(self):
        super().__init__()
        self.updated_by_id = None


# This is probably the mixin you should use
class DefaultMixin(P2k16Mixin, CreatedAtMixin, CreatedByMixin, UpdatedAtMixin, UpdatedByMixin):
    pass


class ImmutableDefaultMixin(P2k16Mixin, CreatedAtMixin, CreatedByMixin):
    pass


# This is the default Mixin without the CreatedBy/UpdatedBy mixins to prevent recursion.
class Account(P2k16Mixin, CreatedAtMixin, UpdatedAtMixin, db.Model):
    __tablename__ = 'account'
    __versioned__ = {}

    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    _password = Column('password', String(100))
    name = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    system = Column(Boolean, nullable=False)

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
        self.system = False

    def display_name(self):
        return self.username

    def create_new_reset_token(self):
        self.reset_token = str(uuid.uuid4())
        self.reset_token_validity = datetime.now() + timedelta(hours=24)

    def is_valid_reset_token(self, reset_token):
        now = datetime.now(timezone.utc)

        return self.reset_token == reset_token and now < self.reset_token_validity

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, plaintext):
        if self.system:
            raise P2k16TechnicalException("System users can't have a password")

        pw = flask_bcrypt.generate_password_hash(plaintext)
        self._password = pw.decode('utf-8')
        self.reset_token = None
        self.reset_token_validity = None

    def valid_password(self, password) -> bool:
        if self.system:
            raise P2k16TechnicalException("System users can't log in")

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
    def get_by_id(_id) -> "Account":
        return Account.query.filter(Account.id == _id).one()

    @staticmethod
    def find_account_by_username(username) -> Optional['Account']:
        return Account.query.filter(func.lower(Account.username) == func.lower(username)).one_or_none()

    @staticmethod
    def get_by_username(username) -> "Account":
        return Account.query.filter(func.lower(Account.username) == func.lower(username)).one()

    @staticmethod
    def find_account_by_email(email) -> Optional['Account']:
        return Account.query.filter(func.lower(Account.email) == func.lower(email)).one_or_none()

    @staticmethod
    def find_account_by_reset_token(reset_token) -> Optional['Account']:
        return Account.query.filter(Account.reset_token == reset_token).one_or_none()

    @staticmethod
    def all_user_accounts() -> List["Account"]:
        return Account.query.filter(func.not_(Account.system)).all()


class CircleManagementStyle(enum.Enum):
    ADMIN_CIRCLE = 1
    SELF_ADMIN = 2


class Circle(DefaultMixin, db.Model):
    __tablename__ = 'circle'
    __versioned__ = {}

    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(50), unique=True, nullable=False)
    comment_required_for_membership = Column(Boolean, nullable=False)
    _management_style = Column('management_style', String(50), nullable=False)

    admin_circle_id = Column("admin_circle", Integer, ForeignKey("circle.id"))
    admin_circle = relationship("Circle", remote_side="Circle.id")  # type: Optional[Circle]

    members = relationship("CircleMember", back_populates="circle",
                           cascade="all, delete-orphan")  # type: List[CircleMember]

    def __init__(self, name: str, description: str, comment_required_for_membership: bool,
                 management_style: CircleManagementStyle):
        super().__init__()
        self.name = name
        self.description = description
        self.comment_required_for_membership = comment_required_for_membership
        self._management_style = management_style.name

    @hybrid_property
    def management_style(self) -> CircleManagementStyle:
        return CircleManagementStyle[self._management_style]

    def __repr__(self):
        return '<Circle:%s, name=%s>' % (self.id, self.name)

    def add_member(self, account: Account, comment: Optional[str]):
        if comment:
            comment = comment.strip()

        if self.comment_required_for_membership and len(comment) == 0:
            raise P2k16UserException("This circle requires memberships to have a comment")

        self.members.append(CircleMember(self, account, comment))

    def remove_member(self, account: Account):
        [self.members.remove(m) for m in self.members if m.account == account]

    def on_before_insert(self):
        if self.management_style == CircleManagementStyle.SELF_ADMIN and len(self.members) == 0:
            raise P2k16UserException("A new circle which is self-administrated must have at least one member")

    def on_before_update(self):
        if self.management_style == CircleManagementStyle.SELF_ADMIN and len(self.members) == 0:
            raise P2k16UserException("A circle which is self-administrated must have at least one member")

    @staticmethod
    def find_by_id(_id) -> Optional["Circle"]:
        return Circle.query.filter(Circle.id == _id).one_or_none()

    @staticmethod
    def get_by_id(_id) -> "Circle":
        return Circle.query.filter(Circle.id == _id).one()

    @staticmethod
    def delete_by_id(_id):
        c = Circle.get_by_id(_id)
        db.session.delete(c)
        db.session.flush()

    @staticmethod
    def find_by_name(name) -> Optional["Circle"]:
        return Circle.query.filter(Circle.name == name).one_or_none()

    @staticmethod
    def get_by_name(name) -> "Circle":
        return Circle.query.filter(Circle.name == name).one()


# noinspection PyUnusedLocal
@event.listens_for(Circle, 'before_insert')
def on_circle_before_insert(mapper, connection, target: Circle):
    target.on_before_insert()


# noinspection PyUnusedLocal
@event.listens_for(Circle, 'before_update')
def on_circle_before_update(mapper, connection, target: Circle):
    target.on_before_update()


class CircleMember(DefaultMixin, db.Model):
    __tablename__ = 'circle_member'
    __versioned__ = {}

    circle_id = Column("circle", Integer, ForeignKey('circle.id'), nullable=False)
    account_id = Column("account", Integer, ForeignKey('account.id'), nullable=False)
    comment = Column("comment", String(200))

    db.UniqueConstraint(circle_id, account_id)

    circle = relationship("Circle")
    account = relationship("Account", foreign_keys=[account_id])

    def __init__(self, circle: Circle, account: Account, comment: str):
        super().__init__()
        self.circle_id = circle.id
        self.account_id = account.id
        self.comment = comment

    def __repr__(self):
        return '<CircleMember:%s, circle=%s, account=%s>' % (self.id, self.circle_id, self.account_id)


class Event(ImmutableDefaultMixin, db.Model):
    __tablename__ = 'event'
    # Not versioned, events are append-only

    domain = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)

    int1 = Column(Integer)
    int2 = Column(Integer)
    int3 = Column(Integer)
    int4 = Column(Integer)
    int5 = Column(Integer)

    text1 = Column(String(100))
    text2 = Column(String(100))
    text3 = Column(String(100))
    text4 = Column(String(100))
    text5 = Column(String(100))

    def __init__(self, domain: str, name: str,
                 int1: int = None, int2: int = None, int3: int = None, int4: int = None, int5: int = None,
                 text1: str = None, text2: str = None, text3: str = None, text4: str = None, text5: str = None):
        super().__init__()

        self.domain = domain
        self.name = name
        self.int1 = int1
        self.int2 = int2
        self.int3 = int3
        self.int4 = int4
        self.int5 = int5
        self.text1 = text1
        self.text2 = text2
        self.text3 = text3
        self.text4 = text4
        self.text5 = text5

    def __repr__(self):
        return '<Event:%r, created_by=%s, domain=%s, name=%s>' % (self.id, self.created_by_id, self.domain, self.name)


class Membership(DefaultMixin, db.Model):
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


class StripePayment(DefaultMixin, db.Model):
    __tablename__ = 'stripe_payment'
    __versioned__ = {}

    stripe_id = Column("stripe_id", String(50), unique=False, nullable=False)
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

    @staticmethod
    def is_account_paying_member(account_id):
        return StripePayment.query. \
                   filter(StripePayment.created_by_id == account_id,
                          StripePayment.end_date >= (datetime.utcnow() - timedelta(days=1))).count() > 0


class StripeCustomer(DefaultMixin, db.Model):
    __tablename__ = 'stripe_customer'
    __versioned__ = {}

    stripe_id = Column("stripe_id", String(50), unique=True, nullable=False)

    def __init__(self, stripe_id):
        super().__init__()
        self.stripe_id = stripe_id

    def __repr__(self):
        return '<StripeCustomer:%r, %r, stripe_id=%r>' % (
            self.id, self.created_by_id, self.stripe_id)


class Company(DefaultMixin, db.Model):
    __tablename__ = 'company'
    __versioned__ = {}

    name = Column(String(50), unique=True, nullable=False)
    active = Column(Boolean, nullable=False)

    contact_id = Column("contact", Integer, ForeignKey('account.id'), nullable=False)
    contact = relationship("Account", foreign_keys=[contact_id])

    employees = relationship("CompanyEmployee")  # type: Iterable[CompanyEmployee]

    def __init__(self, name, contact: Account, active: bool):
        super().__init__()
        self.name = name
        self.contact_id = contact.id
        self.active = active

    def __repr__(self):
        return '<Company:%r, name=%r>' % (self.id, self.name)

    @staticmethod
    def find_by_id(_id) -> Optional['Company']:
        return Company.query.filter(Company.id == _id).one_or_none()

    @staticmethod
    def get_by_id(_id) -> "Company":
        return Company.query.filter(Company.id == _id).one()

    @staticmethod
    def find_active_companies_with_account(account_id: int) -> List['Company']:
        return Company.query. \
            join(Company.employees). \
            filter(Company.active). \
            filter(CompanyEmployee.account_id == account_id) \
            .all()

    @staticmethod
    def is_account_employed(account_id: int) -> bool:
        return Company.query. \
                   join(Company.employees). \
                   filter(Company.active). \
                   filter(CompanyEmployee.account_id == account_id) \
                   .count() > 0


class CompanyEmployee(DefaultMixin, db.Model):
    __tablename__ = 'company_employee'
    __versioned__ = {}

    company_id = Column("company", Integer, ForeignKey('company.id'), nullable=False)
    company = relationship("Company", foreign_keys=[company_id])
    account_id = Column("account", Integer, ForeignKey('account.id'), nullable=False)
    account = relationship("Account", foreign_keys=[account_id])

    def __init__(self, company: Company, account: Account):
        super().__init__()
        self.company_id = company.id
        self.account_id = account.id

    def __repr__(self):
        return '<CompanyEmployee:%r, company=%r, account=%r>' % (self.id, self.company_id, self.account_id)

    @staticmethod
    def find_by_company_and_account(company_id: int, account_id: int) -> Optional['CompanyEmployee']:
        return CompanyEmployee.query. \
            filter(CompanyEmployee.company_id == company_id,
                   CompanyEmployee.account_id == account_id) \
            .one_or_none()


#
# Badges
#


class BadgeDescription(DefaultMixin, db.Model):
    __tablename__ = 'badge_description'
    __versioned__ = {}

    title = Column(String(50), nullable=False)
    description = Column(String(1000), nullable=False)
    slug = Column(String(50), nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(50), nullable=True)

    certification_circle_id = Column("certification_circle", Integer, ForeignKey('circle.id'), nullable=True)
    certification_circle = relationship("Circle")

    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.description = None
        self.slug = None
        self.icon = None
        self.color = None
        self.certification_circle = None


class AccountBadge(DefaultMixin, db.Model):
    __tablename__ = 'account_badge'
    __versioned__ = {}

    account_id = Column("account", Integer, ForeignKey('account.id'), nullable=False)
    account = relationship("Account", foreign_keys=[account_id])
    description_id = Column("badge_description", Integer, ForeignKey('badge_description.id'), nullable=False)
    description = relationship("BadgeDescription", foreign_keys=[description_id])

    awarded_by_id = Column("awarded_by", Integer, ForeignKey('account.id'), nullable=False)
    awarded_by = relationship("Account", foreign_keys=[awarded_by_id])

    def __init__(self, account: Account, awarded_by: Account, description: BadgeDescription):
        super().__init__()
        self.account_id = account.id
        self.awarded_by = awarded_by
        self.description = description


#
# Tools
#
class ToolDescription(DefaultMixin, db.Model):
    __tablename__ = 'tool_description'
    __versioned__ = {}

    name = Column(String(50), nullable=False)
    description = Column(String(1000))
    circle_id = Column("circle", Integer, ForeignKey("circle.id"))
    circle = relationship("Circle", remote_side="Circle.id")  # type: Optional[Circle]

    def __init__(self, name: str, description: str, circle: Circle):
        super().__init__()
        self.name = name
        self.description = description
        self.circle_id = circle.id

    @staticmethod
    def find_by_id(_id) -> Optional['ToolDescription']:
        return ToolDescription.query.filter(ToolDescription.id == _id).one_or_none()


class ToolCheckout(DefaultMixin, db.Model):
    __tablename__ = 'tool_checkout'
    __versioned__ = {}

    tool_description_id = Column("tool_description", Integer, ForeignKey('tool_description.id'), nullable=False)
    tool_description = relationship("ToolDescription", foreign_keys=[tool_description_id])

    account_id = Column("account", Integer, ForeignKey('account.id'), nullable=False)
    account = relationship("Account", foreign_keys=[account_id])

    started = Column(DateTime, nullable=True)

    def __init__(self, tool: ToolDescription, account: Account, started: DateTime):
        super().__init__()
        self.tool_description = tool
        self.account = account
        self.started = started

    @staticmethod
    def find_by_tool(_tool) -> Optional['ToolCheckout']:
        return ToolCheckout.query.filter(ToolCheckout.tool_description_id == _tool.id).one_or_none()


from sqlalchemy import event


@event.listens_for(db.session, 'before_flush')
def receive_before_flush(session, flush_context, instances):
    # print("before flush!")
    # print("flush_context: {}".format(flush_context))
    # print("instances: {}".format(len(instances) if instances else "none!!"))

    for obj in chain(session.new, session.dirty):
        if session.is_modified(obj):
            model_support.before_flush(obj)


db.configure_mappers()
