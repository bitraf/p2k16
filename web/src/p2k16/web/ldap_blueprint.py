import io

from flask import Blueprint
from ldap3 import LDIF, Connection

from p2k16.core import ldap_management
from p2k16.core.models import Account

ldap = Blueprint("ldap", __name__, template_folder="templates")


@ldap.route('/ldap/users.ldif')
def core_ldif():
    f = io.BytesIO()
    con = Connection(server=None, client_strategy=LDIF)  # no need of real LDAP server

    con.open()
    for a in Account.all_user_accounts():
        dn = ldap_management.account_to_dn(a)

        if dn is None:
            continue

        con.delete(dn)

        d = ldap_management.account_to_entry(a)
        if d is not None:
            con.add(dn, d)

    s = f.getvalue()
    print(str(s))
    return s
