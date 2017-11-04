import sys

import flask
import logging
from flask import request
from logging import StreamHandler

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

from p2k16.core import app
from p2k16.core import auth, door

app.logger.addHandler(handler)

auth.login_manager.init_app(app)

door.init()
