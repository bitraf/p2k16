import flask_bower

import p2k16.database
import p2k16_web.views

app = p2k16.app

app.register_blueprint(p2k16_web.views.api)

flask_bower.Bower(app)
