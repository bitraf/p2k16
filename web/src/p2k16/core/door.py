import logging
import typing

import paho.mqtt.client as mqtt

from p2k16.core import P2k16UserException
from p2k16.core import account_management
from p2k16.core.models import db, Account, Circle, AuditRecord

logger = logging.getLogger(__name__)


class Door(object):
    def __init__(self, key, topic, open_time):
        self.key = key
        self.topic = topic
        self.open_time = open_time


class DummyClient(object):
    pass


class DoorClient(object):
    def __init__(self, cfg: typing.Mapping[str, str]):

        host = cfg["MQTT_HOST"]
        port = cfg["MQTT_PORT"]
        keep_alive = 60
        username = cfg["MQTT_USERNAME"]
        password = cfg["MQTT_PASSWORD"]

        logger.info("Connecting to {}:{}".format(host, port))
        logger.info("config: u={}, p={}".format(username, password))
        logger.info("config: u={}, p={}".format(type(username), type(password)))

        c = mqtt.Client()
        c.username_pw_set(username=username, password=password)
        c.connect_async(host, port, keep_alive)
        c.loop_start()

        self._client = c

    def open_doors(self, account: Account, doors: typing.List[Door]):
        door_circle = Circle.get_by_name('door')

        if not account_management.is_account_in_circle(account, door_circle):
            raise P2k16UserException('{} is not in the door circle'.format(account.display_name()))

        publishes = []

        for door in doors:
            logger.info('Opening door. username={}, door={}, open_time={}'.format(
                account.username, door.key, door.open_time))
            db.session.add(AuditRecord('door/{}'.format(door.key), 'open'))
            publishes.append((door.topic, door.open_time))

        # Make sure everything has been written to the database before actually opening the door.
        db.session.flush()

        # TODO: move this to a handler that runs after the transaction is done
        for topic, open_time in publishes:
            self._client.publish(topic, open_time)


def create_client(cfg: typing.Mapping[str, str]) -> DoorClient:
    if "MQTT_HOST" not in cfg:
        logger.info("No MQTT host configured for door, not starting door mqtt client")
        return DummyClient()

    return DoorClient(cfg)


doors = {
    "frontdoor": Door("front", "/bitraf/door/frontdoor/open", 10),
    "2rd-floor": Door("2nd-floor", "/bitraf/door/2floor/open", 60),
    "3rd-floor": Door("3rd-floor", "/bitraf/door/3floor/open", 60),
    "4th-floor": Door("4th-floor", "/bitraf/door/4floor/open", 60),
}
