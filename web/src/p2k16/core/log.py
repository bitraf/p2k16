# TODO: Do not put any p2k16.* imports here!
import logging


class P2k16LoggingFilter(logging.Filter):
    data = None

    def filter(self, record):
        # Just to make sure that these are always set.
        record.p2k16ReqId = ""
        record.p2k16ReqUser = ""
        record.p2k16ReqIp = ""

        data = P2k16LoggingFilter.data

        if data:
            pass  # TODO: Implement

        return True
