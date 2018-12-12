import logging
import string
from typing import Optional, List

import flask
from p2k16.core import P2k16UserException, mail, P2k16TechnicalException, account_management, membership_management
from p2k16.core.models import db, Account, Circle, CircleMember, CircleManagementStyle, Company
from sqlalchemy.orm import aliased

logger = logging.getLogger(__name__)


def can_haz_door_access(account):
    door_circle = Circle.get_by_name('door')

    if account_management.is_account_in_circle(account, door_circle) and membership_management.active_member(account):
        return True

    if (Company.is_account_employed(account.id)):
        return True
    return False

