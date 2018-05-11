import logging
from datetime import datetime
from typing import List, MutableMapping, Tuple

from p2k16.core import P2k16TechnicalException
from p2k16.core.models import db, Account, Event
from sqlalchemy import or_, func, distinct

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

    params = event.to_event()
    db.session.add(Event(converter.domain, converter.name, **params))


def _convert(e: Event):
    converter = _from_key.get((e.domain, e.name), None)

    return converter.instance.from_event(e) if converter else None


def _convert_all(events: List[Event]):
    records = []
    for e in events:
        r = _convert(e)
        if r:
            records.append(r)

    return records


def base_dict(event):
    converter = _from_type[type(event)]
    return {"domain": converter.domain, "name": converter.name}


def get_public_recent_events(start: datetime):
    events = Event.query. \
        filter(or_((Event.domain == "door") & (Event.name == "open"),
                   Event.domain == "badge")). \
        filter(Event.created_at > start). \
        order_by(Event.created_at.desc()).limit(100). \
        all()  # type: List[Event]

    return _convert_all(events)


def get_door_open_events_by_day(start: datetime):
    return db.session.query(func.date(Event.created_at), func.count(distinct(Event.created_by_id))). \
        filter((Event.domain == "door") & (Event.name == "open")). \
        filter(Event.created_at > start). \
        group_by(func.date(Event.created_at)). \
        order_by(func.date(Event.created_at)). \
        all()


def has_opened_door(account: Account):
    import sqlalchemy
    q = sqlalchemy.exists().where((Event.created_by == account) & (Event.domain == "door") & (Event.name == "open"))
    return db.session.query(q).scalar()


def last_door_open(account: Account):
    e = Event.query. \
        filter(Event.created_by == account). \
        filter((Event.domain == "door") & (Event.name == "open")). \
        order_by(Event.created_at). \
        limit(1). \
        one_or_none()

    return _convert(e) if e else None
