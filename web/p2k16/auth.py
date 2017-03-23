import flask_login

from p2k16.models import User, find_user_by_id

login_manager = flask_login.LoginManager()


class AuthenticatedUser(flask_login.UserMixin):
    def __init__(self, user):
        self.id = user.id
        self.user = user


@login_manager.user_loader
def user_loader(user_id):
    print("Loading user id=" + user_id)
    user = find_user_by_id(user_id)

    if user is None:
        return

    return AuthenticatedUser(user)


@login_manager.request_loader
def request_loader(request):
    user_id = request.form.get("user_id")

    if user_id is None:
        return

    return user_loader(user_id)
