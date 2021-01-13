import logging
from datetime import datetime, timedelta
from typing import Optional

import stripe
from p2k16.core import P2k16UserException, mail
from p2k16.core.models import db, Account, StripePayment, model_support, Membership, StripeCustomer, Company

logger = logging.getLogger(__name__)


def paid_members():
    return Account.query. \
        join(StripePayment, StripePayment.created_by_id == Account.id). \
        filter(StripePayment.end_date >= (datetime.utcnow() - timedelta(days=1))). \
        all()


# TODO: Deprecated
def active_member(account: Account = None) -> bool:
    """
    Verify that user is an active member of Bitraf either by paying or member of company
    """

    # Check paying membership
    if StripePayment.is_account_paying_member(account.id):
        return True

    # Check company membership
    if Company.is_account_employed(account.id):
        return True

    return False


def get_membership(account: Account):
    """
    Get membership info for account
    :param account:
    :return: Membership model
    """
    return Membership.query.filter(Membership.created_by_id == account.id).one_or_none()


def get_membership_fee(account: Account):
    """
    Get membership fee for account
    :param account:
    :return: Fee or None
    """
    membership = get_membership(account)
    if membership is None:
        return None
    else:
        return membership.fee


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
    elif event.type == 'checkout.session.completed':
        handle_session_completed(event)
    elif event.type == 'payment_method.attached':
        handle_payment_method_updated(event)
    elif event.type == 'payment_method.updated':
        handle_payment_method_updated(event)
    else:
        pass  # Not implemented on purpose


def handle_invoice_created(event):
    pass


def handle_invoice_updated(event):
    pass


def handle_payment_success(event):
    customer_id = event.data.object.customer
    account = find_account_from_stripe_customer(customer_id)

    with model_support.run_as(account):
        invoice_id = event.data.object.id
        timestamp = datetime.fromtimestamp(event.data.object.created)
        items = event.data.object.lines.data[0]

        payment = StripePayment(invoice_id, datetime.fromtimestamp(items.period.start),
                                datetime.fromtimestamp(items.period.end), items.amount / 100, timestamp)

        db.session.add(payment)
        db.session.commit()

def handle_payment_failed(event):
    pass


    """
    After user completes Stripe Checkout session.
    :return:
    """
def handle_session_completed(event):
    customer_id = event.data.object.customer

    account = Account.find_account_by_id(event.data.object.metadata.accountId)

    stripe_customer = get_stripe_customer(account)

    # Customer not registered with p2k16
    if stripe_customer is None:
        with model_support.run_as(account):
            stripe_customer = StripeCustomer(customer_id)
            db.session.add(stripe_customer)
            db.session.commit()

    mail.send_new_member(account)

    """
    Try to charge unpaid invoices if payment method updated
    This allows a member to openm doors/use tools right away
    instead of waiting for a smart retry (a few days)
    :return:
    """
def handle_payment_method_updated(event):
    stripe_customer_id = event.data.object.customer

    if stripe_customer_id is not None:
        invoices = stripe.Invoice.list(customer=stripe_customer_id, status='open')

        for invoice in invoices.data:
            stripe.Invoice.pay(invoice.id)


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
            cu = stripe.Customer.retrieve(stripe_customer_id.stripe_id, expand=['sources', 'subscriptions'])

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

def member_customer_portal(account: Account, base_url: str):
    """
    Access stripe customer portal
    :param account:
    :param base_url:
    :return: customer portalUrl
    """
    stripe_customer_id = get_stripe_customer(account)

    if stripe_customer_id is None:
        raise P2k16UserException('No billing information available. Create a subscription first.')

    return_url = base_url + '/#!/'

    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url)

        return {'portalUrl': session.url}

    except stripe.error.StripeError as e:
            logger.error("Stripe error: " + repr(e.json_body))

            raise P2k16UserException("Stripe error. Contact kasserer@bitraf.no if the "
                                 "problem persists.")

def member_create_checkout_session(account: Account, base_url: str, price_id: int):
    """
    Create a new subscription using Stripe Checkout / Billing
    :param account:
    :param base_url:
    :param price_id:
    :return: checkout sessionId
    """
    stripe_customer_id = get_stripe_customer(account)

    # Existing customers should only use this flow if they have no subscriptions.
    if stripe_customer_id is not None:
          # Get customer object
        cu = stripe.Customer.retrieve(stripe_customer_id.stripe_id, expand=[
               'subscriptions'])

        if len(cu.subscriptions.data) > 0:
            raise P2k16UserException("User is already subscribed.")

    else:
        # Create a new customer object
        stripe_customer_id = stripe.Customer.create(
            name=account.name,
            email=account.email
            )

        # Store stripe customer in case checkout fails.
        stripe_customer = StripeCustomer(stripe_customer_id.id)
        db.session.add(stripe_customer)
        db.session.commit()

    success_url = base_url + '/#!/?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = base_url + '/#!/'

    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=success_url,
            cancel_url=cancel_url,
            payment_method_types=["card"],
            mode="subscription",
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1
                }
            ],
            metadata={"accountId": account.id},
            customer=stripe_customer_id,
        )

        session_id = checkout_session['id']

        return {'sessionId': session_id}


    except stripe.error.StripeError as e:
            logger.error("Stripe error: " + repr(e.json_body))

            raise P2k16UserException("Stripe error. Contact kasserer@bitraf.no if the problem persists.")
