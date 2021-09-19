import logging
from typing import Mapping, Optional, Tuple, Dict, Any

import ldap3
from ldap3.core.connection import Server, Connection
from ldap3.utils import dn, uri, conv

from p2k16.queue import Message, sqlalchemy_queue
from . import P2k16TechnicalException
from .models import db, Account

logger = logging.getLogger(__name__)

server = None  # type: Optional[Server]
ldap_uri = None  # type: Optional[str]
ldap_base = None  # type: Optional[str]
ldap_bind_dn = None  # type: Optional[str]
ldap_bind_password = None  # type: Optional[str]


def account_to_dn(a: Account) -> str:
    return dn.parse_dn(f"uid={dn.escape_rdn(a.username)},ou=People," + ldap_base)


# (error, objectClass, entry)
def account_to_entry(a: Account) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
    structural_object_class = "inetOrgPerson"
    object_class = ["top", structural_object_class]

    d = {
        "objectClass": object_class,
    }

    parts = a.name.split() if a.name is not None else []

    if len(parts) < 1:
        # bad name
        return "bad name", None, None

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

    return None, structural_object_class, d


def sync_required(account: Account):
    sqlalchemy_queue.insert(db.session, 'ldap-sync', account.id)


def on_ldap_sync(message: Message):
    account = Account.find_account_by_id(message.entity_id)
    update_account(account)


def update_account(account: Account):
    logger.info(f"Updating Account record for {account.username}")

    dn_ = account_to_dn(account)
    if dn_ is None:
        logger.warning(f"Could not create DN from account: {account.username}")
        return

    err, object_class, entry = account_to_entry(account)
    if err is not None:
        logger.warning(f"Could not make LDAP entry from account. username={account.username}: {err}")
        return

    with Connection(server=server, user=ldap_bind_dn, password=ldap_bind_password) as con:
        dn_str = ",".join([f"{a}={v}" for a, v, _ in dn_], )
        search_filter = f"(objectClass=*)"
        found = con.search(dn_str, search_filter, attributes=ldap3.ALL_ATTRIBUTES)

        if not found:
            logger.info("Adding new entry")
            if not con.add(dn_str, object_class, entry):
                raise P2k16TechnicalException(f"Could not add LDAP entry: {con.last_error}")
        else:
            old_entry = con.entries[0]
            logger.info("Updating existing entry")
            to_remove = {e: [(ldap3.MODIFY_REPLACE, [])] for e in old_entry.entry_attributes if e not in entry.keys()}
            to_update = {}
            for key, value in entry.items():
                v = value if isinstance(value, list) else [value]
                to_update[key] = [(ldap3.MODIFY_REPLACE, v)]

            modifications = {**to_remove, **to_update}
            logger.warning(f"modifications: {modifications}")

            if not con.modify(dn_str, modifications):
                raise P2k16TechnicalException(f"Could not modify LDAP entry: {con.last_error}")


def initialized() -> bool:
    return ldap_uri is not None


def setup(cfg: Mapping[str, str]):
    global ldap_uri, ldap_base
    ldap_uri = cfg.get('LDAP_URI', None)

    ldap_base = cfg.get('LDAP_BASE', None)
    logger.info(f"LDAP BASE={ldap_base}")

    global ldap_bind_dn, ldap_bind_password
    ldap_bind_dn = cfg.get('LDAP_BIND_DN', None)
    ldap_bind_password = cfg.get('LDAP_BIND_PASSWORD', None)

    uri_ = uri.parse_uri(ldap_uri)

    global server
    server = Server(host=uri_['host'], port=uri_['port'], use_ssl=uri_['ssl'])
