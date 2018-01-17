import typing

import paho.mqtt.client as mqtt
from p2k16.core import P2k16UserException, app
from p2k16.core import account_management
from p2k16.core.models import db, Account, Circle, AuditRecord

_client = None


class Door(object):
    def __init__(self, key, topic, open_time):
        self.key = key
        self.topic = topic
        self.open_time = open_time


doors = {
    "frontdoor": Door("front", "/bitraf/door/frontdoor/open", 10),
    "2rd-floor": Door("2nd-floor", "/bitraf/door/2floor/open", 60),
    "3rd-floor": Door("3rd-floor", "/bitraf/door/3floor/open", 60),
    "4th-floor": Door("4th-floor", "/bitraf/door/4floor/open", 60),
}


def init(cfg: typing.Mapping[str, str]):
    if not "MQTT_HOST" in cfg:
        app.logger.info("No MQTT host configured for door, not starting door mqtt client")
        return

    host = cfg["MQTT_HOST"]
    port = cfg["MQTT_PORT"]
    keep_alive = 60
    username = cfg["MQTT_USERNAME"]
    password = cfg["MQTT_PASSWORD"]

    app.logger.info("Connecting to {}:{}".format(host, port))
    app.logger.info("config: u={}, p={}".format(username, password))
    app.logger.info("config: u={}, p={}".format(type(username), type(password)))

    _client = mqtt.Client()
    _client.username_pw_set(username=username, password=password)
    _client.connect_async(host, port, keep_alive)
    _client.loop_start()


def open_doors(account: Account, doors: typing.List[Door]):
    door_circle = Circle.get_by_name('door')

    if not account_management.is_account_in_circle(account, door_circle):
        raise P2k16UserException('{} is not in the door circle'.format(account.display_name()))

    publishes = []

    for door in doors:
        app.logger.info('Opening door. username={}, door={}, open_time={}'.format(
            account.username, door.key, door.open_time))
        db.session.add(AuditRecord('door/{}'.format(door.key), 'open'))
        publishes.append((door.topic, door.open_time))

    # Make sure everything has been written to the database before actually opening the door.
    db.session.flush()

    if _client:
        # TODO: move this to a handler that runs after the transaction is done
        for topic, open_time in publishes:
            _client.publish(topic, open_time)
