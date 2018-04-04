# TODO: Do not put any p2k16.* imports here!
import logging
from typing import Dict


class P2k16LoggingFilter(logging.Filter):
    _data = {}  # type: Dict[str, str]

    def filter(self, record):
        # Just to make sure that these are always set.
        record.p2k16ReqId = ""
        record.p2k16Username = ""
        record.p2k16HttpReq = ""

        data = P2k16LoggingFilter._data

        if data:
            username = P2k16LoggingFilter._data.get("username", None)
            if username:
                record.p2k16Username = " [{}]".format(username)

            method = P2k16LoggingFilter._data.get("method", None)
            path = P2k16LoggingFilter._data.get("path", None)

            if method and path:
                record.p2k16HttpReq = " [{} {}]".format(method, path)

        return True

    @classmethod
    def set(cls, **kwargs):
        cls._data = kwargs

    @classmethod
    def clear(cls):
        cls._data.clear()
