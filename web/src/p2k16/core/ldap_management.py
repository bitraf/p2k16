import logging
from typing import Mapping, Optional, Tuple, Dict, Any, List

import ldap
import ldap.dn
import ldap.filter
import ldap.modlist
from ldap.ldapobject import LDAPObject

from p2k16.queue import Message, sqlalchemy_queue
from .models import db, Account

logger = logging.getLogger(__name__)

ldap_uri = None  # type: Optional[str]
ldap_base = None  # type: Optional[List[List[Tuple[str, str, int]]]]
ldap_base_str = None  # type: Optional[str]
ldap_bind_dn = None  # type: Optional[str]
ldap_bind_password = None  # type: Optional[str]


def account_to_dn(a: Account) -> str:
    dn = [[('uid', a.username, 1)], [('ou', 'People', 1)]] + ldap_base
    return ldap.dn.dn2str(dn)


def account_to_entry(a: Account) -> Optional[Dict[str, Any]]:
    object_class = ["top", "inetOrgPerson"]

    d = {
        "objectClass": object_class,
    }

    parts = a.name.split() if a.name is not None else []

    if len(parts) < 1:
        # bad name
        return None

    d["cn"] = [a.name]
    d["sn"] = [parts[-1]]
    if a.email:
        d["mail"] = [a.email]

    # posixAccount: http://ldapwiki.com/wiki/PosixAccount
    object_class.append("posixAccount")
    d["uid"] = [a.username]
    d["uidNumber"] = ["1000"]
    d["gidNumber"] = ["1000"]
    d["homeDirectory"] = ["/home/{}".format(a.username)]
    if a.password is not None:
        d["userPassword"] = [a.password]
    d["gecos"] = [str(a.name).replace("æ", "a").replace("ø", "o").replace("å", "a")]

    return d


def sync_required(account: Account):
    sqlalchemy_queue.insert(db.session, 'ldap-sync', account.id)


def on_ldap_sync(message: Message):
    account = Account.find_account_by_id(message.entity_id)
    update_account(account)


def update_account(account: Account):
    logger.info(f"Updating Account record for {account.username}")

    dn = account_to_dn(account)
    if dn is None:
        logger.warning(f"Could not create DN from account: {account.username}")
        return

    entry = account_to_entry(account)
    if entry is None:
        logger.warning(f"Could not make LDAP entry from account: {account.username}")
        return

    # fuck up all values
    byte_entry = {}
    for key, value in entry.items():
        byte_entry[key] = [s.encode('utf-8') for s in value]
    logger.info(f"byte_entry={byte_entry}")

    con = ldap.initialize(ldap_uri)  # type: LDAPObject
    try:
        if ldap_bind_dn is not None:
            ret = con.simple_bind_s(ldap_bind_dn, ldap_bind_password)
            logger.info(f"bind ret={ret}")

        try:
            res = con.read_s(dn)
            logger.info(f"search={res}")
        except ldap.NO_SUCH_OBJECT:
            res = None

        if res is None:
            logger.info("Adding new entry")
            res = con.add_s(dn, ldap.modlist.addModlist(byte_entry))
        else:
            logger.info("Updating existing entry")
            modifications = ldap.modlist.modifyModlist(res, byte_entry)
            logger.warning(f"modifications: {modifications}")

            res = con.modify_s(dn, modifications)

        logger.warning(f"change result: {res}")
    finally:
        # noinspection PyBroadException
        try:
            con.unbind_s()
        except Exception:
            pass


def initialized() -> bool:
    return ldap_uri is not None


def setup(cfg: Mapping[str, str]):
    global ldap_uri, ldap_base, ldap_base_str
    ldap_uri = cfg.get('LDAP_URI', None)

    ldap_base_str = cfg.get('LDAP_BASE', None)
    if ldap_base_str is not None:
        ldap_base = ldap.dn.str2dn(ldap_base_str)
        logger.info(f"LDAP BASE={ldap_base_str}")

    global ldap_bind_dn, ldap_bind_password
    ldap_bind_dn = cfg.get('LDAP_BIND_DN', None)
    ldap_bind_password = cfg.get('LDAP_BIND_PASSWORD', None)
