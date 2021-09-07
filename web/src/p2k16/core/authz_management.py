import logging

from p2k16.core import account_management
from p2k16.core.models import Circle, Company, CircleMember, StripePayment

logger = logging.getLogger(__name__)


def can_haz_door_access(account, doors = []):

    # If called with no doors, this basically checks if you are paying member
    # or employed at a company. It is used to show the buttons on the front page
    # for now, in the future, we probably want to make those dependant on access,
    # so you only see buttons you have access to.


    # Employed people have access to all doors for now
    if Company.is_account_employed(account.id):
        return True

    # If you aren't a paying member, you have access to no doors
    # Check paying membership
    if not StripePayment.is_account_paying_member(account.id):
        return False


    # Find all circles the account is a member of, then iterate the doors and check
    memberships = {circle.name for circle in
                   account_management.get_circles_for_account(account.id)}

    for door in doors:
        if not memberships & door.circles:
            # No overlap, so we lack access to this door, lets return false
            return False

    # If we get here, we had access to all doors, so return True
    return True
