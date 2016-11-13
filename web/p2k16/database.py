from flask_sqlalchemy import SQLAlchemy

import p2k16

db = SQLAlchemy(p2k16.app)

Base = db.Model

# def create_engine(connection_string):
#     engine = sqlalchemy.create_engine(connection_string, convert_unicode=True)
#
#     # noinspection PyUnresolvedReferences
#     import p2k16.models
#     Base.metadata.create_all(bind=engine)
#
#     return engine
#
#
# def configure_scoped_session(engine):
#     from sqlalchemy.orm import scoped_session, sessionmaker
#     db_session = scoped_session(sessionmaker(autocommit=False,
#                                              autoflush=False,
#                                              bind=engine))
#     Base.query = db_session.query_property()
