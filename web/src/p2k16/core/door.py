import paho.mqtt.client as mqtt
from p2k16.core import P2k16UserException, app
from p2k16.core import account_management
from p2k16.core.models import db, Account, Circle, AuditRecord

_client = mqtt.Client()

_host = 'mqtt.bitraf.no'
_port = 1883
_keep_alive = 60


class Door(object):
    def __init__(self, key):
        self.key = key


FRONT_AND_LAB_DOOR = Door('front-and-lab')
THIRD_DOOR = Door('3rd-floor')
FOURTH_FLOOR_DOOR = Door('4th-floor')

doors = {FRONT_AND_LAB_DOOR, THIRD_DOOR, FOURTH_FLOOR_DOOR}


def init():
    app.logger.info('Connecting to {}:{}'.format(_host, _port))
    _client.username_pw_set(username=app.config['MQTT_USERNAME'], password=app.config['MQTT_PASSWORD'])
    _client.connect_async(_host, _port, _keep_alive)
    _client.loop_start()


def open_door(account: Account, door: Door):
    door_circle = Circle.get_by_name('door')

    if not account_management.is_account_in_circle(account, door_circle):
        raise P2k16UserException('{} is not in the door circle'.format(account.display_name()))

    app.logger.info('Opening door. key={}, username={}'.format(door.key, account.username))

    db.session.add(AuditRecord(account.id, 'door/{}'.format(door.key), 'open'))
    # Make sure everything has been written to the database before actually opening the door.
    db.session.flush()

    _client.publish('/bitraf/door/frontdoor/open', '10')
    _client.publish('/bitraf/door/2floor/open', '60')
    _client.publish('/bitraf/door/4floor/open', '60')
