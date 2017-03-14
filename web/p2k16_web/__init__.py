import flask_bower

import p2k16.database
import p2k16_web.views
import p2k16.config

app = p2k16.app
config.load_config_from_env(app)
app.register_blueprint(p2k16_web.views.api)

flask_bower.Bower(app)
