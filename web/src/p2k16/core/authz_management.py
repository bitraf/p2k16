import logging

from p2k16.core import account_management, membership_management
from p2k16.core.models import Circle, Company

logger = logging.getLogger(__name__)


def can_haz_door_access(account):
    door_circle = Circle.get_by_name('door')

    if account_management.is_account_in_circle(account, door_circle) and membership_management.active_member(account):
        return True

    if Company.is_account_employed(account.id):
        return True

    return False
