from flask_testing import TestCase
from p2k16.core import app, account_management, membership_management, P2k16UserException
from p2k16.core.membership_management import get_membership
from p2k16.core.models import *


# noinspection PyMethodMayBeStatic
from sqlalchemy.orm.exc import NoResultFound


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
        return app

    def setUp(self):
        # Base.metadata.create_all(self.engine)
        # self.session = self.Session()
        # self.session.add(Panel(1, 'ion torrent', 'start'))
        # self.session.commit()
        db.create_all()
        pass

    def tearDown(self):
        # Base.metadata.drop_all(self.engine)
        pass

    def test_basic(self):
        accounts = Account.query.all()
        print("accounts: " + str(accounts))

    def test_authentication_test(self):
        session = db.session
        account = Account('foo', 'foo@example.org', password='123')
        session.add(account)
        session.flush()

        with model_support.run_as(account):
            membership = Membership(500)
            session.add(membership)
            session.flush()
            session.commit()

    def test_circles(self):
        session = db.session
        admin = Account('admin1', 'admin1@example.org', password='123')
        a1 = Account('account1', 'account1@example.org', password='123')
        a2 = Account('account2', 'account2@example.org', password='123')
        c = Circle('circle-1', 'Circle 1')

        with model_support.run_as(admin):
            c_admin = Circle('circle-1-admin', 'Circle 1 Admins')
            session.add_all([admin, a1, a2, c, c_admin])
            session.flush()

        with model_support.run_as(admin):
            session.add(CircleMember(c_admin, admin))
            session.flush()

        # non-admin account trying to add
        try:
            account_management.add_account_to_circle(a1.id, c.id, a2.id)
            session.flush()
            self.fail("expected exception")
        except P2k16UserException:
            pass

        with model_support.run_as(admin):
            account_management.add_account_to_circle(a1.id, c.id, admin.id)

        session.commit()
        session.refresh(c)
        print('c.members=%s' % c.members)
        assert len(c.members) > 0

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
