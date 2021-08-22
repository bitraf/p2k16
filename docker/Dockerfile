FROM debian:buster-slim

RUN apt-get update && apt-get install --no-install-recommends --yes \
    virtualenv git curl bash && \
    rm -rf /var/lib/apt/cache

RUN useradd --shell /bin/bash --home-dir /p2k16 p2k16 && mkdir /p2k16 /p2k16/bin && chown -R p2k16 /p2k16
WORKDIR /p2k16
SHELL ["/bin/bash", "-c"]
USER p2k16

RUN git clone --depth 1 --branch v0.38.0 https://github.com/nvm-sh/nvm.git nvm 2>/dev/null
ENV NVM_DIR="/p2k16/nvm"
ENV NODE_VERSION="v14.7.0"
COPY .nvmrc .
RUN . "$NVM_DIR/nvm.sh" --no-use && nvm install

RUN virtualenv -p python3 env

COPY requirements.txt .
RUN env/bin/pip install -r requirements.txt

COPY --chown=p2k16 web web
RUN env/bin/pip install --trusted-host github.com -e web

COPY bin/package.json \
    bin/package-lock.json \
    bin/npm-tool \
    bin/bower \
    bin/
RUN . "$NVM_DIR/nvm.sh" && cd web && ../bin/bower install

COPY infrastructure/gunicorn-config.py \
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
