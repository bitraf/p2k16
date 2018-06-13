import logging
from datetime import datetime, timedelta
from sqlalchemy import text, func
from typing import Mapping, Optional

import stripe
from p2k16.core import P2k16UserException
from p2k16.core.models import db, Account, StripePayment, model_support, Membership, StripeCustomer

logger = logging.getLogger(__name__)


def paid_members():
    return Account.query. \
        join(StripePayment, StripePayment.created_by_id == Account.id). \
        filter(StripePayment.end_date >= (datetime.utcnow() - timedelta(days=1))). \
        all()


def active_member(account: Account = None) -> bool:
    """
    Verify that user is an active member of Bitraf either by paying or some other mechanism
    """
    return StripePayment.query. \
        filter(StripePayment.created_by_id == account.id,
               StripePayment.end_date >= (datetime.utcnow() - timedelta(days=1))).count() is not 0


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


def get_membership_payments(account: Account):
    return StripePayment.query.filter(StripePayment.created_by_id == account.id).all()


def find_account_from_stripe_customer(stripe_customer_id) -> Optional[Account]:
    """
    Get account from stripe customer
    :param stripe_customer_id:
    :return: account
    """
    sc = StripeCustomer.query.filter(StripeCustomer.stripe_id == stripe_customer_id).one_or_none()

    return Account.find_account_by_id(sc.created_by_id) if sc is not None else None


def parse_stripe_event(event):
    logger.info("Received stripe event: id={id}, type={type}".format(id=event.id, type=event.type))

    if event.type == 'invoice.created':
        handle_invoice_created(event)
    elif event.type == 'invoice.updated':
        handle_invoice_updated(event)
    elif event.type == 'invoice.payment_succeeded':
        handle_payment_success(event)
    elif event.type == 'invoice.payment_failed':
        handle_payment_failed(event)
    else:
        pass # Not implemented on purpose


def handle_invoice_created(event):
    pass


def handle_invoice_updated(event):
    pass


def handle_payment_success(event):
    customer_id = event.data.object.customer
    account = find_account_from_stripe_customer(customer_id)

    with model_support.run_as(account):
        invoice_id = event.data.object.id
        timestamp = datetime.fromtimestamp(event.data.object.date)
        items = event.data.object.lines.data[0]

        payment = StripePayment(invoice_id, datetime.fromtimestamp(items.period.start),
                                datetime.fromtimestamp(items.period.end), items.amount / 100, timestamp)

        db.session.add(payment)
        db.session.commit()


def handle_payment_failed(event):
    pass


def member_get_details(account):
    # Get mapping from account to stripe_id
    stripe_customer_id = get_stripe_customer(account)

    details = {}

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

        # Export payments
        payments = []
        for pay in get_membership_payments(account):
            payments.append({
                'id': pay.id,
                'start_date': pay.start_date,
                'end_date': pay.end_date,
                'amount': float(pay.amount),
                'payment_date': pay.payment_date
            })

        details['payments'] = payments

    except stripe.error.StripeError:
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

            logger.info("Created customer for user=%r" % account.username)
        else:
            # Get customer object
            cu = stripe.Customer.retrieve(stripe_customer_id.stripe_id)

            if cu is None or (hasattr(cu, 'deleted') and cu.deleted):
                logger.error("Stripe customer does not exist. This should not happen! account=%r, stripe_id=%r" %
                             (account.username, stripe_token))
                raise P2k16UserException("Set credit card invalid state. Contact kasserer@bitraf.no")

            # Create a new default card
            new_card = cu.sources.create(source=stripe_token)
            cu.default_source = new_card.id
            cu.save()

            # Delete any old cards
            for card in cu.sources.list():
                if card.id != new_card.id:
                    card.delete()

        # Commit to db
        db.session.add(stripe_customer_id)
        db.session.commit()

        # Check if there are any outstanding invoices on this account that needs billing
        for invoice in stripe.Invoice.list(customer=cu.stripe_id):
            if invoice.paid is False:
                invoice.pay()

        logger.info("Successfully updated credit card for user=%r" % account.username)
        return True

    except stripe.error.CardError as e:
        err = e.json_body.get('error', {})
        msg = err.get('message')

        logger.info("Card processing failed for user=%r, error=%r" % (account.username, err))

        raise P2k16UserException("Error updating credit card: %r" % msg)

    except stripe.error.StripeError as e:
        logger.error("Stripe error: " + repr(e.json_body))

        raise P2k16UserException("Error updating credit card due to stripe error. Contact kasserer@bitraf.no if the "
                                 "problem persists.")


def member_cancel_membership(account):
    try:
        # Update local db
        membership = get_membership(account)
        db.session.delete(membership)

        # Update stripe
        stripe_customer_id = get_stripe_customer(account)

        for sub in stripe.Subscription.list(customer=stripe_customer_id):
            sub.delete(at_period_end=True)

        db.session.commit()

    except stripe.error.StripeError as e:
        logger.error("Stripe error: " + repr(e.json_body))

        raise P2k16UserException("Stripe error. Contact kasserer@bitraf.no if the problem persists.")


def member_set_membership(account, membership_plan, membership_price):
    # TODO: Remove membership_price and look up price from model

    try:
        membership = get_membership(account)

        if membership_plan == 'none':
            member_cancel_membership(account)
            return True

        # --- Update membership in local db ---
        if membership is not None:
            if membership.fee is membership_price:
                # Nothing's changed.
                logger.info("No membership change for user=%r, type=%r, amount=%r" % (
                    account.username, membership_plan, membership_price))
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

        if stripe_customer_id is None:
            raise P2k16UserException("You must set a credit card before changing plan.")

        # Check for active subscription
        subscriptions = stripe.Subscription.list(customer=stripe_customer_id)

        if subscriptions is None or len(subscriptions) == 0:
            sub = stripe.Subscription.create(customer=stripe_customer_id, items=[{"plan": membership_plan}])
        else:
            sub = next(iter(subscriptions), None)
            stripe.Subscription.modify(sub.id, cancel_at_period_end=False,
                                       items=[{
                                           'id': sub['items']['data'][0].id,
                                           'plan': membership_plan
                                       }])

        # Commit to db
        db.session.add(membership)
        db.session.commit()

        logger.info("Successfully updated membership type for user=%r, type=%r, amount=%r" % (
            account.username, membership_plan, membership_price))
        return True

    except stripe.error.CardError as e:
        err = e.json_body.get('error', {})
        msg = err.get('message')

        logger.info("Card processing failed for user=%r, error=%r" % (account.username, err))

        raise P2k16UserException("Error charging credit card: %r" % msg)

    except stripe.error.StripeError as e:
        logger.error("Stripe error: " + repr(e.json_body))

        raise P2k16UserException("Stripe error. Contact kasserer@bitraf.no if the problem persists.")
