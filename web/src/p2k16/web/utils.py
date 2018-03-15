import os
import re
from functools import wraps
from symtable import Function

import flask
import jsonschema as js
from p2k16.core import P2k16UserException


def validate_schema(schema):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kw):
            try:
                js.validate(flask.request.json, schema)
                return f(*args, **kw)
            except js.ValidationError as e:
                raise P2k16UserException(e.message)

        return wrapper

    return decorator


class ResourcesTool(object):
    class Dir(object):
        def __init__(self, name):
            self.name = name
            self.dirs = []
            self.files = []
            pass

    class File(object):
        def __init__(self, name):
            self.name = name

    @staticmethod
    def scan(path, dir: Dir):
        # print("scanning {}, dir={}".format(path, dir.name))
        # This is a python3.6 ism
        # with os.scandir(path) as it:
        # but we run py3.5 in prod..
        it = os.scandir(path)
        if True:
            for entry in it:
                if entry.name.startswith("."):
                    continue
                if entry.name == "bower_components":
                    continue

                if entry.is_file():
                    # print("file: {}".format(entry.name))
                    dir.files.append(entry.name)
                if entry.is_dir():
                    p = os.path.join(path, entry.path)
                    # print("dir: {}".format(p))
                    d = ResourcesTool.Dir(entry.name)
                    dir.dirs.append(d)
                    ResourcesTool.scan(p, d)

                dir.dirs.sort(key=lambda d: d.name)
                dir.files.sort()

    @staticmethod
    def generate(file, depth: int, prefix: str, dir: Dir, path: str):
        # print("// depth={}, prefix={}, dir.name={}, path={}".format(depth, prefix, dir.name, path))

        for f in dir.files:
            # print("// {}{}".format(" " * depth, f))
            filename = "{}{}".format(path, f)
            # print("// filename={}".format(filename))
            url = flask.url_for("static", filename=filename)
            symbol = f.replace("-", "_").replace(".", "_")
            file.write("{}.{} = \"{}\";\n".format(prefix, symbol, url))

        for d in dir.dirs:
            if len(d.files) == 0:
                continue

            child_prefix = "{}.{}".format(prefix, d.name)
            file.write("{} = {{}};\n".format(child_prefix))
            ResourcesTool.generate(file, depth + 1, child_prefix, d, "{}{}/".format(path, d.name))

        return len(dir.files)

    @staticmethod
    def run(path: str, file):
        root = ResourcesTool.Dir("")
        ResourcesTool.scan(path, root)
        file.write("var p2k16_resources = {};\n")
        ResourcesTool.generate(file, 0, "p2k16_resources", root, "")


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

    def __init__(self, name, jsName, blueprint: flask.Blueprint):
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
        s += "function {}($http) {{\n".format(self.name)
        s += "  this.$http = $http;\n"
        # s += "  console.log('{}', this);\n".format(self.name)
        s += "  return this;\n"
        s += "}\n"
        s += "\n"

        names = [r.name for r in self._routes]

        resolvers = []

        for r in self._routes:
            args = []
            url_parts = []

            matches = list(DataServiceTool.segments_re.finditer(r.url))
            if len(matches):
                # print("len(matches)={}, str={}".format(len(matches), r.url))
                # i = 0
                url = ""
                for m in matches:
                    g = m.groups()
                    if g[3]:
                        url_parts.append((None, g[3]))
                    else:
                        url_parts.append((g[2], None))
                        args.append(g[2])

                # print("url={}".format(url))
            else:
                raise Exception("Hm..")

            has_payload = r.method != "GET" and r.method != "HEAD"

            # print("url_parts={}".format(url_parts))

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
            # print("url_parts={}".format(up))

            middle = '='
            f_args = args + ['payload'] if has_payload else args
            s += "{}.prototype.{} = function ({}) {{\n".format(self.name, r.name, ", ".join(f_args))
            # s += "    console.log('{}: this', this);\n".format(r.name)
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
            s += "    return this.$http(req);\n"
            s += "};\n"

            if not has_payload:
                # resolvers.append(r.name)
                r_args = [self.name]
                if len(args):
                    r_args.append("$route")

                r_s = "function ({}) {{\n".format(", ".join(r_args))
                for a in args:
                    r_s += "  var {} = $route.current.params.{};\n".format(a, a)

                r_s += "  return {}.{}({}).then(function (res) {{ return res.data; }});\n". \
                    format(self.name, r.name, ", ".join(args))
                r_s += "};\n"
                resolvers.append((r.name, r_s))

            s += "\n"

        s += "var {}Resolvers = {{}};\n".format(self.name)
        for (name, fun) in resolvers:
            s += "{}Resolvers.{} = ".format(self.name, name) + fun

        return s
