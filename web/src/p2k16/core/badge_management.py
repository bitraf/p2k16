import logging
from datetime import datetime
from typing import List, Optional

from p2k16.core import P2k16UserException, account_management, event_management
from p2k16.core.models import db, Account, AccountBadge, BadgeDescription, Event

logger = logging.getLogger(__name__)


@event_management.converter_for("badge", "awarded")
class BadgeAwardedEvent(object):
    def __init__(self, account_badge: AccountBadge, badge_description: Optional[BadgeDescription],
                 created_at: Optional[datetime] = None, created_by: Optional[Account] = None):
        self.account_badge = account_badge
        self.badge_description = badge_description
        self.created_at = created_at
        self.created_by = created_by

    def to_event(self):
        return {
            "int1": self.account_badge.id,
            "int2": self.badge_description.id if self.badge_description else None
        }

    @staticmethod
    def from_event(event: Event) -> "BadgeAwardedEvent":
        account_badge = AccountBadge.query.filter(AccountBadge.id == event.int1).one()
        badge_description = BadgeDescription.query.filter(BadgeDescription.id == event.int2).one_or_none()
        return BadgeAwardedEvent(account_badge, badge_description, event.created_at, event.created_by)

    def to_dict(self):
        from p2k16.web import badge_blueprint
        return {**event_management.base_dict(self), **{
            "created_at": self.created_at,
            "created_by": self.created_by,
            "created_by_username": self.created_by.username,
            "account_badge": badge_blueprint.badge_to_json(self.account_badge),
            "badge_description": badge_blueprint.badge_description_to_json(self.badge_description) if self.badge_description else None,
        }}


def _load_description(title: str) -> BadgeDescription:
    return BadgeDescription.query. \
        filter(BadgeDescription.title == title). \
        one_or_none()


def badges_for_account(account_id: int) -> List[AccountBadge]:
    return AccountBadge.query. \
        join(Account, Account.id == AccountBadge.account_id). \
        filter(Account.id == account_id)


def create_badge(receiver: Account, awarder: Account, title: str) -> AccountBadge:
    desc = _load_description(title)

    logger.info("Creating badge: title={}, receiver={}, awarder={}".format(title, receiver.username, awarder.username))
    if desc:
        logger.info("desc.certification_circle={}".format(desc.certification_circle))

    if desc:
        if desc.certification_circle:
            if not account_management.is_account_in_circle(awarder, desc.certification_circle):
                raise P2k16UserException("The awarder {} is not a valid certifier".format(awarder.username))
    else:
        desc = BadgeDescription(title)
        db.session.add(desc)
        db.session.flush([desc])

    ab = AccountBadge(receiver, awarder, desc)
    db.session.add(ab)
    db.session.flush()

    event_management.save_event(BadgeAwardedEvent(ab, desc))

    return ab
