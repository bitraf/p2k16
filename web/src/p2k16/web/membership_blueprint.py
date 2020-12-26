import json
import logging
from typing import Mapping

import stripe
from flask import Blueprint, jsonify, request
from p2k16.core.membership_management import parse_stripe_event

logger = logging.getLogger(__name__)

webhook_secret = None


def setup_stripe(cfg: Mapping[str, str]) -> None:
    global webhook_secret
    stripe.api_key = cfg.get('STRIPE_SECRET_KEY')
    webhook_secret = cfg.get('STRIPE_WEBHOOK_SECRET', None)

    # The API version routinely contains breaking changes and must be kept in sync with code/library.
    stripe.api_version = '2020-08-27'


membership = Blueprint('membership', __name__, template_folder='templates')


@membership.route('/membership', methods=['GET'])
def test():
    return jsonify(dict({'key': 'Hello, World!'}))


@membership.route('/membership/stripe/webhook', methods=['POST'])
def webhook():

    if webhook_secret is None:
        return "Stripe not enabled", 400

    payload = request.data.decode('utf-8')
    received_sig = request.headers.get('Stripe-Signature', None)

    try:
        # In the stripe test api, we set the secret to test to disable the signature check
        if webhook_secret != 'test':
            event = stripe.Webhook.construct_event(
                payload, received_sig, webhook_secret)
        else:
            data = json.loads(payload)
            event = stripe.Event.construct_from(data, stripe.api_key)

    except ValueError:
        logger.warning("Error while decoding event!")
        return 'Bad payload', 400
    except stripe.error.SignatureVerificationError:
        logger.warning("Invalid signature!")
        return 'Bad signature', 400

    parse_stripe_event(event)

    return 'OK\n', 200
