import logging
from datetime import datetime
from typing import Optional, Mapping, List

import paho.mqtt.client as mqtt
from p2k16.core import P2k16UserException, membership_management
from p2k16.core import account_management, event_management, badge_management
from p2k16.core.models import db, Account, Circle, Event, Company

logger = logging.getLogger(__name__)


class Door(object):
    def __init__(self, key, topic, open_time):
        self.key = key
        self.topic = topic
        self.open_time = open_time


class DummyClient(object):
    pass


@event_management.converter_for("door", "open")
class OpenDoorEvent(object):
    def __init__(self, door, created_at: Optional[datetime] = None, created_by: Optional[Account] = None):
        self.door = door
        self.created_at = created_at
        self.created_by = created_by

    def to_event(self):
        return {"text1": self.door}

    @staticmethod
    def from_event(event: Event) -> "OpenDoorEvent":
        return OpenDoorEvent(event.text1, event.created_at, event.created_by)

    def to_dict(self):
        return {**event_management.base_dict(self), **{
            "created_at": self.created_at,
            "created_by": self.created_by,
            "created_by_username": self.created_by.username,
            "door": self.door
        }}


class DoorClient(object):
    def __init__(self, cfg: Mapping[str, str]):

        host = cfg["MQTT_HOST"]
        port = cfg["MQTT_PORT"]
        username = cfg["MQTT_USERNAME"]
        password = cfg["MQTT_PASSWORD"]
        self.prefix = cfg["MQTT_PREFIX"]

        logger.info("Connecting to {}:{}".format(host, port))
        logger.info("config: username={}, prefix={}".format(username, self.prefix))

        keep_alive = 60
        c = mqtt.Client()
        if username:
            c.username_pw_set(username=username, password=password)
        c.connect_async(host, port, keep_alive)
        c.enable_logger()
        c.loop_start()

        self._client = c

    def open_doors(self, account: Account, doors: List[Door]):
        door_circle = Circle.get_by_name('door')

        if not account_management.is_account_in_circle(account, door_circle):
            raise P2k16UserException('{} is not in the door circle'.format(account.display_name()))

        if not membership_management.active_member(account) and len(
            Company.find_active_companies_with_account(account.id)) == 0:
            raise P2k16UserException('{} does not have an active membership and is not employed in an active company'.
                                     format(account.display_name()))

        publishes = []

        if not event_management.has_opened_door(account):
            system = Account.find_account_by_username("system")
            logger.info("First door opening for {}".format(account))
            badge_management.create_badge(account, system, "first-door-opening")

        for door in doors:
            logger.info('Opening door. username={}, door={}, open_time={}'.format(
                account.username, door.key, door.open_time))
            event_management.save_event(OpenDoorEvent(door.key))
            publishes.append((self.prefix + door.topic, str(door.open_time)))

        # Make sure everything has been written to the database before actually opening the door.
        db.session.flush()

        # TODO: move this to a handler that runs after the transaction is done
        # TODO: we can look at the responses and see if they where successfully sent/received.
        for topic, open_time in publishes:
            logger.info("Sending message: {}: {}".format(topic, open_time))
            self._client.publish(topic, open_time)


def create_client(cfg: Mapping[str, str]) -> DoorClient:
    if "MQTT_HOST" not in cfg:
        logger.info("No MQTT host configured for door, not starting door mqtt client")
        return DummyClient()

    return DoorClient(cfg)


_doors = [
    Door("frontdoor", "frontdoor/open", 10),
    Door("2floor", "2floor/open", 60),
    Door("3office", "3office/open", 60),
    Door("3workshop", "3workshop/open", 60),
    Door("4floor", "4floor/open", 60),
]

doors = {d.key: d for d in _doors}
