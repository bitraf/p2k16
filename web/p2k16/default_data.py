from p2k16 import database
from p2k16.models import *


def create_default_users():
    session = database.db.session
    session.add(User('super', 'super@example.org', 'Super', 'User', '01234567',  'super'))
    session.add(User('foo', 'foo@example.org', 'Foo', 'Bar', '76543210', 'foo'))
    spr = User.find_user_by_username('super')

    session.add(GroupMember(Group.find_by_name('admins'), spr, spr))
    session.commit()

def create_default_groups():
    session = database.db.session
    session.add(Group('admins', 'Admins'))
    session.commit()
