from datetime import datetime
import os
import stripe
from p2k16.core.models import Account, MembershipPayment, model_support, Membership, StripeCustomer
from p2k16.core.database import db
from p2k16.core import app, P2k16UserException


def paid_members():
    return Account.query. \
        join(MembershipPayment, MembershipPayment.created_by_id == Account.id). \
        filter(MembershipPayment.end_date >= datetime.now()). \
        all()


def active_member(account: Account = None) -> bool:
    """
    Verify that user is an active member of Bitraf either by paying or some other mechanism
    """
    return MembershipPayment.query. \
               filter(MembershipPayment.created_by_id == account.id,
                      MembershipPayment.end_date >= datetime.now()).scalar() is not None


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

def member_get_details(account):
    # Get mapping from account to stripe_id
    stripe_customer_id = get_stripe_customer(account)

    details = {}

    details['stripe_pubkey'] = os.environ.get('STRIPE_PUBLIC_KEY')

    try:
        # Get payment details
        details['card'] = "N / A"
        details['card_exp'] = ""
        details['stripe_price'] = "0"
        details['stripe_subscription_status'] = "none"

        if stripe_customer_id is not None:
            # Get customer object
            cu = stripe.Customer.retrieve(stripe_customer_id.stripe_id)

            if len(cu.sources.data) > 0:
                card = cu.sources.data[0]
                details['card'] = "**** **** **** " + card.last4
                details['card_exp'] = "%r/%r" % (card.exp_month, card.exp_year)

            # Get stripe subscription to make sure it matches local database
            assert len(cu.subscriptions.data) <= 1
            for sub in cu.subscriptions.data:
                details['stripe_subscription_status'] = sub.status
                details['stripe_price'] = sub.plan.amount / 100

        # Get current membership
        membership = get_membership(account)
        if membership is not None:
            details['fee'] = membership.fee
            details['first_membership'] = membership.first_membership
            details['start_membership'] = membership.start_membership
        else:
            details['fee'] = 0

        # TODO: Add payments

    except stripe.error.StripeError as e:
        raise P2k16UserException("Error reading data from Stripe. Contact kasserer@bitraf.no if the problem persists.")

    return details

def member_set_credit_card(account, stripe_token):
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

        # Check if there are any outstanding invoices on this account that needs billing
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


def member_set_membership(account, membership_plan, membership_price):

    # TODO: Remove membership_price and look up price from model

    try:
        membership = get_membership(account)

        # --- Update membership in local db ---
        if membership is not None:
            if membership.fee is membership_price:
                # Nothing's changed.
                app.logger.info("No membership change for user=%r, type=%r, amount=%r" % (account.username, membership_plan, membership_price))
                return
            else:
                membership.fee = membership_price
                membership.start_membership = datetime.now()
        else:
            # New membership
            membership = Membership(membership_price)

        # --- Update membership in stripe ---

        # Get customer object
        stripe_customer_id = get_stripe_customer(account)

        # Remove existing subscriptions
        for sub in stripe.Subscription.list(customer=stripe_customer_id):
            sub.delete(at_period_end=False)

        stripe.Subscription.create(customer=stripe_customer_id, items=[{"plan": membership_plan}])

        # Commit to db
        db.session.add(membership)
        db.session.commit()

        app.logger.info("Successfully updated membership type for user=%r, type=%r, amount=%r" % (account.username, membership_plan, membership_price))
        return True

    except stripe.error.CardError as e:
        err = e.json_body.get('error', {})
        msg = err.get('message')

        app.logger.info("Card processing failed for user=%r, error=%r" % (account.username, err))

        raise P2k16UserException("Error charging credit card: %r" % msg)

    except stripe.error.StripeError as e:
        app.logger.error("Stripe error: " + repr(e.json_body))

        raise P2k16UserException("Stripe error. Contact kasserer@bitraf.no if the problem persists.")
