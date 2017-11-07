from itertools import chain
from sqlalchemy import event

import p2k16.core
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(p2k16.core.app)

from sqlalchemy_continuum.plugins import FlaskPlugin
from sqlalchemy_continuum import make_versioned

make_versioned(plugins=[FlaskPlugin()], user_cls=None)

# Explicitly import all the models here so we know configure_mappers() are called afterwards
from p2k16.core.models import *


@event.listens_for(db.session, 'before_flush')
def receive_before_flush(session, flush_context, instances):
    print("before flush!")
    print("flush_context: {}".format(flush_context))
    print("instances: {}".format(len(instances) if instances else "none!!"))

    for obj in chain(session.new, session.dirty):
        if session.is_modified(obj):
            model_support.before_flush(obj)


db.configure_mappers()
