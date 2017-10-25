import re
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

    # path_re = re.compile("(<([^:]+)+:([^>]+)>)")
    segments_re = re.compile("(/<([^:]+)+:([^>]+)>)|(/[^/]*)")

    def generate(self, ):
        s = "'use strict';\n"
        s += "/**\n * @constructor\n */\n"
        s += "var {} = function ($http) {{\n".format(self.name)
        s += "\n"

        names = [r.name for r in self._routes]

        resolvers = []

        for r in self._routes:
            args = []
            url_parts = []

            matches = list(DataServiceTool.segments_re.finditer(r.url))
            if len(matches):
                print("len(matches)={}, str={}".format(len(matches), r.url))
                # i = 0
                url = ""
                for m in matches:
                    g = m.groups()
                    if g[3]:
                        url_parts.append((None, g[3]))
                    else:
                        url_parts.append((g[2], None))
                        args.append(g[2])

                print("url={}".format(url))
            else:
                raise Exception("Hm..")

            has_payload = r.method == "POST"

            print("url_parts={}".format(url_parts))

            up = []
            tmp = None
            for p in url_parts:
                if p[1]:
                    if tmp:
                        tmp += p[1]
                    else:
                        tmp = p[1]
                else:
                    if tmp:
                        up.append((None, tmp))
                        tmp = None

                    up.append(p)
            if tmp:
                up.append((None, tmp))
            print("url_parts={}".format(up))

            middle = '='
            f_args = ['payload'] + args if has_payload else args
            s += "  function {}({}) {{\n".format(r.name, ", ".join(f_args))
            s += "    var req = {{}};\n".format()
            s += "    req.method = '{}';\n".format(r.method)

            for p in up:
                if p[1]:
                    s += "    req.url {} '{}';\n".format(middle, p[1])
                else:
                    s += "    req.url {} '/' + {};\n".format(middle, p[0])
                middle = '+='

            if has_payload:
                s += "    req.data = payload;\n".format(r.url)
            s += "    return $http(req);\n"
            s += "  }\n"

            if not has_payload:
                # resolvers.append(r.name)
                r_args = ["CoreDataService"]
                if len(args):
                    r_args.append("$route")

                r_s = "function ({}) {{\n".format(", ".join(r_args))
                for a in args:
                    r_s += "  var {} = $route.current.params.{};\n".format(a, a)

                r_s += "  return CoreDataService.{}({}).then(function (res) {{ return res.data; }});\n".format(r.name, ", ".join(args))
                r_s += "};\n"
                resolvers.append((r.name, r_s))

            s += "\n"

        s += "\n"
        s += "  /**\n   * @lends {}.prototype\n   */\n".format(self.name)
        s += "  return {\n"
        s += "    " + ",\n".join(["    {}: {}".format(n, n) for n in names]).strip()
        s += "\n  };\n"

        s += "}};\n".format()

        s += "\n"
        s += "var CoreDataServiceResolvers = {};\n"
        for (name, fun) in resolvers:
            s += "CoreDataServiceResolvers.{} = ".format(name) + fun

        return s
