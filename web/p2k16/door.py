import paho.mqtt.client as mqtt
from p2k16 import P2k16UserException, app
from p2k16 import user_management
from p2k16.models import db, User, Group, AuditRecord

_client = mqtt.Client()

_host = 'mqtt.bitraf.no'
_port = 1883
_keep_alive = 60


class Door(object):
    def __init__(self, key):
        self.key = key


FRONT_DOOR = Door('front')


def init():
    app.logger.info('Connecting to {}:{}'.format(_host, _port))
    _client.username_pw_set(username=app.config['MQTT_USERNAME'], password=app.config['MQTT_PASSWORD'])
    _client.connect(_host, _port, _keep_alive)
    _client.loop_start()


def open_door(user: User, door):
    door_group = Group.get_by_name('door')

    if not user_management.is_user_in_group(door_group, user):
        raise P2k16UserException('{} is not in the door group'.format(user.display_name()))

    app.logger.info('Opening door. key={}, user={}'.format(door.key, user.username))

    db.session.add(AuditRecord(user.id, 'door/{}'.format(door.key), 'open'))
    # Make sure everything has been written to the database before actually opening the door.
    db.session.flush()

    _client.publish('/bitraf/door/frontdoor/open', '10')
    _client.publish('/bitraf/door/2floor/open', '60')
    _client.publish('/bitraf/door/4floor/open', '60')
