import datetime
from p2k16.core.models import Account, MembershipPayment


def paid_members():
    return Account.query. \
        join(MembershipPayment, MembershipPayment.account_id == Account.id). \
        filter(MembershipPayment.end_date >= datetime.datetime.utcnow()). \
        all()


def active_member(account: Account = None) -> bool:
    """
    Verify that user is an active member of Bitraf either by paying or some other mechanism
    """
    return Account.query.join(MembershipPayment).filter(Account.id == account.id,
                                                        MembershipPayment.end_date >= datetime.datetime.utcnow()).scalar() is not None


def parse_stripe_event(event):
    print("Hi")
    repr(event)
    print("Received event: id={id}, type={type}".format(id=event.id, type=event.type))

    pass
