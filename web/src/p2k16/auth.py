import flask_login
from p2k16 import user_management
from p2k16.models import User

login_manager = flask_login.LoginManager()


class AuthenticatedUser(flask_login.UserMixin):
    def __init__(self, user, groups):
        self.id = user.id
        self.user = user
        self.groups = groups


@login_manager.user_loader
def user_loader(user_id):
    user = User.find_user_by_id(user_id)

    if user is None:
        return

    groups = user_management.groups_by_user(user.id)

    return AuthenticatedUser(user, groups)


@login_manager.request_loader
def request_loader(request):
    user_id = request.form.get("user_id")

    if user_id is None:
        return

    return user_loader(user_id)
