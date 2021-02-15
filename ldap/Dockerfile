FROM debian:buster

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    slapd \
    odbc-postgresql </dev/null

RUN mkdir /ldap
COPY setup.awk odbc.template.ini slapd.template.conf /ldap/
COPY entrypoint /
RUN chmod +x /entrypoint

CMD /entrypoint
