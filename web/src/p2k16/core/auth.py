import logging

import flask_login

from p2k16.core import account_management
from p2k16.core.models import Account

logger = logging.getLogger(__name__)

login_manager = flask_login.LoginManager()


class AuthenticatedAccount(flask_login.UserMixin):
    def __init__(self, account, circles):
        self.id = account.id
        self.account = account
        self.circles = circles


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
