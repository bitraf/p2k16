from functools import wraps
from symtable import Function

import jsonschema as js
from flask import request, Blueprint
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


class DataServiceTool(object):
    class Route(object):
        def __init__(self, name, fun, url, **kwargs):
            self.name = name
            self.url = url
            self.function = fun
            self.kwargs = kwargs

            if "methods" in kwargs:
                methods = kwargs["methods"]
                assert len(methods) == 1
                self.method = methods[0]
            else:
                self.method = "GET"

    def __init__(self, name, jsName, blueprint: Blueprint):
        self.name = name
        self.jsName = jsName
        self.blueprint = blueprint
        self._routes = []  # List[Route]

    def route(self, url, **kwargs):
        """
        A special decorator that 1) registers the url so it can be iterated over later and 2) forwards to the blueprint's route method.

        These have the same effects in terms of routing:

        @core.route('/service/authz/log-in', methods=['POST'])
        def foo():
            ...

        @registering_route('/service/authz/log-in', methods=['POST'])
        def foo():
            ...

        :param blueprint:
        :param url:
        :param kwargs:
        :return:
        """

        def decorator(f: Function):
            self._routes.append(self.Route(f.__name__, f, url, **kwargs))
            x = self.blueprint.route(url, **kwargs)
            y = x(f)
            return y

        return decorator

    def generate(self, ):
        s = "'use strict';\n"
        s += "/**\n * @constructor\n */\n"
        s += "var {} = function ($http) {{\n".format(self.name)

        names = [r.name for r in self._routes]

        for r in self._routes:
            args = []

            has_payload = r.method == "POST"

            if has_payload:
                args.append("payload")

            s += "  function {}({}) {{\n".format(r.name, ", ".join(args))
            s += "    var req = {{}};\n".format()
            s += "    req.method = '{}';\n".format(r.method)
            s += "    req.url = '{}';\n".format(r.url)
            if has_payload:
                s += "    req.data = payload;\n".format(r.url)
            s += "    return $http(req);\n"
            s += "  }\n"
            s += "\n"

        s += "  /**\n   * @lends {}.prototype\n   */\n".format(self.name)
        s += "  return {\n    "
        s += ",\n    ".join(["{}: {}".format(n, n) for n in names]).strip()
        s += "\n  }\n"

        s += "}};\n".format()

        s += "\n"
        s += "{}.resolve = {{}};\n".format(self.name)
        for r in self._routes:
            s += "{}.resolve.{} = function(CoreDataService) {{\n".format(self.name, r.name)
            s += "  return CoreDataService.{}().then(function (res) {{ return res.data; }});\n".format(r.name)
            s += "}};\n".format()

        return s
