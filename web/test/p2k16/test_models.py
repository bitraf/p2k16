from datetime import datetime
from datetime import timedelta

import p2k16.database
from flask_testing import TestCase
from p2k16 import account_management, membership_management, P2k16UserException
from p2k16.models import *


# noinspection PyMethodMayBeStatic
class AccountTest(TestCase):
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True

    # engine = p2k16.database.create_engine("sqlite:///:memory:")
    # Session = sessionmaker(bind=engine)

    # def create_app(self):
    #     app = Flask(__name__)
    #     app.config['TESTING'] = True
    #     return app

    def create_app(self):
        return p2k16.app

    def setUp(self):
        # Base.metadata.create_all(self.engine)
        # self.session = self.Session()
        # self.session.add(Panel(1, 'ion torrent', 'start'))
        # self.session.commit()
        p2k16.database.db.create_all()
        pass

    def tearDown(self):
        # Base.metadata.drop_all(self.engine)
        pass

    def test_basic(self):
        accounts = Account.query.all()
        print("accounts: " + str(accounts))

    def test_authentication_test(self):
        session = p2k16.database.db.session
        account = Account('foo', 'foo@example.org', password='123')
        session.add(account)
        session.flush()

        membership = Membership(account, 500)
        session.add(membership)
        session.flush()
        session.commit()

    def test_circles(self):
        session = p2k16.database.db.session
        admin = Account('admin1', 'admin1@example.org', password='123')
        a1 = Account('account1', 'account1@example.org', password='123')
        a2 = Account('account2', 'account2@example.org', password='123')
        c = Circle('circle-1', 'Circle 1')
        c_admin = Circle('circle-1-admin', 'Circle 1 Admins')
        session.add_all([admin, a1, a2, c, c_admin])
        session.flush()
        session.add(CircleMember(c_admin, admin, admin))
        session.flush()

        # non-admin account trying to add
        try:
            account_management.add_account_to_circle(a1.id, c.id, a2.id)
            session.flush()
            self.fail("expected exception")
        except P2k16UserException as e:
            pass

        account_management.add_account_to_circle(a1.id, c.id, admin.id)
        session.commit()
        session.refresh(c)
        print('c.members=%s' % c.members)
        assert len(c.members) > 0

    def test_membership(self):
        session = p2k16.database.db.session
        a3 = Account('account3', 'account3@example.org', password='123')
        a4 = Account('account4', 'account4@example.org', password='123')
        a5 = Account('account5', 'account5@example.org', password='123')
        session.add_all([a3, a4, a5])
        session.flush()

        # Add account3 with active membership
        payment1 = MembershipPayment(a3, 'tok_stripe_xx1234', datetime(2017, 1, 1), datetime(2017, 1, 31), '500.00',
                                     datetime(2017, 1, 1))
        payment2 = MembershipPayment(a3, 'tok_stripe_xx1337', datetime(2017, 2, 1), datetime(2017, 2, 28), '500.00',
                                     datetime(2017, 2, 1))
        payment3 = MembershipPayment(a3, 'tok_stripe_xx1338', datetime(2017, 3, 1),
                                     datetime.utcnow() + timedelta(days=1), '500.00', datetime(2017, 2, 1))

        # Account 4 with expired membership
        payment4 = MembershipPayment(a4, 'tok_stripe_xx3234', datetime(2017, 1, 1), datetime(2017, 1, 31), '500.00',
                                     datetime(2017, 1, 1))

        # Account 5 has no payments

        session.add_all([payment1, payment2, payment3, payment4])
        session.flush()

        # Verify only one paid account
        assert len(membership_management.paid_members()) == 1

        assert membership_management.active_member(a3) is True
        assert membership_management.active_member(a4) is False
        assert membership_management.active_member(a5) is False


if __name__ == '__main__':
    import unittest

    unittest.main()
