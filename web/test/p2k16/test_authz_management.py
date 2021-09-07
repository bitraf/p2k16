import logging
from unittest import TestCase

from p2k16.core import make_app, account_management, P2k16UserException, authz_management, door
from p2k16.core.models import *

logger = logging.getLogger(__name__)


class P2k16TestCase(TestCase):

    def setUp(self):
        logger.info("setUp")
        self.app = make_app()


        door.doors["test-door-1"] = door.MqttDoor("test-door-1", 1, {"door"}, "test-door-1/open")
        door.doors["test-door-2"] = door.MqttDoor("test-door-2", 1, {"bv9-chemist"}, "test-door-2/open")
        door.doors["test-door-3"] = door.MqttDoor("test-door-3", 1, {"other-circle"}, "test-door-3/open")

        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"

        self._ctx = self.app.test_request_context()
        self._ctx.push()

        db.init_app(self.app)
        db.create_all()

        logger.info("setUp done")

    def tearDown(self):
        self._ctx.pop()
        logger.info("tearDown")


# noinspection PyMethodMayBeStatic
class DoorAccessTest(P2k16TestCase):

    def test_door_access(self):
        session = db.session

        a1 = Account('door-account1', 'door-account1@example.org', password='123')
        a2 = Account('door-account2', 'door-account2@example.org', password='123')
        a3 = Account('door-account3', 'door-account3@example.org', password='123')
        session.add_all([a1, a2, a3])
        session.flush()
        with model_support.run_as(a1):

            m1 = Membership(500)
            payment1 = StripePayment('tok_stripe_xx1339', datetime(2017, 3, 1),
                                     datetime.now() + timedelta(days=10), '500.00', datetime(2017, 2, 1))
            session.add_all([m1, payment1])

        with model_support.run_as(a2):
            m2 = Membership(500)
            payment2 = StripePayment('tok_stripe_xx1348', datetime(2017, 3, 1),
                                     datetime.now() + timedelta(days=10), '500.00', datetime(2017, 2, 1))
            session.add_all([m2, payment2])

        c_door = Circle('door', 'Door access', False, CircleManagementStyle.SELF_ADMIN)
        c_chemistry = Circle('bv9-chemist', 'BV9: Chemist', False, CircleManagementStyle.SELF_ADMIN)

        with session.begin(subtransactions=True):
            with model_support.run_as(a1):
                c_door.add_member(a1, "")
                c_chemistry.add_member(a1, "")
                c_door.add_member(a2, "")
                session.add_all([c_door, c_chemistry])
                session.flush()
                logger.info("Setup done")

        with session.begin(subtransactions=True):
            # a1 is paying member
            assert StripePayment.is_account_paying_member(a1.id) is True
            assert authz_management.can_haz_door_access(a1, [door.doors["test-door-1"]]) is True
            assert authz_management.can_haz_door_access(a1, [door.doors["test-door-2"]]) is True
            assert authz_management.can_haz_door_access(a1, [door.doors["test-door-3"]]) is False
            assert authz_management.can_haz_door_access(a1, [
                door.doors["test-door-2"],
                door.doors["test-door-1"],
            ]) is True
            assert authz_management.can_haz_door_access(a1, [
                door.doors["test-door-3"],
                door.doors["test-door-1"],
            ]) is False

            # a2 is paying member, but not member of bv9-chemist circle
            assert authz_management.can_haz_door_access(a2, [door.doors["test-door-1"]]) is True
            assert authz_management.can_haz_door_access(a2, [door.doors["test-door-2"]]) is False
            assert authz_management.can_haz_door_access(a2, [door.doors["test-door-3"]]) is False

            # a3 is not a paying member
            assert authz_management.can_haz_door_access(a3, [door.doors["test-door-1"]]) is False
            assert authz_management.can_haz_door_access(a3, [door.doors["test-door-2"]]) is False
            assert authz_management.can_haz_door_access(a3, [door.doors["test-door-3"]]) is False

