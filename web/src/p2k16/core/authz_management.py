import logging

from p2k16.core import account_management, membership_management
from p2k16.core.models import Circle, Company

logger = logging.getLogger(__name__)


def can_haz_door_access(account, doors = []):

    # If called with no doors, this basically checks if you are paying member
    # or employed at a company. It is used to show the buttons on the front page
    # for now, in the future, we probably want to make those dependant on access,
    # so you only see buttons you have access to.

    # Find all circles needed for these doors

    circles = {circle for door in doors for circle in door.circle}

    # If you lack access to one of the doors attempted, you cant open anything
    access = True
    for circle in circles:
        door_circle = Circle.find_by_name(circle)
        if door_circle is None:
            access = False
        elif not account_management.is_account_in_circle(account, door_circle):
            access = False

    if access and membership_management.active_member(account):
        return True

    if Company.is_account_employed(account.id):
        return True

    return False
