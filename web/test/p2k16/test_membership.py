import logging

from flask_testing import TestCase
from p2k16.core import make_app, account_management, membership_management, P2k16UserException
from p2k16.core.membership_management import get_membership
from p2k16.core.models import *

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class AccountTest(TestCase):
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True

    def create_app(self):
        app = make_app()
        db.init_app(app)
        return app

    def setUp(self):
        db.create_all()

    def test_membership(self):
        session = db.session
        a3 = Account('account3', 'account3@example.org', password='123')
        a4 = Account('account4', 'account4@example.org', password='123')
        a5 = Account('account5', 'account5@example.org', password='123')
        session.add_all([a3, a4, a5])
        session.flush()

        with model_support.run_as(a3):
            # Add account3 with active membership
            m3 = Membership(500)

            payment1 = MembershipPayment('tok_stripe_xx1234', datetime(2017, 1, 1), datetime(2017, 1, 31), '500.00',
                                         datetime(2017, 1, 1))
            payment2 = MembershipPayment('tok_stripe_xx1337', datetime(2017, 2, 1), datetime(2017, 2, 28), '500.00',
                                         datetime(2017, 2, 1))
            payment3 = MembershipPayment('tok_stripe_xx1338', datetime(2017, 3, 1),
                                         datetime.now() + timedelta(days=1), '500.00', datetime(2017, 2, 1))
            session.add_all([m3, payment1, payment2, payment3])

        with model_support.run_as(a4):
            # Account 4 with expired membership
            payment4 = MembershipPayment('tok_stripe_xx3234', datetime(2017, 1, 1), datetime(2017, 1, 31), '500.00',
                                         datetime(2017, 1, 1))
            session.add_all([payment4])

        # Account 5 has no payments
        session.flush()

        # Verify only one paid account
        assert len(membership_management.paid_members()) == 1

        # Check membership payments
        assert membership_management.active_member(a3) is True
        assert membership_management.active_member(a4) is False
        assert membership_management.active_member(a5) is False

        # Check membership
        membership = get_membership(a3)
        assert membership.fee is 500

        membership = get_membership(a5)
        assert membership is None


if __name__ == '__main__':
    import unittest

    unittest.main()
