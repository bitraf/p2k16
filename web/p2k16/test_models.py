from flask_testing import TestCase

import p2k16.database
from p2k16.models import *


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

if __name__ == '__main__':
    import unittest
    unittest.main()
