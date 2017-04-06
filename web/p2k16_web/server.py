import sys
import logging
from logging import StreamHandler
import flask
from flask import Flask, g, request

_REQ_FMT = '%(name)s %(levelname)s %(path)s %(endpoint)s %(remote_addr)s %(message)s'
_DEFAULT_FMT = '%(name)s %(levelname)s %(message)s'


class CustomFormatter(logging.Formatter):
    def __init__(self):
        super(CustomFormatter).__init__()
        self.req_formatter = logging.Formatter(_REQ_FMT)
        self.default_format = logging.Formatter(_DEFAULT_FMT)

    def format(self, record):
        if flask.has_request_context():
            # record.uuid = g.uuid if hasattr(g, 'uuid') else None
            record.path = request.path
            record.endpoint = request.endpoint
            record.remote_addr = request.remote_addr

            return self.req_formatter.format(record)

        return self.default_format.format(record)


handler = StreamHandler(stream=sys.stdout)
handler.setFormatter(CustomFormatter())

from p2k16 import app
from p2k16 import auth, database, door

app.logger.addHandler(handler)

auth.login_manager.init_app(app)

door.init()

if app.config['P2K16_CREATE_DATABASE']:
    from p2k16 import default_data
    from p2k16.models import *

    app.logger.info("Creating database")
    database.db.create_all(app=app)
    app.logger.info("Database created")

    if len(User.query.all()) == 0:
        default_data.create()
