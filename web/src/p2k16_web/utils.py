from functools import wraps

import jsonschema as js
from flask import jsonify, request
from p2k16 import P2k16UserException


def validate_schema(schema):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kw):
            try:
                js.validate(request.json, schema)
                return f(*args, **kw)
            except js.ValidationError as e:
                raise P2k16UserException(e.message)

        return wrapper

    return decorator
