from p2k16 import database
from p2k16.models import *


def create():
    from p2k16_web import app
    app.logger.info("No users found in database.")
    session = database.db.session
    supr = User('super', 'super@example.org', 'Super', 'User', '01234567', 'super')
    session.add(supr)
    session.add(User('foo', 'foo@example.org', 'Foo', 'Bar', '76543210', 'foo'))

    session.flush()
    # super = User.find_user_by_username('super')

    admins = Group('admins', 'Admins')
    door = Group('door', 'Users with access to the door')
    session.add_all([admins, door])
    session.flush()
    session.add(GroupMember(admins, supr, supr))
    session.add(GroupMember(door, supr, supr))

    # Add stripe payments
    payment = MembershipPayment(supr, 'tok_sjdkjdfsk', '2017-01-01', '2017-01-01', '500.00', '2017-01-12')
    session.add(payment)

    session.commit()
    app.logger.info("Default data created")
