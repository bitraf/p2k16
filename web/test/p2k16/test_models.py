import logging
from unittest import TestCase

from p2k16.core import make_app, account_management, P2k16UserException
from p2k16.core.models import *

logger = logging.getLogger(__name__)


class P2k16TestCase(TestCase):

    def setUp(self):
        logger.info("setUp")
        self.app = make_app()
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
class AccountTest(P2k16TestCase):

    def test_circles(self):
        session = db.session

        admin = Account('admin1', 'admin1@example.org', password='123')
        a1 = Account('account1', 'account1@example.org', password='123')
        a2 = Account('account2', 'account2@example.org', password='123')
        c_admin = Circle('c-admin', 'Circle 1 Admins', CircleManagementStyle.SELF_ADMIN)
        c = Circle('c', 'Circle 1', CircleManagementStyle.ADMIN_CIRCLE)
        c.admin_circle = c_admin

        with session.begin(subtransactions=True):
            with model_support.run_as(admin):
                session.add_all([admin, a1, a2])
                session.flush()
                c_admin.add_member(admin, "")
                session.add_all([c, c_admin])
                session.flush()
                logger.info("Setup done")

        with session.begin(subtransactions=True):
            logger.info("Reloading objects")
            admin = Account.get_by_id(admin.id)
            a1 = Account.get_by_id(a1.id)
            a2 = Account.get_by_id(a2.id)
            c_admin = Circle.get_by_id(c_admin.id)
            c = Circle.get_by_id(c.id)

            logger.info("admin.id={}".format(admin.id))
            logger.info("a1.id={}".format(a1.id))
            logger.info("a2.id={}".format(a2.id))
            logger.info("c_admin={}".format(c_admin))
            logger.info("c={}".format(c))

        logger.info("c.admin_circle.id={}".format(c.admin_circle.id))
        logger.info("c.admin_circle={}".format(c.admin_circle))

        # session.refresh(c)
        assert len(c.members) == 0
        # session.refresh(c_admin)
        assert len(c_admin.members) == 1

        assert c.admin_circle is not None
        assert c.admin_circle.id == c_admin.id

        # a2 trying to add a1 to c. C is managed by an admin circle (c_admin), a2 is not in c_admin.
        with session.begin(subtransactions=True):
            try:
                account_management.add_account_to_circle(a1, c, a2, "")
                session.flush()
                self.fail("expected exception")
            except P2k16UserException as e:
                self.assertEqual(e.msg, "account2 is not in the admin circle (c-admin) for circle c")

        session.refresh(c)
        assert len(c.members) == 0

        # admin trying to add a1 to c. C is managed by an admin circle (c_admin), admin is in c_admin.
        with session.begin(subtransactions=True):
            with model_support.run_as(admin):
                account_management.add_account_to_circle(a1, c, admin, "")

        session.refresh(c)
        assert len(c.members) == 1

        # admin trying to add a1 to c_admin. C is managed by the circle's members, admin is in c_admin.
        with session.begin(subtransactions=True):
            with model_support.run_as(admin):
                account_management.add_account_to_circle(a1, c_admin, admin, "")

        with session.begin(subtransactions=True):
            adminable_circles = account_management.get_circles_with_admin_access(admin.id)
            self.assertSetEqual({c.name for c in adminable_circles}, {"c-admin"})

        session.refresh(c_admin)
        assert len(c_admin.members) == 2


if __name__ == '__main__':
    import unittest

    unittest.main()
