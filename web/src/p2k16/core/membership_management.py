import datetime
import stripe
from p2k16.core.models import Account, MembershipPayment, model_support, Membership, StripeCustomer
from p2k16.core.database import db
from p2k16.core import app, P2k16UserException


def paid_members():
    return Account.query. \
        join(MembershipPayment, MembershipPayment.created_by_id == Account.id). \
        filter(MembershipPayment.end_date >= datetime.datetime.utcnow()). \
        all()


def active_member(account: Account = None) -> bool:
    """
    Verify that user is an active member of Bitraf either by paying or some other mechanism
    """
    return MembershipPayment.query. \
               filter(MembershipPayment.created_by_id == account.id,
                      MembershipPayment.end_date >= datetime.datetime.utcnow()).scalar() is not None


def get_membership(account: Account):
    """
    Get membership info for account
    :param account:
    :return: Membership model
    """
    return Membership.query.filter(Membership.created_by_id == account.id).one_or_none()


def get_stripe_customer(account: Account):
    """
    Get stripe customer for account
    :param account:
    :return: StripeCustomer model
    """
    return StripeCustomer.query.filter(StripeCustomer.created_by_id == account.id).one_or_none()


def parse_stripe_event(event):
    print("Hi")
    repr(event)
    print("Received event: id={id}, type={type}".format(id=event.id, type=event.type))

    pass


def member_set_credit_card(account, stripe_token) -> bool:
    # Get mapping from account to stripe_id
    stripe_customer_id = get_stripe_customer(account)

    try:
        if stripe_customer_id is None:
            # Create a new stripe customer and set source
            cu = stripe.Customer.create(
                description="Customer for %r" % account.name,
                email=account.email,
                source=stripe_token
            )
            stripe_customer_id = StripeCustomer(cu.stripe_id)

            app.info("Created customer for user=%r" % account.username)
        else:
            # Get customer object
            cu = stripe.Customer.retrieve(stripe_customer_id.stripe_id)

            if cu is None or (hasattr(cu, 'deleted') and cu.deleted):
                app.logger.error("Stripe customer does not exist. This should not happen! account=%r, stripe_id=%r" %
                                 (account.username, stripe_token))
                raise P2k16UserException("Set credit card invalid state. Contact kasserer@bitraf.no")

            # Delete any old cards
            for card in cu.sources.list():
                card.delete()

            # Create a new default card
            card = cu.sources.create(source=stripe_token)
            cu.default_source = card.id
            cu.save()

        # Commit to db
        db.session.add(stripe_customer_id)
        db.session.commit()

        # Check if there is any outstanding invoices on this account that needs billing
        for invoice in stripe.Invoice.list(customer=cu.stripe_id):
            if invoice.paid is False:
                invoice.pay()

        app.logger.info("Successfully updated credit card for user=%r" % account.username)
        return True

    except stripe.error.CardError as e:
        err = e.json_body.get('error', {})
        msg = err.get('message')

        app.logger.info("Card processing failed for user=%r, error=%r" % (account.username, err))

        raise P2k16UserException("Error updating credit card: %r" % msg)

    except stripe.error.StripeError as e:
        app.logger.error("Stripe error: " + repr(e.json_body))

        raise P2k16UserException("Error updating credit card due to stripe error. Contact kasserer@bitraf.no if the "
                                 "problem persists.")
