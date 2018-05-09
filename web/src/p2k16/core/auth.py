import logging
from typing import List

import flask_login
import flask_login.signals
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

    logger.info("login_manager.user_loader: Loaded account.id={}, account.username={}".
                format(account.id, account.username))

    circles = account_management.get_circles_for_account(account.id)

    return AuthenticatedAccount(account, circles)


def debug_signals(app):
    signals = [flask_login.signals.user_logged_in, flask_login.signals.user_logged_out,
               flask_login.signals.user_loaded_from_cookie, flask_login.signals.user_loaded_from_header,
               flask_login.signals.user_loaded_from_request, flask_login.signals.user_login_confirmed,
               flask_login.signals.user_unauthorized, flask_login.signals.user_needs_refresh,
               flask_login.signals.user_accessed, flask_login.signals.session_protected]
    for s in signals:
        name = s.name

        def dbg(name):
            return lambda *args, **kwargs: logger.info("name={}, args={}, kwargs={}".format(name, args, kwargs))

        s.connect(dbg(name), weak=False)
