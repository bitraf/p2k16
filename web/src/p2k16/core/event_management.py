import logging
from datetime import datetime
from typing import Collection, MutableMapping, Tuple

from p2k16.core import P2k16TechnicalException
from p2k16.core.models import db, Account, Event
from sqlalchemy import or_

logger = logging.getLogger(__name__)

_from_key = {}  # type: MutableMapping[Tuple[str, str], Converter]
_from_type = {}  # type: MutableMapping[type, Converter]


class Converter(object):
    def __init__(self, domain: str, name: str, instance):
        self.domain = domain
        self.name = name
        self.instance = instance


def converter_for(domain: str, name: str):
    def decorator(Cls):
        c = Converter(domain, name, Cls)
        _from_key[(domain, name)] = c
        _from_type[Cls] = c
        return Cls

    return decorator


def save_event(event):
    logger.info("type(event)={}".format(type(event)))
    converter = _from_type[type(event)]

    if not converter:
        raise P2k16TechnicalException("Could not find converter for {}".format(type(event)))

    db.session.add(event.to_event())


def _convert(events: Collection[Event]):
    records = []
    for e in events:
        converter = _from_key[(e.domain, e.name)]

        if not converter:
            continue

        r = converter.instance.from_event(e)
        if r:
            records.append(r)

    return records


def get_public_recent_events(start: datetime):
    events = Event.query. \
        filter(or_((Event.domain == "door") & (Event.name == "open"),
                   Event.domain == "badge")). \
        filter(Event.created_at > start). \
        order_by(Event.created_at.desc()).limit(100). \
        all()  # type: Collection[Event]

    return _convert(events)
