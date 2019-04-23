import logging
import os.path

import emails.loader
from jinja2 import Template, Environment
from jinja2.loaders import PackageLoader
from p2k16.core.models import Account

logger = logging.getLogger(__name__)

mail_from = ('Bitraf', 'root@bitraf.no')
membership_cc = 'post@bitraf.no'


class Templates():
    def __init__(self):
        self.basedir = os.path.dirname(__file__)
        env = Environment()
        loader = PackageLoader(__name__, package_path="")

        self.send_password_recovery_t = loader.load(env, "send_password_recovery.html")  # type: Template
        self.new_member_t = loader.load(env, "new_member.html")  # type: Template
        self.membership_ended_t = loader.load(env, "membership_ended.html")  # type: Template

    def send_password_recovery(self, **kwargs):
        html = self.send_password_recovery_t.render(**kwargs)
        return emails.html(subject="Reset password for Bitraf", html=html)

    def new_member(self, **kwargs):
        html = self.new_member_t.render(**kwargs)
        return emails.html(subject="Welcome to Bitraf", html=html)

    def membership_ended(self, **kwargs):
        html = self.membership_ended_t.render(**kwargs)
        return emails.html(subject="Bitraf membership ended", html=html)


_templates = Templates()


def get_templates() -> Templates:
    if not hasattr(get_templates, 'templates'):
        get_templates.templates = Templates()

    return get_templates.templates


def send_password_recovery(account: Account, reset_url: str):
    # message = emails.html(subject=T("Reset password for Bitraf"),
    #                       html=T("<p>Someone (hopefully you) have requested to reset the password for your Bitraf "
    #                              "account ({{ account.username }}). If you want do change your password go here:</p>"
    #                              "<p>{{ url }}</p>"
    #                              "<p>If you don't want to change your password you can ignore this email.</p>"),
    #                       mail_from=mail_from)

    logger.info("Sending password recovery email to {}".format(account.email))

    m = _templates.send_password_recovery(url=reset_url, account=account)
    m.mail_to = (account.username, account.email)
    m.mail_from = mail_from
    m.send()

def send_new_member(account: Account):
    logger.info("Sending new member email to {}".format(account.email))

    m = _templates.new_member(account=account)
    m.mail_to = (account.username, account.email)
    m.mail_from = mail_from
    m.bcc = membership_cc
    m.send()

def send_membership_ended(account: Account):
    logger.info("Sending membership ended email to {}".format(account.email))

    m = _templates.membership_ended(account=account)
    m.mail_to = (account.username, account.email)
    m.mail_from = mail_from
    m.bcc = membership_cc
    m.send()

