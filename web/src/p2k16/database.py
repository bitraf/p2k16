import p2k16
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(p2k16.app)

from sqlalchemy_continuum.plugins import FlaskPlugin
from sqlalchemy_continuum import make_versioned

make_versioned(plugins=[FlaskPlugin()], user_cls=None)

# Explicitly import all the models here so we know configure_mappers() are called afterwards
from p2k16.models import *

db.configure_mappers()
