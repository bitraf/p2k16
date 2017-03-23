import p2k16.database
import p2k16_web
from p2k16.models import *

# engine = p2k16.database.create_engine('postgresql://p2k16-web:p2k16-web@localhost/p2k16')

app = p2k16_web.app

print("Creating database")
p2k16.database.db.create_all(app=p2k16.app)
print("Database created")

from p2k16.auth import login_manager

login_manager.init_app(app)

if len(User.query.all()) == 0:
    session = p2k16.database.db.session

    session.add(Group('admin', 'Admins'))
    session.add(User('super', 'super@example.org', 'super'))
    session.add(User('foo', 'foo@example.org', 'foo'))
    spr = User.find_user_by_username('super')
    session.add(GroupMember(Group.find_by_name('Admins'), spr, spr))
    session.commit()
