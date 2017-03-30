from flask_testing import TestCase

import p2k16.database
from p2k16.models import *
from p2k16 import user_management, P2k16UserException


class UserTest(TestCase):
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
        # users = self.session.query(User).all()
        users = User.query.all()
        print("users: " + str(users))

    def test_authentication_test(self):
        session = p2k16.database.db.session
        user = User('foo', 'foo@example.org', '123')
        session.add(user)
        session.flush()

        membership = Membership(user, 500)
        session.add(membership)
        session.flush()
        session.commit()

    def test_groups(self):
        session = p2k16.database.db.session
        admin = User('admin1', 'admin1@example.org', '123')
        u1 = User('user1', 'user1@example.org', '123')
        u2 = User('user2', 'user2@example.org', '123')
        g = Group('group-1', 'Group 1')
        g_admin = Group('group-1-admin', 'Group 1 Admins')
        session.add_all([admin, u1, u2, g, g_admin])
        session.flush()
        session.add(GroupMember(g_admin, admin, admin))
        session.flush()

        # non-admin user trying to add
        try:
            user_management.add_user_to_group(u1.id, g.id, u2.id)
            session.flush()
            self.fail("expected exception")
        except P2k16UserException as e:
            pass

        user_management.add_user_to_group(u1.id, g.id, admin.id)
        session.commit()
        session.refresh(g)
        print('g.members=%s' % g.members)
        assert len(g.members) > 0

if __name__ == '__main__':
    import unittest

    unittest.main()
