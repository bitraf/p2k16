from functools import wraps

import jsonschema as js
from flask import jsonify, request


def validate_schema(schema):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kw):
            try:
                js.validate(request.json, schema)
                return f(*args, **kw)
            except js.ValidationError as e:
                return jsonify({"messages": e.message}), 400

        return wrapper

    return decorator
