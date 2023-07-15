import json
import logging
from io import BytesIO
from typing import Mapping

import flask
import stripe
from flask import Blueprint, jsonify, request

from p2k16.core.membership_management import parse_stripe_event
from p2k16.core.reports import stats_chart

logger = logging.getLogger(__name__)

webhook_secret = None


def setup_stripe(cfg: Mapping[str, str]) -> None:
    global webhook_secret
    stripe.api_key = cfg.get('STRIPE_SECRET_KEY')
    webhook_secret = cfg.get('STRIPE_WEBHOOK_SECRET', None)

    # The API version routinely contains breaking changes and must be kept in sync with code/library.
    stripe.api_version = '2022-11-15'


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


@membership.route('/stripe-stats.png', methods=['GET'])
def stripe_stats():
    from p2k16.core import models

    with models.db.engine.connect() as con:
        logger.info("Getting stripe payments")
        df = stats_chart.query(con)
        logger.info("Query done, creating picture")

        logger.info("data\n{}".format(df))

        fig = stats_chart.run(df)
        logger.info("Picture done")

        buf = BytesIO()
        fig.savefig(buf, format="png")

        response = flask.make_response(buf.getvalue())
        response.headers.set('Content-Type', 'image/png')
        return response, 200
