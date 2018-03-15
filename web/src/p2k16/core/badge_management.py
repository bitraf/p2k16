import logging
from typing import List, Optional

from p2k16.core import P2k16UserException, account_management
from p2k16.core.models import db, Account, AccountBadge, BadgeDescription

logger = logging.getLogger(__name__)


def _load_description(title: str) -> BadgeDescription:
    return BadgeDescription.query. \
        filter(BadgeDescription.title == title). \
        one_or_none()


def badges_for_account(account_id: int) -> List[AccountBadge]:
    return AccountBadge.query. \
        join(Account, Account.id == AccountBadge.account_id). \
        filter(Account.id == account_id)


def create_badge(receiver: Account, awarder: Optional[Account], title: str) -> AccountBadge:
    desc = _load_description(title)

    logger.info("create_badge")
    logger.info("desc={}".format(desc))
    if desc:
        logger.info("desc.certification_circle={}".format(desc.certification_circle))

    if desc:
        if desc.certification_circle:
            if not awarder:
                raise P2k16UserException("The badge {} needs to be certified".format(title))
            if not account_management.is_account_in_circle(awarder, desc.certification_circle):
                raise P2k16UserException("The awarder {} is not a valid certifier".format(awarder.username))
    else:
        desc = BadgeDescription(title)
        db.session.add(desc)
        db.session.flush([desc])

    ab = AccountBadge(receiver, awarder, desc)
    db.session.add(ab)

    return ab
