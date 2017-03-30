import p2k16.database
import p2k16_web
from p2k16.models import *
from p2k16 import default_data

# engine = p2k16.database.create_engine('postgresql://p2k16-web:p2k16-web@localhost/p2k16')

app = p2k16_web.app

print("Creating database")
p2k16.database.db.create_all(app=p2k16.app)
print("Database created")

from p2k16.auth import login_manager

login_manager.init_app(app)

if len(User.query.all()) == 0:
    app.logger.info("No users found in database.")

    default_data.create_default_groups()
    default_data.create_default_users()

    #
    # session = p2k16.database.db.session
    #
    # session.add(Group('admin', 'Admins'))
    # session.add(User('super', 'super@example.org', 'Super', 'User', '01234567',  'super'))
    # session.add(User('foo', 'foo@example.org', 'Foo', 'Bar', '76543210', 'foo'))
    # spr = User.find_user_by_username('super')
    #
    # session.add(GroupMember(Group.find_by_name('admins'), spr, spr))
    # session.commit()
    #app.logger.info("Default users created.")
