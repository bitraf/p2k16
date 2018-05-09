import logging
from datetime import datetime
from typing import Optional, Mapping, List

import paho.mqtt.client as mqtt
from p2k16.core import P2k16UserException, membership_management
from p2k16.core import account_management, event_management, badge_management
from p2k16.core.models import db, Account, Circle, Event, Company

logger = logging.getLogger(__name__)


class DummyClient(object):
    pass


class ToolClient(object):
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

    # TODO: check permissions
    def checkout_tool(self, account: Account, tool: str):
        #door_circle = Circle.get_by_name('door')

        """
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
        """


        logger.info('Checking out tool. username={}, tool={}'.format(account.username, tool))

#            event_management.save_event(OpenDoorEvent(door.key))
#            publishes.append((self.prefix + door.topic, str(door.open_time)))

        # Make sure everything has been written to the database before actually opening the door.
        db.session.flush()

        # TODO: move this to a handler that runs after the transaction is done
        # TODO: we can look at the responses and see if they where successfully sent/received.
#        for topic, open_time in publishes:
#            logger.info("Sending message: {}: {}".format(topic, open_time))
#            self._client.publish(topic, open_time)

        topic = "{}/{}".format('/public/machine/pick_and_place', 'unlock')
        payload = 'true'
        logger.info("Sending message: {}: {}".format(topic, payload))
        self._client.publish(topic, payload)

    def checkin_tool(self, account: Account, tool: str):
        logger.info('Checking in tool. username={}, tool={}'.format(account.username, tool))


        topic = "{}/{}".format('/public/machine/pick_and_place', 'lock')
        payload = 'true'
        logger.info("Sending message: {}: {}".format(topic, payload))
        self._client.publish(topic, payload)


def create_client(cfg: Mapping[str, str]) -> ToolClient:
    if "MQTT_HOST" not in cfg:
        logger.info("No MQTT host configured for door, not starting door mqtt client")
        return DummyClient()

    return ToolClient(cfg)


