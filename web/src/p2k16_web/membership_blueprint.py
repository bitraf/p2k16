import json
import os
import stripe
from flask import Blueprint, jsonify, request
from p2k16.membership_management import parse_stripe_event

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
webhook_secret = os.environ.get('WEBHOOK_SECRET')

membership = Blueprint('membership', __name__, template_folder='templates')


@membership.route('/membership', methods=['GET'])
def test():
    return jsonify(dict({'key': 'Hello, World!'}))


@membership.route('/membership/stripe/webhook', methods=['POST'])
def webhooks():
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
        print("Error while decoding event!")
        return 'Bad payload', 400
    except stripe.error.SignatureVerificationError:
        print("Invalid signature!")
        return 'Bad signature', 400

    print(event)

    parse_stripe_event(event)

    return 'OK\n', 200
