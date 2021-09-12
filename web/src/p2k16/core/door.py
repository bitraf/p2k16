import logging
from datetime import datetime
from typing import Optional, Mapping, List

import paho.mqtt.client as mqtt
import requests

from p2k16.core import P2k16UserException, membership_management
from p2k16.core import account_management, event_management, badge_management, authz_management
from p2k16.core.models import db, Account, Circle, Event, Company

logger = logging.getLogger(__name__)


# Generic door  ##############################################################

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
        if "MQTT_HOST" in cfg:
            self.mqtt = MqttClient(cfg)
        else:
            logger.info("No MQTT host configured for door, not starting door MQTT client")

        if "DLOCK_BASE_URL" in cfg:
            self.dlock = DlockClient(cfg)
        else:
            logger.info("No dlock base URL configured for door, not starting door dlock client")

    def open_doors(self, account: Account, doors):
        can_open_door = authz_management.can_haz_door_access(account, doors)
        if not can_open_door:
            f = "{} does not have an active membership, or lacks door circle membership"
            raise P2k16UserException(f.format(account.display_name()))

        if not event_management.has_opened_door(account):
            system = Account.find_account_by_username("system")
            logger.info("First door opening for {}".format(account))
            badge_management.create_badge(account, system, "first-door-opening")

        for door in doors:
            lf = "Opening door. username={}, door={}, open_time={}"
            logger.info(lf.format(account.username, door.key, door.open_time))

            event_management.save_event(OpenDoorEvent(door.key))

        # Make sure everything has been written to the database before actually opening the door.
        db.session.flush()

        # TODO: move this to a handler that runs after the transaction is done
        # TODO: we can look at the responses and see if they where successfully sent/received.
        for door in doors:
            if isinstance(door, DlockDoor):
                self.dlock.open(door)
            elif isinstance(door, MqttDoor):
                self.mqtt.open(door)
            else:
                P2k16TechnicalException("Unknown kind of door")

def create_client(cfg: Mapping[str, str]) -> DoorClient:
    return DoorClient(cfg)

# dlock  #####################################################################

class DlockDoor(object):
    def __init__(self, key, open_time, circles, name):
        self.key = key
        self.open_time = open_time
        self.circles = circles
        if name is None:
            self.name = "Door: {}".format(key)
        else:
            self.name = name

class DlockClient(object):
    def __init__(self, cfg: Mapping[str, str]):
        self.base_url = cfg["DLOCK_BASE_URL"]
        self.username = cfg["DLOCK_USERNAME"]
        self.password = cfg["DLOCK_PASSWORD"]

        logger.info("dlock config: base_url={}, username={}".format(self.base_url, self.username))

    def open(self, door):
        logger.info("Sending dlock request: {}: {}".format(door.key, door.open_time))

        url = "{}/doors/{}/unlock".format(self.base_url, door.key)
        auth = (self.username, self.password)
        params = {"duration": str(door.open_time)}

        r = requests.post(url, auth=auth, params=params)
        try:
            r.raise_for_status()
        except e:
            logger.error("http error: {}".format(e))
            P2k16TechnicalException("Could not unlock door through dlock")

# MQTT  ######################################################################

class MqttDoor(object):
    def __init__(self, key, open_time, circles, topic, name):
        self.key = key
        self.open_time = open_time
        self.circles = circles
        self.topic = topic
        if name is None:
            self.name = "Door: {}".format(key)
        else:
            self.name = name

class MqttClient(object):
    def __init__(self, cfg: Mapping[str, str]):
        host = cfg["MQTT_HOST"]
        port = cfg["MQTT_PORT"]
        username = cfg["MQTT_USERNAME"]
        password = cfg["MQTT_PASSWORD"]
        self.prefix = cfg["MQTT_PREFIX"]

        logger.info("MQTT client connecting to {}:{}".format(host, port))
        logger.info("MQTT config: username={}, prefix={}".format(username, self.prefix))

        keep_alive = 60
        c = mqtt.Client()
        if username:
            c.username_pw_set(username=username, password=password)
        c.connect_async(host, port, keep_alive)
        c.enable_logger()
        c.loop_start()

        self._client = c

    def open(self, door):
        topic = self.prefix + door.topic
        open_time = str(door.open_time)

        logger.info("Sending MQTT message: {}: {}".format(topic, open_time))
        self._client.publish(topic, open_time)

# Site-specific configuration  ###############################################

_doors = [
    DlockDoor(  "bv9-f2-entrance",  name="Entrance",
              open_time=10, circles={"door"}),
]

doors = {d.key: d for d in _doors}
