FROM debian:buster-slim

RUN mkdir /p2k16
WORKDIR /p2k16

RUN apt-get update && apt-get install --no-install-recommends --yes \
    python3 virtualenv npm && \
    rm -rf /var/lib/apt/cache

RUN virtualenv -p python3 env

ADD requirements.txt .
RUN env/bin/pip install -r requirements.txt

ADD web web
RUN env/bin/pip install --trusted-host github.com -e web

ADD infrastructure/gunicorn-config.py \
    infrastructure/config-default.cfg \
    infrastructure/config-local.cfg \
    infrastructure/logging-stdout.yaml \
    infrastructure/

ENV FLASK_DEBUG=1 \
    P2K16_CONFIG=infrastructure/config-local.cfg \
    P2K16_LOGGING=infrastructure/logging-stdout.yaml

# Use the Stripe non-prod API
ENV STRIPE_WEBHOOK_SECRET='whsec_Rr4aEG6kaZWIljjybZxqibta4Yjkakna' \
    STRIPE_SECRET_KEY='sk_test_JgaPEgWXlT6VkmLcz0bcIkOf' \
    STRIPE_PUBLIC_KEY='pk_test_hUoh3MEu4Oa8RjVFwZrFge4b'

# Dockerfile
CMD env/bin/gunicorn \
    --config "infrastructure/gunicorn-config.py" \
    --reload \
    p2k16.web.server:app
