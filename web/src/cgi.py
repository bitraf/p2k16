
from email.message import Message

def parse_header(header):
    msg = Message()
    msg.add_header('content-type', header)
    r = msg.get_param('charset')
    if r:
        return r
