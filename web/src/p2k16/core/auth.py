import logging
from typing import List

import flask_login
from p2k16.core import account_management
from p2k16.core.models import Account, Circle

logger = logging.getLogger(__name__)

login_manager = flask_login.LoginManager()


class AuthenticatedAccount(flask_login.UserMixin):
    def __init__(self, account: Account, circles: List[Circle]):
        self.id = account.id
        self.account = account
        self.circles = circles

    def is_in_circle(self, circle_name: str):
        return next((True for c in self.circles if c.name == circle_name), False)


@login_manager.user_loader
def account_loader(account_id):
    logger.info("login_manager.user_loader: Loading account_id={}".format(account_id))

    account = Account.find_account_by_id(account_id)

    if account is None:
        logger.info("login_manager.user_loader: no such account".format(account_id))
        return

    logger.info("login_manager.user_loader: Loaded account.id={}, account.username={}".format(account.id, account.username))

    circles = account_management.get_circles_for_account(account.id)

    return AuthenticatedAccount(account, circles)
